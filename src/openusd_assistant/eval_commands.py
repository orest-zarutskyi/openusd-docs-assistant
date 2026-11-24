"""CLI handlers for answer generation, judging, human labels and judge calibration."""

import json
import re
from pathlib import Path

from .answer_eval import Price, answer_metrics, load_records, run_answers, save_records
from .chat import GeminiChat
from .judge import Judge, Verdict, calibrate, judge_metrics, label_template
from .questions import load_questions
from .retrieval_eval import percentile


def parse_model(spec: str) -> tuple[str, str]:
    """Split ``provider:model[@variant]`` into provider and model ID (variant dropped)."""
    provider, _, rest = spec.partition(":")
    model = rest.partition("@")[0]
    if provider not in {"ollama", "gemini"} or not model:
        raise ValueError(f"Model must look like ollama:<tag> or gemini:<id>, not {spec!r}")
    return provider, model


def variant_settings(spec: str) -> dict:
    """Settings for a variant: ollama ``@think``/``@nothink``; gemini ``@budget=N``/``@level=X``."""
    provider, _ = parse_model(spec)
    variant = spec.partition("@")[2]
    if not variant:
        return {}
    if provider == "ollama" and variant in {"think", "nothink"}:
        return {"ollama_reasoning": variant == "think"}
    key, _, value = variant.partition("=")
    if provider == "gemini" and key == "budget" and value.lstrip("-").isdigit():
        return {"gemini_thinking_budget": int(value), "gemini_thinking_level": None}
    if provider == "gemini" and key == "level" and value:
        return {"gemini_thinking_level": value, "gemini_thinking_budget": None}
    raise ValueError(f"Unknown variant {variant!r} for {spec!r}")


def slug(model_spec: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "_", model_spec)


def chat_for(spec: str, settings, ollama_models_factory):
    provider, model = parse_model(spec)
    options = variant_settings(spec)
    if provider == "gemini":
        update = {"chat_provider": "gemini", "gemini_model": model} | options
        return GeminiChat(settings.model_copy(update=update))
    return ollama_models_factory(settings.model_copy(update={"chat_model": model} | options))


def load_prices(path: Path) -> dict[str, Price]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {
        model: Price(entry["input"], entry["output"])
        for model, entry in data["usd_per_million_tokens"].items()
    }


def price_for(spec: str, prices: dict[str, Price]) -> Price:
    provider, model = parse_model(spec)
    if provider == "ollama":
        return Price()
    if model not in prices:
        raise ValueError(f"No price for {model} in the pricing file")
    return prices[model]


def generate_answers(args, settings, retrieve, ollama_models_factory) -> None:
    questions = load_questions(args.questions)[: args.limit or None]
    contexts: dict[str, list] = {}

    def shared_retrieve(text: str):
        # Every model answers from the same retrieved context.
        if text not in contexts:
            contexts[text] = retrieve(text)
        return contexts[text]

    for spec in args.models.split(","):
        chat = chat_for(spec, settings, ollama_models_factory)

        def progress(record, spec=spec):
            print(f"{spec} {record.id}: {record.outcome} ({record.latency_ms:.0f} ms)", flush=True)

        records = run_answers(questions, shared_retrieve, chat, spec, progress=progress)
        save_records(args.out_dir / f"{slug(spec)}.jsonl", records)


def _verdict_cache(path: Path) -> dict[tuple[str, str], dict]:
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {(row["model"], row["id"]): row for row in rows}


