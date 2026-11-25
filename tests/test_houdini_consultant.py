import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

PATH = Path("integrations/houdini/python3.11libs/openusd_consultant.py")
spec = importlib.util.spec_from_file_location("openusd_consultant", PATH)
consultant = importlib.util.module_from_spec(spec)
spec.loader.exec_module(consultant)


def test_render_escapes_model_text_and_links_only_pinned_sources():
    response = {
        "status": "answer",
        "answer": "<script>x</script> Use a payload.",
        "sources": [
            {
                "path": "docs/glossary.rst",
                "start_line": 1,
                "end_line": 2,
                "url": "https://github.com/PixarAnimationStudios/OpenUSD/blob/abc/docs/glossary.rst#L1-L2",
                "quote": "a <b>deferred</b> reference",
            },
            {
                "path": "docs/x.rst",
                "start_line": 3,
                "end_line": 4,
                "url": "javascript:alert(1)",
                "quote": "q",
            },
        ],
    }
    out = consultant.render_html("What is <a payload>?", response, 1.5)
    assert "<script>" not in out and "&lt;script&gt;" in out
    assert "What is &lt;a payload&gt;?" in out and "&lt;b&gt;deferred&lt;/b&gt;" in out
    assert (
        'href="https://github.com/PixarAnimationStudios/OpenUSD/blob/abc/docs/glossary.rst#L1-L2"'
        in out
    )
    assert "javascript:" not in out and "docs/x.rst#L3-L4" in out
    refusal = consultant.render_html(
        "Pyro?", {"status": "insufficient_context", "answer": "No."}, 2.0
    )
    assert "No." in refusal and "2.0 s" in refusal


def test_ask_posts_the_question_and_reports_unreachable_servers():
    seen = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            seen["path"] = self.path
            seen["body"] = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            payload = json.dumps({"status": "answer", "answer": "A.", "sources": []}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args):
            pass

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    url = f"http://127.0.0.1:{server.server_port}"
    assert consultant.ask("What is a stage?", url=url, timeout=5)["answer"] == "A."
    assert seen == {"path": "/ask", "body": {"question": "What is a stage?"}}
    server.server_close()
    with pytest.raises(RuntimeError, match="Cannot reach the assistant"):
        consultant.ask("x", url=url, timeout=2)
