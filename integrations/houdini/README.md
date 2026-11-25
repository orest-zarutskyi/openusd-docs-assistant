# OpenUSD Consultant for Houdini

A small Houdini panel that sends a question to a running OpenUSD Docs Assistant and shows the
answer, with links to the exact lines of the OpenUSD 26.08 documentation. It is a thin client:
the assistant itself runs outside Houdini (`openusd-assistant serve` or Docker Compose).

Requires Houdini 20.5 or newer (Python 3.11, PySide6 through `hutil.Qt`).

## Install

1. Start the assistant. See the main [README](../../README.md); by default it listens on
   `http://127.0.0.1:8000`.
2. Copy `openusd_consultant.json` into your Houdini packages folder, for example
   `%USERPROFILE%\Documents\houdini21.0\packages\`. Edit `OPENUSD_CONSULTANT` in it to point at this
   folder.
3. Restart Houdini. Then open the consultant in either of two ways:
   - **as a pane:** New Pane Tab → Misc → **OpenUSD Consultant**;
   - **as a floating window:** the **USD Consultant** tool on the **OpenUSD** shelf.

To use another server, set `OPENUSD_ASSISTANT_URL`, for example in the package's `env`.

## What it does and does not do

- The question is sent as typed. The panel does not read the scene or the selection.
- Answers are the assistant's, so they come with the same guarantees. Every quote is checked
  against the cited chunk, and the assistant refuses when the documentation does not cover the
  question.
- Requests run on a background thread, so Houdini stays responsive while the model works. That
  can take a few seconds with Gemini, or 10–20 s with a local model that thinks.
