import argparse
import json
import sys
from pathlib import Path
from urllib.error import URLError

import uvicorn
from qdrant_client.http.exceptions import ResponseHandlingException, UnexpectedResponse

from .adapters import OllamaModels, QdrantIndex, Settings, connect_qdrant
from .api import create_app
from .chat import make_chat
from .corpus import fetch_chunks, load_manifest
from .eval_commands import (
    calibrate_judge,
    compare_variants,
    generate_answers,
    judge_answers,
    model_refusal_report,
    reverify_answers,
    write_label_template,
)
from .models import DependencyTimeout, DependencyUnavailable
from .questions import load_questions, validate_question_sets
from .retrieval import (
    Bm25Searcher,
    HybridSearcher,
    RerankSearcher,
    build_retriever,
    fastembed_scorer,
)
from .retrieval_eval import (
    apply_frozen_gates,
    choose_top_k,
    choose_winner,
    evaluate_searcher,
    markdown_report,
)
from .setup_info import describe_setup
from .snapshot import build_manifest, corpus_report, github_file, github_tree

RERANKERS = ("Xenova/ms-marco-MiniLM-L-6-v2", "BAAI/bge-reranker-base")


def run_pass_comparison(args, settings, chunks, index) -> None:
    """ADR 19 step 4: first-pass gate and strict check replayed on the second-pass answers."""
    from .answer_eval import REFUSED_RETRIEVAL, load_records
    from .eval_commands import _verdict_cache, load_prices, price_for
    from .judge import Verdict
    from .pass_compare import passes_report, replay, summarize

    questions = load_questions(args.questions)
    hybrid = HybridSearcher(Bm25Searcher(chunks), index, depth=settings.candidate_depth)
    rerank = RerankSearcher(
        hybrid,
        fastembed_scorer(settings.reranker_model, settings.reranker_cache),
        depth=settings.rerank_depth,
    )
    scores = {q.id: rerank.search(q.question, settings.top_k).confidence for q in questions}
    prices = load_prices(args.pricing)
    cache = _verdict_cache(args.answers_dir / "verdicts.jsonl")
    files = [f for f in sorted(args.answers_dir.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
    results: dict[str, dict] = {"first pass": {}, "second pass": {}}
    for path in files:
        records = load_records(path)
        spec = records[0].model
        saved = {r.id for r in records if r.outcome == REFUSED_RETRIEVAL}
        again = {q for q, s in scores.items() if s is None or s < settings.rerank_min_score}
        if saved != again:
            raise ValueError(f"{spec}: gate decisions differ from the saved run: {saved ^ again}")
        verdicts = {
            r.id: Verdict.model_validate(cache[(spec, r.id)]["verdict"])
            if cache.get((spec, r.id), {}).get("verdict")
            else None
            for r in records
        }
        price = price_for(spec, prices)
        first = replay(records, scores, args.first_pass_gate, "strict")
        second = replay(records, scores, settings.rerank_min_score, settings.citation_check)
        results["first pass"][spec] = summarize(first, verdicts, price)
        results["second pass"][spec] = summarize(second, verdicts, price)
    setup = [
        f"- Questions: `{args.questions.as_posix()}`; answers: `{args.answers_dir.as_posix()}`, "
        f"one run with the frozen settings (tag `{args.tag}`).",
        f"- First pass: gate {args.first_pass_gate}, `strict` citations. Second pass: gate "
        f"{settings.rerank_min_score}, `{settings.citation_check}` citations. Everything else is "
        "the same, so both rows come from the same model outputs (ADR 19).",
    ]
    report = passes_report(results, setup, args.title)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline=chr(10))
    print(report)


def run_gate_comparison(args, settings, manifest, chunks, index) -> None:
    """ADR 15: evaluate refusal-gate thresholds exactly by replaying saved answers."""
    from .answer_eval import REFUSED_RETRIEVAL, load_records
    from .gate_compare import (
        choose_gate,
        evaluate_gate,
        gate_report,
        merge_outcomes,
        recall_first_threshold,
    )
    from .retrieval_eval import best_gate

    questions = load_questions(args.questions)
    hybrid = HybridSearcher(Bm25Searcher(chunks), index, depth=settings.candidate_depth)
    rerank = RerankSearcher(
        hybrid,
        fastembed_scorer(settings.reranker_model, settings.reranker_cache),
        depth=settings.rerank_depth,
    )
    scores = {q.id: rerank.search(q.question, settings.top_k).confidence for q in questions}

    def runs(directory: Path) -> dict:
        files = [f for f in sorted(directory.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
        return {load_records(f)[0].model: load_records(f) for f in files}

    behind, gate_off = runs(args.baseline_dir), runs(args.nogate_dir)
    # The replay is exact only if today's scores reproduce the gate decisions of the saved run.
    for spec, records in behind.items():
        saved = {r.id for r in records if r.outcome == REFUSED_RETRIEVAL}
        replayed = {q for q, s in scores.items() if s is None or s < settings.rerank_min_score}
        if saved != replayed:
            raise ValueError(
                f"{spec}: gate decisions differ from the saved run: {saved ^ replayed}"
            )
    per_model = {spec: merge_outcomes(r, gate_off.get(spec, [])) for spec, r in behind.items()}
    answerable = {q.id for q in questions if q.answerable}
    refit = best_gate(
        [scores[q] for q in sorted(answerable)],
        [scores[q.id] for q in questions if not q.answerable],
    ).threshold
    variants = {
        "G0 no gate": None,
        "G1 current": settings.rerank_min_score,
        "G2 refit": refit,
        "G3 recall-first": recall_first_threshold(scores, answerable),
    }
    results = {name: evaluate_gate(per_model, scores, t) for name, t in variants.items()}
    chosen = choose_gate(results, len(answerable))
    setup = [
        f"- Questions: `{args.questions.as_posix()}`, {len(questions)} total, "
        f"{len(answerable)} answerable.",
        f"- Answers behind the current gate: `{args.baseline_dir.as_posix()}`; gate-off answers "
        f"for the questions it refused: `{args.nogate_dir.as_posix()}`.",
        f"- Gate score: top `{settings.reranker_model}` score over hybrid candidates; the replayed "
        "current gate reproduces the saved run's refusals exactly.",
    ]
    report = gate_report(results, chosen, setup)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline="\n")
    scores_path = args.report.with_name(args.report.stem + "_scores.json")
    scores_path.write_text(
        json.dumps(scores, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n"
    )
    print(report)


def run_retrieval_eval(args, settings, manifest, chunks, index) -> None:
    questions = load_questions(args.questions)
    lexical = Bm25Searcher(chunks)
    searchers = {}
    for mode in args.modes.split(","):
        if mode == "bm25":
            searchers[mode] = lexical
        elif mode == "dense":
            searchers[mode] = index
        elif mode == "hybrid":
            searchers[mode] = HybridSearcher(lexical, index, depth=settings.candidate_depth)
        elif mode == "hybrid-rerank":
            hybrid = HybridSearcher(lexical, index, depth=settings.candidate_depth)
            for model in filter(None, args.rerankers.split(",")):
                scorer = fastembed_scorer(model, settings.reranker_cache)
                name = f"hybrid-rerank ({model.split('/')[-1]})"
                searchers[name] = RerankSearcher(hybrid, scorer, depth=settings.rerank_depth)
        else:
            raise ValueError(f"Unknown retrieval mode: {mode}")

    results = {name: evaluate_searcher(questions, s, chunks) for name, s in searchers.items()}
    frozen = bool(getattr(args, "final", False))
    if frozen:
        # Held-out: apply the dev choices as /ask does and select nothing on these questions.
        deployed_rerank = f"hybrid-rerank ({settings.reranker_model.split('/')[-1]})"
        winner = (
            deployed_rerank
            if settings.retrieval_mode == "hybrid-rerank"
            else settings.retrieval_mode
        )
        top_k = settings.top_k
        apply_frozen_gates(
            results,
            {
                "bm25": None,
                "dense": settings.min_score,
                "hybrid": settings.min_score,
                deployed_rerank: settings.rerank_min_score,
            },
        )
    else:
        winner = choose_winner(results)
        top_k = choose_top_k(results[winner]["hit@k"], results[winner]["answerable"])
    summary = {
        name: {key: r[key] for key in ("hit@5", "mrr@5", "ndcg@10", "latency_ms")}
        | {"gate_threshold": r["gate"].threshold if r["gate"] else None}
        for name, r in results.items()
    }
    print(json.dumps({"winner": winner, "top_k": top_k, "modes": summary}, indent=2))
    if args.report:
        setup = describe_setup(settings, manifest, chunks, questions, args)
        report = markdown_report(
            results,
            winner=winner,
            top_k=top_k,
            title=f"Retrieval: {args.questions.as_posix()}",
            setup=setup,
            frozen=frozen,
        )
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(report, encoding="utf-8", newline="\n")


def write_answers_page(args) -> None:
    import shutil
    import tempfile

    from .answers_page import render_answers_page

    questions = load_questions(args.questions)
    answers_dir = args.answers_dir
    if args.models:
        # Copy only the chosen models' files (and the verdicts) into a temporary directory.
        wanted = set(args.models.split(","))
        tmp = Path(tempfile.mkdtemp())
        for f in answers_dir.glob("*.jsonl"):
            first = f.read_text(encoding="utf-8").split("\n", 1)[0]
            if f.name == "verdicts.jsonl" or (first and json.loads(first)["model"] in wanted):
                shutil.copy(f, tmp / f.name)
        answers_dir = tmp
    html = render_answers_page(
        questions,
        answers_dir,
        title=f"Answers side by side: {args.questions.as_posix()}",
        commit=load_manifest(args.manifest).commit,
        source=args.answers_dir.as_posix(),
    )
    if answers_dir != args.answers_dir:
        shutil.rmtree(answers_dir, ignore_errors=True)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(html, encoding="utf-8", newline="\n")
    print(f"Wrote {args.out}")


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenUSD Docs Assistant")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("index", "check-corpus", "eval-retrieval", "compare-gates", "compare-passes"):
        command = commands.add_parser(name)
        command.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
        command.add_argument(
            "--source-dir", type=Path, help="Use a verified local source snapshot."
        )
        if name == "check-corpus":
            command.add_argument("--report", type=Path, help="Write chunk statistics as Markdown.")
        if name == "compare-passes":
            command.add_argument("--questions", type=Path, default=Path("eval/heldout_v2.jsonl"))
            command.add_argument(
                "--answers-dir", type=Path, default=Path("reports/answers/pass2_heldout_v2")
            )
            command.add_argument("--pricing", type=Path, default=Path("eval/pricing.json"))
            command.add_argument(
                "--report", type=Path, default=Path("reports/pass2/heldout_v2_passes.md")
            )
            command.add_argument("--first-pass-gate", type=float, default=-0.9831)
            command.add_argument("--tag", default="pass-2-frozen", help="Tag of the frozen run.")
            command.add_argument(
                "--title", default="First pass vs second pass on held-out v2", help="Report title."
            )
            command.add_argument("--final", action="store_true", help="Allow held-out questions.")
        if name == "compare-gates":
            command.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
            command.add_argument(
                "--baseline-dir", type=Path, default=Path("reports/answers/pass2_dev_baseline")
            )
            command.add_argument(
                "--nogate-dir", type=Path, default=Path("reports/answers/pass2_dev_nogate")
            )
            command.add_argument("--report", type=Path, default=Path("reports/pass2/gates_dev.md"))
        if name == "eval-retrieval":
            command.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
            command.add_argument(
                "--modes",
                default="bm25,dense,hybrid,hybrid-rerank",
                help="Comma-separated modes; hybrid-rerank runs once per --rerankers model.",
            )
            command.add_argument("--rerankers", default=",".join(RERANKERS))
            command.add_argument("--report", type=Path, help="Write the comparison as Markdown.")
            command.add_argument(
                "--final", action="store_true", help="Allow a held-out run with frozen settings."
            )
    rebuild = commands.add_parser(
        "build-manifest", help="List every docs/**/*.rst at the pinned commit and hash it."
    )
    rebuild.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    rebuild.add_argument(
        "--snapshot-dir", type=Path, help="Also save the downloaded files for --source-dir."
    )
    check = commands.add_parser("check-questions", help="Validate dev and held-out questions.")
    check.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    check.add_argument("--source-dir", type=Path, default=Path("data/openusd-26.08"))
    check.add_argument("--dev", type=Path, default=Path("eval/questions.jsonl"))
    check.add_argument("--heldout", type=Path, default=Path("eval/heldout_v4.jsonl"))
    answers = commands.add_parser("eval-answers", help="Answer questions with each model.")
    answers.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    answers.add_argument("--source-dir", type=Path, help="Use a verified local source snapshot.")
    answers.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    answers.add_argument("--models", required=True, help="e.g. ollama:qwen3:4b,gemini:<id>")
    answers.add_argument("--out-dir", type=Path, default=Path("reports/answers/dev"))
    answers.add_argument("--limit", type=int, default=0, help="Only the first N questions.")
    answers.add_argument("--ids", default="", help="Only these question IDs (comma-separated).")
    answers.add_argument("--final", action="store_true", help="Allow a held-out run.")
    judged = commands.add_parser("judge-answers", help="Judge saved answers and write a report.")
    judged.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    judged.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    judged.add_argument("--pricing", type=Path, default=Path("eval/pricing.json"))
    judged.add_argument("--tier", choices=("free", "paid"), required=True)
    judged.add_argument("--report", type=Path, default=Path("reports/answers_dev.md"))
    judged.add_argument("--models", default="", help="Only these model specs (comma-separated).")
    judged.add_argument("--final", action="store_true", help="Allow a held-out run.")
    labels = commands.add_parser("label-answers", help="Sample answers for human labelling.")
    labels.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    labels.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    labels.add_argument("--out", type=Path, default=Path("eval/llm_labels.jsonl"))
    labels.add_argument("--models", default="", help="Only these model specs (comma-separated).")
    labels.add_argument("-n", type=int, default=20)
    page = commands.add_parser(
        "answers-page", help="Write a static HTML page comparing answers side by side."
    )
    page.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    page.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    page.add_argument("--models", default="", help="Only these model specs (comma-separated).")
    page.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    page.add_argument("--out", type=Path, default=Path("reports/answers_dev.html"))
    page.add_argument("--final", action="store_true", help="Allow held-out answers.")
    cites = commands.add_parser(
        "compare-citations", help="Re-check saved dev answers under each citation check (ADR 16)."
    )
    cites.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    cites.add_argument(
        "--baseline-dir", type=Path, default=Path("reports/answers/pass2_dev_baseline")
    )
    cites.add_argument("--nogate-dir", type=Path, default=Path("reports/answers/pass2_dev_nogate"))
    cites.add_argument("--scores", type=Path, default=Path("reports/pass2/gates_dev_scores.json"))
    cites.add_argument("--report", type=Path, default=Path("reports/pass2/citations_dev.md"))
    prompts = commands.add_parser(
        "compare-prompts", help="Compare answer prompts on dev with ADR 17's rule."
    )
    prompts.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    prompts.add_argument(
        "--baseline-dir", type=Path, default=Path("reports/answers/pass2_dev_baseline")
    )
    prompts.add_argument(
        "--nogate-dir", type=Path, default=Path("reports/answers/pass2_dev_nogate")
    )
    prompts.add_argument("--scores", type=Path, default=Path("reports/pass2/gates_dev_scores.json"))
    prompts.add_argument("--v2-dir", type=Path, default=Path("reports/answers/pass2_dev_prompt_v2"))
    prompts.add_argument("--report", type=Path, default=Path("reports/pass2/prompts_dev.md"))
    models_cmd = commands.add_parser(
        "compare-models", help="Compare local model variants on dev with ADR 21's rule."
    )
    models_cmd.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    models_cmd.add_argument(
        "--baseline-dir", type=Path, default=Path("reports/answers/pass2_dev_baseline")
    )
    models_cmd.add_argument(
        "--nogate-dir", type=Path, default=Path("reports/answers/pass2_dev_nogate")
    )
    models_cmd.add_argument(
        "--scores", type=Path, default=Path("reports/pass2/gates_dev_scores.json")
    )
    models_cmd.add_argument(
        "--former-heldout-dir", type=Path, default=Path("reports/answers/pass2_heldout_v2")
    )
    models_cmd.add_argument(
        "--new-dir", type=Path, default=Path("reports/answers/pass3_dev_models")
    )
    models_cmd.add_argument("--report", type=Path, default=Path("reports/pass3/models_dev.md"))
    refusals = commands.add_parser(
        "refusal-report", help="Report model refusals from a run without the retrieval gate."
    )
    refusals.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    refusals.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev_nogate"))
    refusals.add_argument("--report", type=Path, default=Path("reports/refusals_nogate_dev.md"))
    variants = commands.add_parser("compare-variants", help="Pick reasoning variants on dev.")
    variants.add_argument("--questions", type=Path, default=Path("eval/questions.jsonl"))
    variants.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    variants.add_argument("--pricing", type=Path, default=Path("eval/pricing.json"))
    variants.add_argument("--report", type=Path, default=Path("reports/variants_dev.md"))
    reverify = commands.add_parser(
        "reverify-answers", help="Re-apply the citation check to saved answers."
    )
    reverify.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    calib = commands.add_parser(
        "calibrate-judge", help="Compare judge verdicts to reference labels."
    )
    calib.add_argument("--labels", type=Path, default=Path("eval/llm_labels.jsonl"))
    calib.add_argument("--answers-dir", type=Path, default=Path("reports/answers/dev"))
    calib.add_argument("--report", type=Path, default=Path("reports/judge_calibration_dev.md"))
    serve = commands.add_parser("serve")
    serve.add_argument("--manifest", type=Path, default=Path("corpus/manifest.json"))
    serve.add_argument("--source-dir", type=Path, help="Use a verified local source snapshot.")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    try:
        if args.command == "build-manifest":
            current = json.loads(args.manifest.read_text(encoding="utf-8"))
            manifest = build_manifest(
                current, github_tree, github_file, snapshot_dir=args.snapshot_dir
            )
            text = json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"
            args.manifest.write_text(text, encoding="utf-8", newline="\n")
            load_manifest(args.manifest)
            print(f"OpenUSD {manifest['release']}: {len(manifest['documents'])} documents.")
            return 0
        if args.command == "check-questions":
            sets = {"dev": load_questions(args.dev)}
            if args.heldout.exists():
                sets["heldout"] = load_questions(args.heldout)
            result = validate_question_sets(sets, load_manifest(args.manifest), args.source_dir)
            print(json.dumps(result, indent=2))
            return 1 if result["errors"] else 0
        settings = Settings()
        questions_path = getattr(args, "questions", None)
        if (
            questions_path
            and "heldout" in questions_path.name
            and not getattr(args, "final", False)
        ):
            raise ValueError("Held-out questions need --final; tune settings on dev only.")
        if args.command == "judge-answers":
            judge_answers(args, settings)
            return 0
        if args.command == "label-answers":
            write_label_template(args)
            return 0
        if args.command == "reverify-answers":
            reverify_answers(args)
            return 0
        if args.command == "answers-page":
            write_answers_page(args)
            return 0
        if args.command == "compare-models":
            from .model_compare import choose_model, current_variants, models_report, summarize
            from .prompt_compare import fresh_run

            check = settings.citation_check
            runs = {
                spec: records
                for spec, records in current_variants(
                    args.baseline_dir,
                    args.nogate_dir,
                    args.scores,
                    args.former_heldout_dir,
                    settings.rerank_min_score,
                    check,
                ).items()
                if spec.startswith("ollama:")
            } | fresh_run(args.new_dir, check)
            questions = load_questions(args.questions)
            ids = {q.id for q in questions}
            for spec, records in runs.items():
                if {r.id for r in records} != ids:
                    raise ValueError(f"{spec} does not cover the {len(ids)} dev questions")
            results = {spec: summarize(records) for spec, records in runs.items()}
            chosen = choose_model(results, sum(q.answerable for q in questions))
            setup = [
                f"- Questions: `{args.questions.as_posix()}`, {len(ids)} total; gate "
                f"{settings.rerank_min_score}; citation check `{check}`; prompt "
                f"`{settings.answer_prompt}`.",
                f"- Current variants: replayed from `{args.baseline_dir.as_posix()}`, "
                f"`{args.nogate_dir.as_posix()}` and `{args.former_heldout_dir.as_posix()}`. "
                f"New variants: `{args.new_dir.as_posix()}`.",
            ]
            report = models_report(results, chosen, setup)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report, encoding="utf-8", newline=chr(10))
            print(report)
            return 0
        if args.command == "compare-prompts":
            from .prompt_compare import (
                choose_prompt,
                fresh_run,
                prompt_report,
                replayed_baseline,
                summarize,
            )

            check = settings.citation_check
            results = {
                "v1": summarize(
                    replayed_baseline(
                        args.baseline_dir,
                        args.nogate_dir,
                        args.scores,
                        settings.rerank_min_score,
                        check,
                    )
                ),
                "v2": summarize(fresh_run(args.v2_dir, check)),
            }
            answerable = sum(q.answerable for q in load_questions(args.questions))
            chosen = choose_prompt(results, answerable)
            setup = [
                f"- Questions: `{args.questions.as_posix()}`; gate {settings.rerank_min_score}; "
                f"citation check `{check}`.",
                f"- v1: saved second-pass answers replayed from `{args.baseline_dir.as_posix()}` "
                f"and `{args.nogate_dir.as_posix()}`. v2: a new run in `{args.v2_dir.as_posix()}`.",
            ]
            report = prompt_report(results, chosen, setup)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report, encoding="utf-8", newline=chr(10))
            print(report)
            return 0
        if args.command == "compare-citations":
            from .citation_compare import citation_report, compare_citations

            results, chosen, newly = compare_citations(
                args.questions,
                args.baseline_dir,
                args.nogate_dir,
                args.scores,
                settings.rerank_min_score,
            )
            setup = [
                f"- Questions: `{args.questions.as_posix()}`; answers replayed from "
                f"`{args.baseline_dir.as_posix()}` and `{args.nogate_dir.as_posix()}` under the "
                f"deployed gate {settings.rerank_min_score} (scores: `{args.scores.as_posix()}`).",
                "- No model was called; only the citation check differs between rows.",
            ]
            report = citation_report(results, chosen, newly, setup)
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(report, encoding="utf-8", newline=chr(10))
            print(report)
            return 0
        if args.command == "refusal-report":
            model_refusal_report(args)
            return 0
        if args.command == "compare-variants":
            compare_variants(args)
            return 0
        if args.command == "calibrate-judge":
            calibrate_judge(args)
            return 0
        serving = args.command in {"serve", "eval-answers"}
        needs_chunks = serving and settings.retrieval_mode != "dense"
        if (
            args.command
            in {"index", "check-corpus", "eval-retrieval", "compare-gates", "compare-passes"}
            or needs_chunks
        ):
            manifest = load_manifest(args.manifest)
            chunks = fetch_chunks(manifest, source_dir=args.source_dir)
            if args.command == "check-corpus":
                print(f"OpenUSD {manifest.release}: {len(chunks)} verified chunks.")
                if args.report:
                    args.report.parent.mkdir(parents=True, exist_ok=True)
                    report = corpus_report(manifest, chunks)
                    args.report.write_text(report, encoding="utf-8", newline="\n")
                return 0
            if args.command == "eval-retrieval" and set(args.modes.split(",")) == {"bm25"}:
                run_retrieval_eval(args, settings, manifest, chunks, index=None)
                return 0  # BM25 alone needs neither Ollama nor Qdrant

        models = OllamaModels(settings)
        client = connect_qdrant(settings)
        try:
            index = QdrantIndex(client, models, settings)
            if args.command == "index":
                print(f"OpenUSD {manifest.release}: {len(chunks)} verified chunks.")
                changed = index.index(chunks)
                print("Index activated." if changed else "The current index already matches.")
            elif args.command == "compare-passes":
                index.index(chunks)
                run_pass_comparison(args, settings, chunks, index)
            elif args.command == "compare-gates":
                index.index(chunks)
                run_gate_comparison(args, settings, manifest, chunks, index)
            elif args.command == "eval-retrieval":
                index.index(chunks)  # make sure the dense index matches this corpus
                run_retrieval_eval(args, settings, manifest, chunks, index)
            else:
                retrieve = build_retriever(
                    settings.retrieval_mode,
                    chunks=chunks if needs_chunks else [],
                    dense=index,
                    scorer=lambda: fastembed_scorer(
                        settings.reranker_model, settings.reranker_cache
                    ),
                    top_k=settings.top_k,
                    min_score=settings.min_score,
                    rerank_min_score=settings.rerank_min_score,
                    candidate_depth=settings.candidate_depth,
                    rerank_depth=settings.rerank_depth,
                )
                if args.command == "eval-answers":
                    generate_answers(args, settings, retrieve, OllamaModels)
                else:
                    chat = make_chat(settings, models)
                    app = create_app(retrieve, chat.generate, index.ready, settings.citation_check)
                    uvicorn.run(app, host=args.host, port=args.port)
        finally:
            client.close()
    except (
        ValueError,
        URLError,
        OSError,
        DependencyUnavailable,
        DependencyTimeout,
        ResponseHandlingException,
        UnexpectedResponse,
    ) as exc:
        # Provider exceptions contain operational details that should stay off API responses.
        print(f"OpenUSD assistant: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
