# OpenUSD Consultant for Houdini

A chat panel for Solaris. It sends a question to a running OpenUSD Docs Assistant and shows the
answer, with links to the exact lines of the OpenUSD 26.08 documentation. It can add the prim
selected in the viewer to the question. It is a thin client: the assistant itself runs outside
Houdini (`openusd-assistant serve` or Docker Compose).

Requires Houdini 20.5 or newer (Python 3.11, PySide6 through `hutil.Qt`).

## Install

1. Start the assistant. See the main [README](../../README.md); by default it listens on
   `http://127.0.0.1:8000`.
2. Copy `openusd_consultant.json` into your Houdini packages folder, for example
   `%USERPROFILE%\Documents\houdini21.0\packages\`. Edit `OPENUSD_CONSULTANT` in it to point at this
   folder.
3. Restart Houdini. Then open the consultant in either of two ways:
   - the **USD Consultant** tool on the **OpenUSD** shelf docks it as a tab in the Parameters pane,
     so the viewer stays visible;
   - New Pane Tab → Misc → **OpenUSD Consultant** puts it in any pane.

To use another server, set `OPENUSD_ASSISTANT_URL`, for example in the package's `env`.

## What it does and does not do

- With **Include the selected prim** on, the panel reads the first prim selected in the Solaris
  viewer from the displayed LOP node's stage. It appends one sentence to the question: the prim's
  path, type, kind, composition arcs (references, payload, inherits, specializes, instancing),
  variant sets and applied schemas. The sentence is shown under the toggle before you ask, and
  next to your question in the chat. Nothing else from the scene is sent.
- The assistant only knows the documentation. The scene sentence becomes part of the question
  text, so it also affects which passages are retrieved. It does not let the assistant inspect
  or change the scene.
- Answers are the assistant's, so they come with the same guarantees. Every quote is checked
  against the cited chunk, and the assistant refuses when the documentation does not cover the
  question.
- Requests run on a background thread, so Houdini stays responsive while the model works. That
  takes about 5 s with Gemini Flash-Lite and about 20 s with the local qwen3.5:9b with thinking.

## Screenshots

`demo/solaris_demo_scene.py` builds the scene used for the screenshots in the main README: the
rubber toy and squab sample assets, a camera, a dome light and Karma settings, with the Karma
viewport on and the toy selected. `demo/capture_screenshots.py` then asks three questions in the
panel and saves a screenshot after each answer.