def judge_answers(args, settings) -> None:
    questions = {q.id: q for q in load_questions(args.questions)}
    files = sorted(args.answers_dir.glob("*.jsonl"))
    files = [f for f in files if f.name != "verdicts.jsonl"]
    runs = {load_records(f)[0].model: load_records(f) for f in files}
    wanted = set(args.models.split(",")) if getattr(args, "models", "") else None
    if wanted:
        if missing := wanted - set(runs):
            raise ValueError(f"No answers found for {sorted(missing)}")
        runs = {spec: records for spec, records in runs.items() if spec in wanted}
    compared = [parse_model(spec)[1] for spec in runs]
    judge = Judge(settings, compared_models=compared)
    cache_path = args.answers_dir / "verdicts.jsonl"
    cache = _verdict_cache(cache_path)
    prices = load_prices(args.pricing)
    judge_price = prices.get(judge.model, Price())
    judge_cost = 0.0

    def cached(key) -> bool:
        row = cache.get(key)
        return (
            bool(row)
            and row["verdict"] is not None
            and (row["judge"], row["prompt_sha256"]) == (judge.model, judge.prompt_sha256)
        )

    # Append each verdict as it arrives so a quota error or crash mid-run keeps the
    # finished ones; a rerun skips them and asks again only where the judge's output
    # was unusable. Later rows win when the cache is reloaded.
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with cache_path.open("a", encoding="utf-8", newline="\n") as log:
        for spec, records in runs.items():
            for record in records:
                key = (spec, record.id)
                if record.outcome != "answer" or cached(key):
                    continue
                verdict, usage = judge.grade(record, questions[record.id])
                judge_cost += judge_price.cost(usage.__dict__)
                cache[key] = {
                    "model": spec,
                    "id": record.id,
                    "judge": judge.model,
                    "prompt_sha256": judge.prompt_sha256,
                    "verdict": verdict.model_dump() if verdict else None,
                }
                log.write(json.dumps(cache[key], ensure_ascii=False) + "\n")
                log.flush()
                print(f"judged {spec} {record.id}", flush=True)
    cache_path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in cache.values()),
        encoding="utf-8",
        newline="\n",
    )

    results = {}
    for spec, records in runs.items():
        verdicts = {
            r.id: Verdict.model_validate(cache[(spec, r.id)]["verdict"])
            if cache.get((spec, r.id), {}).get("verdict")
            else None
            for r in records
            if r.outcome == "answer"
        }
        generation = [r.generation_ms for r in records if r.generation_ms]
        results[spec] = (
            answer_metrics(records, price_for(spec, prices))
            | judge_metrics(records, verdicts)
            | {"generation_p50": percentile(generation, 0.5) if generation else None}
        )
    report = answers_report(results, args, judge, judge_cost)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline="\n")
    print(report)


def answers_report(results: dict[str, dict], args, judge: Judge, judge_cost: float) -> str:
    def pct(value):
        return "—" if value is None else f"{value:.0%}"

    def ms(value):
        return "—" if value is None else f"{value / 1000:.1f}"

    lines = [
        f"# Answers: {args.questions.as_posix()}",
        "",
        f"- Answers: `{args.answers_dir.as_posix()}`; billing tier for Gemini calls: {args.tier}.",
        f"- Judge: `{judge.model}` via {getattr(judge, 'route', judge.provider)}, prompt "
        f"`eval/prompts/judge.md` (sha256 `{judge.prompt_sha256}`); judge cost of the calls made "
        f"in this run at official prices ${judge_cost:.4f} (a gateway may bill differently).",
        f"- Prices: `{args.pricing.as_posix()}`; Ollama models are $0.",
        "",
        "| Model | Citations valid | Correct refusals | False refusals | Facts covered | "
        "Claims supported | Fully grounded | Invalid output | p50 s | p95 s | $ / 100 q |",
        "| --- |" + " --- |" * 10,
    ]
    for spec, r in results.items():
        lines.append(
            f"| `{spec}` | {pct(r['citation_validity'])} | {pct(r['correct_refusal'])} | "
            f"{pct(r['false_refusal'])} | {pct(r['fact_coverage'])} | {pct(r['claims_supported'])} | "
            f"{pct(r['fully_grounded'])} | {pct(r['invalid_output'])} | {ms(r['latency_ms']['p50'])} | "
            f"{ms(r['latency_ms']['p95'])} | ${r['cost_per_100']:.4f} |"
        )
    lines += [
        "",
        "Citations valid: of answers the model claimed, every quote appears in a retrieved chunk. "
        "Refusals count both the retrieval gate and the model. Facts covered and groundedness "
        "come from the judge and cover answered questions only. Latency is end to end "
        "(retrieval and generation).",
        "",
        "| Model | Questions | Errors | Judge failures | Input tokens | Output tokens | Thinking tokens |",
        "| --- | --- | --- | --- | --- | --- | --- |",
        *(
            f"| `{spec}` | {r['questions']} | {r['errors']} | {r['judge_failures']} | "
            f"{r['tokens']['input_tokens']} | {r['tokens']['output_tokens']} | "
            f"{r['tokens']['thinking_tokens']} |"
            for spec, r in results.items()
        ),
    ]
    return "\n".join(lines) + "\n"


