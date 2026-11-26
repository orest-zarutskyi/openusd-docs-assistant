"""OpenUSD consultant for Houdini: ask the OpenUSD Docs Assistant without leaving Solaris.

The panel posts the question to a running assistant (``openusd-assistant serve`` or Docker
Compose) and shows the answer with links to the exact documentation lines. Optionally it adds a
one-line description of the prim selected in the Solaris viewer (its type, composition arcs and
applied schemas), so a question such as "why is this not loading?" carries the scene context.
Nothing runs inside Houdini except reading that selection and an HTTP request on a background
thread, so the UI never blocks.

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
MAX_CONTEXT_CHARS = 240
SUGGESTIONS = (
    "Which composition arc lets me open a stage before loading a heavy asset?",
    "What is the difference between a reference and a payload?",
    "How do I bind a material to a whole set of prims at once?",
)


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


def describe_prim(info: dict | None) -> str:
    """One short sentence about the selected prim, from plain data read out of the stage."""
    if not info or not info.get("path"):
        return ""
    kind = f" (kind {info['kind']})" if info.get("kind") else ""
    noun = info.get("type") or "typeless prim"
    article = "an" if noun[0].lower() in "aeiou" or noun.startswith("X") else "a"
    text = f"The selected prim {info['path']} is {article} {noun}{kind}"
    arcs = list(info.get("arcs", []))
    if info.get("variant_sets"):
        arcs.append("variant sets " + ", ".join(info["variant_sets"]))
    if arcs:
        text += " with " + ", ".join(arcs)
    if info.get("schemas"):
        text += "; applied schemas " + ", ".join(info["schemas"])
    text += "."
    if len(text) > MAX_CONTEXT_CHARS:
        text = text[: MAX_CONTEXT_CHARS - 1].rstrip(" ,;") + "…"
    return text


def compose_question(question: str, context: str) -> str:
    """The text sent to the assistant: the question, then the scene context if there is any."""
    question = question.strip()
    return f"{question}\n\nScene context: {context}" if context else question


def render_html(question: str, response: dict, seconds: float, context: str = "") -> str:
    """One exchange as chat-style HTML. Model text is untrusted, so everything is escaped,
    and only source links into the pinned OpenUSD repository are made clickable."""
    parts = [
        '<table width="100%" cellspacing="0" cellpadding="8"><tr><td width="18%"></td>'
        '<td style="background-color:#2b3442; color:#e6edf3">'
        f"<b>You</b><br>{html.escape(question)}"
    ]
    if context:
        parts.append(f'<br><span style="color:#8b98a8">Scene: {html.escape(context)}</span>')
    parts.append("</td></tr></table>")
    parts.append(
        '<table width="100%" cellspacing="0" cellpadding="8"><tr>'
        '<td style="background-color:#1c2129; color:#e6edf3"><b>OpenUSD Consultant</b><br>'
    )
    if response.get("status") == "answer":
        parts.append(html.escape(response.get("answer", "")).replace("\n", "<br>"))
        for source in response.get("sources", []):
            label = html.escape(
                f"{source.get('path', '')}#L{source.get('start_line')}-L{source.get('end_line')}"
            )
            url = source.get("url", "")
            link = (
                f'<a href="{html.escape(url, quote=True)}" style="color:#4cc2b0">{label}</a>'
                if url.startswith(SOURCE_PREFIX)
                else label
            )
            quote = html.escape(source.get("quote", ""))
            parts.append(
                f'<p style="margin-left:10px">{link}<br>'
                f'<span style="color:#9aa4b2">&ldquo;{quote}&rdquo;</span></p>'
            )
    else:
        message = html.escape(response.get("answer", "No answer."))
        parts.append(f'<span style="color:#f0a35e">{message}</span>')
    parts.append(
        f'<br><span style="color:#6b7480; font-size:small">{seconds:.1f} s</span>'
        '</td><td width="18%"></td></tr></table><br>'
    )
    return "".join(parts)


def lop_viewer():  # pragma: no cover - needs Houdini
    """The first Scene Viewer that shows a LOP network, or None."""
    import hou

    for tab in hou.ui.paneTabs():
        if tab.type() == hou.paneTabType.SceneViewer:
            network = tab.pwd()
            if network is not None and network.childTypeCategory() == hou.lopNodeTypeCategory():
                return tab
    return None


def selection_info() -> dict | None:  # pragma: no cover - needs Houdini
    """Read the first prim selected in the Solaris viewer, or None if nothing is selected."""
    viewer = lop_viewer()
    if viewer is None:
        return None
    paths = list(viewer.currentSceneGraphSelection())
    network = viewer.pwd()
    lop = network.displayNode() if network is not None else None
    if not paths or lop is None or not hasattr(lop, "stage"):
        return None
    prim = lop.stage().GetPrimAtPath(paths[0])
    if not prim or not prim.IsValid():
        return None
    from pxr import Usd

    arcs = [
        name
        for name, present in (
            ("references", prim.HasAuthoredReferences()),
            ("a payload", prim.HasAuthoredPayloads()),
            ("inherits", prim.HasAuthoredInherits()),
            ("specializes", prim.HasAuthoredSpecializes()),
        )
        if present
    ]
    if prim.IsInstance():
        arcs.append("instanceable")
    return {
        "path": str(prim.GetPath()),
        "type": str(prim.GetTypeName()),
        "kind": Usd.ModelAPI(prim).GetKind() or "",
        "arcs": arcs,
        "variant_sets": list(prim.GetVariantSets().GetNames()),
        "schemas": [str(s) for s in prim.GetAppliedSchemas()],
    }


try:  # Qt is only needed inside Houdini; the functions above are usable without it.
    from hutil.Qt import QtCore, QtWidgets
except ImportError:  # pragma: no cover - outside Houdini
    QtCore = QtWidgets = None


if QtWidgets is not None:  # pragma: no cover - needs Houdini

    class _AskWorker(QtCore.QThread):
        answered = QtCore.Signal(str, dict, float, str)
        failed = QtCore.Signal(str, str)

        def __init__(self, question: str, context: str, parent=None):
            super().__init__(parent)
            self.question = question
            self.context = context

        def run(self):
            started = time.perf_counter()
            try:
                response = ask(compose_question(self.question, self.context))
            except Exception as exc:  # noqa: BLE001 - shown to the user verbatim
                self.failed.emit(self.question, str(exc))
                return
            self.answered.emit(self.question, response, time.perf_counter() - started, self.context)

    class ConsultantWidget(QtWidgets.QWidget):
        """Chat transcript, suggested questions, a scene-context toggle and the question box."""

        def __init__(self, parent=None):
            super().__init__(parent)
            self.setWindowTitle("OpenUSD Consultant")
            self.transcript = QtWidgets.QTextBrowser()
            self.transcript.setOpenExternalLinks(True)
            self.transcript.setStyleSheet("QTextBrowser { background: #14181e; border: none; }")
            self.transcript.setHtml(
                '<p style="color:#8b98a8">Ask about USD. Answers quote the OpenUSD 26.08 '
                "documentation and link to the exact lines; questions the docs do not cover "
                "are refused.</p>"
            )
            self.suggestions = QtWidgets.QHBoxLayout()
            for text in SUGGESTIONS:
                button = QtWidgets.QPushButton(text if len(text) < 48 else text[:45] + "…")
                button.setToolTip(text)
                button.clicked.connect(lambda _=False, t=text: self._ask_suggested(t))
                self.suggestions.addWidget(button)
            self.use_selection = QtWidgets.QCheckBox("Include the selected prim")
            self.use_selection.setChecked(True)
            self.use_selection.toggled.connect(self._refresh_context)
            self.context_label = QtWidgets.QLabel()
            self.context_label.setWordWrap(True)
            self.context_label.setStyleSheet("color: #8b98a8;")
            self.question = QtWidgets.QLineEdit()
            self.question.setPlaceholderText("Ask about USD…")
            self.button = QtWidgets.QPushButton("Ask")
            self.status = QtWidgets.QLabel(f"Server: {api_url()}")
            row = QtWidgets.QHBoxLayout()
            row.addWidget(self.question)
            row.addWidget(self.button)
            layout = QtWidgets.QVBoxLayout(self)
            layout.addWidget(self.transcript, 1)
            layout.addLayout(self.suggestions)
            layout.addWidget(self.use_selection)
            layout.addWidget(self.context_label)
            layout.addLayout(row)
            layout.addWidget(self.status)
            self.button.clicked.connect(self.submit)
            self.question.returnPressed.connect(self.submit)
            self._worker = None
            self._started = 0.0
            self._ticker = QtCore.QTimer(self)
            self._ticker.timeout.connect(self._tick)
            self._context_timer = QtCore.QTimer(self)
            self._context_timer.timeout.connect(self._refresh_context)
            self._context_timer.start(1000)
            self._context = ""
            self._refresh_context()

        def _refresh_context(self):
            context = ""
            if self.use_selection.isChecked():
                try:
                    context = describe_prim(selection_info())
                except Exception:  # noqa: BLE001 - no viewer or stage yet
                    context = ""
            self._context = context
            self.context_label.setText(context or "No prim selected in the viewer.")

        def _ask_suggested(self, text):
            self.question.setText(text)
            self.submit()

        def submit(self):
            text = self.question.text().strip()
            if not text or self._worker is not None:
                return
            self.button.setEnabled(False)
            self._started = time.perf_counter()
            self._ticker.start(500)
            self._tick()
            self._worker = _AskWorker(text, self._context, self)
            self._worker.answered.connect(self._on_answer)
            self._worker.failed.connect(self._on_error)
            self._worker.finished.connect(self._done)
            self._worker.start()

        def _tick(self):
            self.status.setText(f"Thinking… {time.perf_counter() - self._started:.0f} s")

        def _on_answer(self, question, response, seconds, context):
            self.transcript.append(render_html(question, response, seconds, context))
            self.question.clear()

        def _on_error(self, question, message):
            self.transcript.append(
                f'<p style="color:#e5534b">{html.escape(question)}<br>{html.escape(message)}</p>'
            )

        def _done(self):
            self._worker = None
            self._ticker.stop()
            self.button.setEnabled(True)
            self.status.setText(f"Server: {api_url()}")

    _window = None

    def show():
        """Open the consultant as a floating window."""
        global _window
        import hou

        if _window is None:
            _window = ConsultantWidget(hou.qt.mainWindow())
            _window.setWindowFlags(QtCore.Qt.Window)
            _window.resize(640, 760)
        _window.show()
        _window.raise_()

    def dock():
        """Open the consultant as a tab in the Parameters pane, so the viewer stays visible
        (used by the shelf). Reuses a consultant tab that is already open."""
        import hou

        desktop = hou.ui.curDesktop()
        for tab in desktop.paneTabs():
            if tab.type() == hou.paneTabType.PythonPanel:
                interface = tab.activeInterface()
                if interface is not None and interface.name() == "openusd_consultant":
                    tab.setIsCurrentTab()
                    return
        anchor = None
        for kind in (
            hou.paneTabType.Parm,
            hou.paneTabType.SceneGraphTree,
            hou.paneTabType.NetworkEditor,
        ):
            anchor = desktop.paneTabOfType(kind)
            if anchor is not None:
                break
        if anchor is None:
            show()
            return
        tab = anchor.pane().createTab(hou.paneTabType.PythonPanel)
        tab.setActiveInterface(hou.pypanel.interfaceByName("openusd_consultant"))
        tab.setIsCurrentTab()
