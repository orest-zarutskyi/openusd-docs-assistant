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
    provider, _, model = spec.partition(":")
    if provider not in {"ollama", "gemini"} or not model:
        raise ValueError(f"Model must look like ollama:<tag> or gemini:<id>, not {spec!r}")
    return provider, model


def slug(model_spec: str) -> str:
    return re.sub(r"[^A-Za-z0-9.-]+", "_", model_spec)


def chat_for(spec: str, settings, ollama_models_factory):
    provider, model = parse_model(spec)
    if provider == "gemini":
        return GeminiChat(
            settings.model_copy(update={"chat_provider": "gemini", "gemini_model": model})
        )
    return ollama_models_factory(settings.model_copy(update={"chat_model": model}))


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
    compared = [parse_model(spec)[1] for spec in runs]
    judge = Judge(settings, compared_models=compared)
    cache_path = args.answers_dir / "verdicts.jsonl"
    cache = _verdict_cache(cache_path)
    prices = load_prices(args.pricing)
    judge_price = prices.get(judge.model, Price())
    judge_cost = 0.0

    for spec, records in runs.items():
        for record in records:
            key = (spec, record.id)
            if record.outcome != "answer" or (
                key in cache and cache[key]["prompt_sha256"] == judge.prompt_sha256
            ):
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
        f"- Judge: `{judge.model}`, prompt `eval/prompts/judge.md` (sha256 `{judge.prompt_sha256}`); "
        f"judge cost of this run ${judge_cost:.4f}.",
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
        raise ValueError(f"{args.out} exists; refusing to overwrite human labels")
    questions = {q.id: q for q in load_questions(args.questions)}
    records = [
        r
        for f in sorted(args.answers_dir.glob("*.jsonl"))
        if f.name != "verdicts.jsonl"
        for r in load_records(f)
    ]
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
