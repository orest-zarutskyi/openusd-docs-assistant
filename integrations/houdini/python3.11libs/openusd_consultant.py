"""OpenUSD consultant for Houdini: ask the OpenUSD Docs Assistant without leaving Solaris.

The panel posts the question to a running assistant (``openusd-assistant serve`` or Docker
Compose) and shows the answer with links to the exact documentation lines. Nothing runs inside
Houdini except an HTTP request on a background thread, so the UI never blocks.

Set OPENUSD_ASSISTANT_URL to point at another server (default http://127.0.0.1:8000).
"""

import html
import json
import os
import time
import urllib.error
import urllib.request

DEFAULT_URL = "http://127.0.0.1:8000"
SOURCE_PREFIX = "https://github.com/PixarAnimationStudios/OpenUSD/"


def api_url() -> str:
    return os.environ.get("OPENUSD_ASSISTANT_URL", DEFAULT_URL).rstrip("/")


def ask(question: str, url: str | None = None, timeout: float = 180) -> dict:
    """POST the question to /ask and return the JSON response."""
    request = urllib.request.Request(
        f"{url or api_url()}/ask",
        data=json.dumps({"question": question}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", "replace")[:300]
        raise RuntimeError(f"The assistant returned HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise RuntimeError(
            f"Cannot reach the assistant at {url or api_url()}. Start it with "
            "`openusd-assistant serve` or `docker compose up`."
        ) from exc


def render_html(question: str, response: dict, seconds: float) -> str:
    """One question and its answer as HTML. Model text is untrusted, so everything is escaped,
    and only source links into the pinned OpenUSD repository are made clickable."""
    parts = [f'<p style="color:#9aa4b2"><b>Q:</b> {html.escape(question)}</p>']
    if response.get("status") == "answer":
        answer = html.escape(response.get("answer", "")).replace("\n", "<br>")
        parts.append(f"<p>{answer}</p>")
        for source in response.get("sources", []):
            label = html.escape(
                f"{source.get('path', '')}#L{source.get('start_line')}-L{source.get('end_line')}"
            )
            url = source.get("url", "")
            link = (
                f'<a href="{html.escape(url, quote=True)}">{label}</a>'
                if url.startswith(SOURCE_PREFIX)
                else label
            )
            quote = html.escape(source.get("quote", ""))
            parts.append(
                f'<p style="margin-left:12px">{link}<br>'
                f'<span style="color:#9aa4b2">&ldquo;{quote}&rdquo;</span></p>'
            )
    else:
        parts.append(
            f'<p style="color:#f0a35e">{html.escape(response.get("answer", "No answer."))}</p>'
        )
    parts.append(f'<p style="color:#6b7480; font-size:small">{seconds:.1f} s</p><hr>')
    return "".join(parts)


try:  # Qt is only needed inside Houdini; the functions above are usable without it.
    from hutil.Qt import QtCore, QtWidgets
except ImportError:  # pragma: no cover - outside Houdini
    QtCore = QtWidgets = None


if QtWidgets is not None:

    class _AskWorker(QtCore.QThread):
        answered = QtCore.Signal(str, dict, float)
        failed = QtCore.Signal(str, str)

        def __init__(self, question: str, parent=None):
            super().__init__(parent)
            self.question = question

        def run(self):
            started = time.perf_counter()
            try:
                response = ask(self.question)
            except Exception as exc:  # noqa: BLE001 - shown to the user verbatim
                self.failed.emit(self.question, str(exc))
                return
            self.answered.emit(self.question, response, time.perf_counter() - started)

    class ConsultantWidget(QtWidgets.QWidget):
        """Question box, Ask button and a running transcript with clickable sources."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("OpenUSD Consultant")
            self.transcript = QtWidgets.QTextBrowser()
            self.transcript.setOpenExternalLinks(True)
            self.question = QtWidgets.QLineEdit()
            self.question.setPlaceholderText(
                "Ask about USD, e.g. Which composition arc lets me load a heavy asset later?"
            )
            self.button = QtWidgets.QPushButton("Ask")
            self.status = QtWidgets.QLabel(f"Server: {api_url()}")
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.question)
            row.addWidget(self.button)
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.transcript)
            layout.addLayout(row)
            layout.addWidget(self.status)
            self.button.clicked.connect(self.submit)
            self.question.returnPressed.connect(self.submit)
            self._worker = None

        def submit(self):
            text = self.question.text().strip()
            if not text or self._worker is not None:
                return
            self.button.setEnabled(False)
            self.status.setText("Thinking…")
            self._worker = _AskWorker(text, self)
            self._worker.answered.connect(self._on_answer)
            self._worker.failed.connect(self._on_error)
            self._worker.finished.connect(self._done)
            self._worker.start()

        def _on_answer(self, question, response, seconds):
            self.transcript.append(render_html(question, response, seconds))
            self.question.clear()

        def _on_error(self, question, message):
            self.transcript.append(
                f'<p style="color:#e5534b">{html.escape(question)}<br>{html.escape(message)}</p><hr>'
            )

        def _done(self):
            self._worker = None
            self.button.setEnabled(True)
            self.status.setText(f"Server: {api_url()}")

    _window = None

    def show():
        """Open the consultant as a floating window (used by the shelf tool)."""
        global _window
        import hou

        if _window is None:
            _window = ConsultantWidget(hou.qt.mainWindow())
            _window.setWindowFlags(QtCore.Qt.Window)
            _window.resize(640, 720)
        _window.show()
        _window.raise_()
