"""A static HTML page that shows every model's answer to each question side by side."""

import json
from html import escape
from pathlib import Path

from .answer_eval import AnswerRecord, load_records
from .questions import Question

GITHUB = "https://github.com/PixarAnimationStudios/OpenUSD/blob/{commit}/{path}#L{start}-L{end}"

OUTCOME_LABELS = {
    "answer": ("answered", "ok"),
    "refused_retrieval": ("refused by retrieval gate", "refuse"),
    "refused_model": ("refused by model", "refuse"),
    "invalid_citation": ("invalid citation", "bad"),
    "invalid_output": ("invalid output", "bad"),
    "error": ("provider error", "bad"),
}

STYLE = """
body{font:15px/1.5 system-ui,sans-serif;margin:0 auto;max-width:1400px;padding:24px;color:#1d1d1f}
h1{font-size:22px}h2{font-size:17px;margin:0 0 4px}
.q{border-top:1px solid #ddd;padding:20px 0}.meta{color:#666;font-size:13px}
.facts{margin:6px 0 12px;padding-left:20px;font-size:14px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:12px}
.card{border:1px solid #ddd;border-radius:8px;padding:12px;background:#fafafa}
.model{font-weight:600;font-size:14px}.badge{display:inline-block;border-radius:4px;
padding:1px 6px;font-size:12px;margin-left:6px}
.ok{background:#dff3e3;color:#145a26}.refuse{background:#e8eefc;color:#1d3f8a}
.bad{background:#fde6e4;color:#8a1d12}.answer{white-space:pre-wrap;margin:8px 0}
.judge{font-size:13px;color:#444}.claim{font-size:13px;color:#8a1d12}
blockquote{margin:6px 0;padding-left:8px;border-left:3px solid #ccc;font-size:13px;color:#444}
nav a{margin-right:8px;font-size:13px}
"""


def _verdicts(answers_dir: Path) -> dict[tuple[str, str], dict]:
    path = answers_dir / "verdicts.jsonl"
    if not path.exists():
        return {}
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
    return {(row["model"], row["id"]): row["verdict"] for row in rows if row["verdict"]}


def _card(record: AnswerRecord | None, verdict: dict | None, commit: str) -> str:
    if record is None:
        return '<div class="card"><span class="meta">no answer recorded</span></div>'
    label, kind = OUTCOME_LABELS.get(record.outcome, (record.outcome, "bad"))
    parts = [
        f'<div class="card"><span class="model">{escape(record.model)}</span>'
        f'<span class="badge {kind}">{escape(label)}</span>'
        f'<span class="meta"> · {record.latency_ms / 1000:.1f} s</span>'
    ]
    if record.answer:
        parts.append(f'<div class="answer">{escape(record.answer)}</div>')
    chunks = {c["chunk_id"]: c for c in record.context}
    for quote in record.quotes:
        chunk = chunks.get(quote.get("chunk_id"))
        source = ""
        if chunk:
            start, end = chunk["lines"]
            url = GITHUB.format(commit=commit, path=chunk["path"], start=start, end=end)
            source = f' — <a href="{escape(url)}">{escape(chunk["path"])}#L{start}-L{end}</a>'
        parts.append(f"<blockquote>{escape(quote.get('quote', ''))}{source}</blockquote>")
    if verdict:
        facts = verdict["facts"]
        covered = sum(f["covered"] for f in facts)
        bad = [c for c in verdict["claims"] if c["verdict"] != "supported"]
        judge = f"judge: {covered}/{len(facts)} facts" if facts else "judge:"
        judge += ", all claims supported" if not bad else f", {len(bad)} claim(s) not supported"
        parts.append(f'<div class="judge">{escape(judge)}</div>')
        for claim in bad:
            parts.append(
                f'<div class="claim">{escape(claim["verdict"])}: {escape(claim["claim"])}</div>'
            )
    parts.append("</div>")
    return "".join(parts)


def render_answers_page(
    questions: list[Question],
    answers_dir: Path,
    *,
    title: str,
    commit: str,
    source: str | None = None,
) -> str:
    """``source`` names the answers directory in the header (default: ``answers_dir``)."""
    files = [f for f in sorted(answers_dir.glob("*.jsonl")) if f.name != "verdicts.jsonl"]
    runs = {}
    for f in files:
        records = load_records(f)
        if records:
            runs[records[0].model] = {r.id: r for r in records}
    verdicts = _verdicts(answers_dir)
    models = sorted(runs)
    body = [
        f"<h1>{escape(title)}</h1>",
        f'<p class="meta">{len(questions)} questions · models: '
        f"{escape(', '.join(models))} · answers from <code>{escape(source or answers_dir.as_posix())}</code>"
        "</p>",
        "<nav>"
        + "".join(f'<a href="#{escape(q.id)}">{escape(q.id)}</a>' for q in questions)
        + "</nav>",
    ]
    for q in questions:
        facts = "".join(f"<li>{escape(fact)}</li>" for fact in q.expected_facts)
        body.append(
            f'<section class="q" id="{escape(q.id)}"><h2>{escape(q.question)}</h2>'
            f'<div class="meta">{escape(q.id)} · {escape(q.kind)} · '
            f"{'answerable' if q.answerable else 'not answerable from the corpus'}</div>"
            + (f'<ul class="facts">{facts}</ul>' if facts else "")
            + '<div class="grid">'
            + "".join(_card(runs[m].get(q.id), verdicts.get((m, q.id)), commit) for m in models)
            + "</div></section>"
        )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        f"<title>{escape(title)}</title><style>{STYLE}</style></head><body>"
        + "".join(body)
        + "</body></html>\n"
    )