def write_label_template(args) -> None:
    if args.out.exists():
        raise ValueError(f"{args.out} exists; refusing to overwrite labels")
    questions = {q.id: q for q in load_questions(args.questions)}
    wanted = set(args.models.split(",")) if args.models else None
    records = [
        r
        for f in sorted(args.answers_dir.glob("*.jsonl"))
        if f.name != "verdicts.jsonl"
        for r in load_records(f)
        if wanted is None or r.model in wanted
    ]
    if wanted and {r.model for r in records} != wanted:
        raise ValueError(f"No answers found for {sorted(wanted - {r.model for r in records})}")
    labels = label_template(records, questions, n=args.n)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(
        "".join(json.dumps(label, ensure_ascii=False) + "\n" for label in labels),
        encoding="utf-8",
        newline="\n",
    )
    print(f"Wrote {len(labels)} answers to label in {args.out}")


def calibrate_judge(args) -> None:
    labels = [
        json.loads(line) for line in args.labels.read_text(encoding="utf-8").splitlines() if line
    ]
    cache = _verdict_cache(args.answers_dir / "verdicts.jsonl")
    verdicts = {
        key: Verdict.model_validate(row["verdict"]) if row["verdict"] else None
        for key, row in cache.items()
    }
    print(json.dumps(calibrate(labels, verdicts), indent=2))


def compare_variants(args) -> None:
    """Pick each model's reasoning variant on dev with the judge-free rule."""
    from .answer_eval import choose_variants, variant_score

    questions = load_questions(args.questions)
    answerable = sum(q.answerable for q in questions)
    files = [f for f in sorted(args.answers_dir.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
    runs = {load_records(f)[0].model: load_records(f) for f in files}
    prices = load_prices(args.pricing)
    results = {spec: answer_metrics(recs, price_for(spec, prices)) for spec, recs in runs.items()}
    chosen = choose_variants(results, answerable)

    def pct(value):
        return "—" if value is None else f"{value:.0%}"

    lines = [
        f"# Reasoning variants: {args.questions.as_posix()}",
        "",
        "Rule, fixed before the runs: per model, the highest score = (answerable questions "
        "answered with valid citations + correct refusals) / 2; variants within one answerable "
        "question of the best are decided by lower p50 latency. No judge output is used.",
        "",
        "| Variant | Answered (valid citations) | Correct refusals | False refusals | "
        "Invalid output | Citations valid | Score | p50 s | p95 s | Chosen |",
        "| --- |" + " --- |" * 9,
    ]
    for spec, r in results.items():
        mark = "yes" if spec in chosen.values() else ""
        lines.append(
            f"| `{spec}` | {pct(r['answered_answerable'])} | {pct(r['correct_refusal'])} | "
            f"{pct(r['false_refusal'])} | {pct(r['invalid_output'])} | {pct(r['citation_validity'])} | "
            f"{variant_score(r):.3f} | {r['latency_ms']['p50'] / 1000:.1f} | "
            f"{r['latency_ms']['p95'] / 1000:.1f} | {mark} |"
        )
    lines += [
        "",
        "## Why citations fail",
        "",
        "An answer counts only if every quote is verbatim in its chunk, as the API requires. "
        "Quote validity counts quotes one by one.",
        "",
        "| Variant | Claimed answers | Quotes verbatim | Answers without quotes | "
        "Unanswerable reaching the model | Refused by the model |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for spec, r in results.items():
        claimed = sum(1 for rec in runs[spec] if rec.outcome in {"answer", "invalid_citation"})
        lines.append(
            f"| `{spec}` | {claimed} | {pct(r['quote_validity'])} | {r['no_evidence_answers']} | "
            f"{r['unanswerable_reaching_model']} | {r['model_refused_unanswerable']} |"
        )
    report = "\n".join(lines) + "\n"
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(report, encoding="utf-8", newline="\n")
    print(report)


def reverify_answers(args) -> None:
    from .answer_eval import reverify

    for path in sorted(args.answers_dir.glob("*.jsonl")):
        if path.name == "verdicts.jsonl":
            continue
        before = load_records(path)
        after = [reverify(r) for r in before]
        changed = [
            (b.id, b.outcome, a.outcome) for b, a in zip(before, after) if b.outcome != a.outcome
        ]
        save_records(path, after)
        print(f"{path.name}: {len(changed)} changed {changed}")
