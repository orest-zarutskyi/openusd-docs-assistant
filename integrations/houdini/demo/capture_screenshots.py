"""Ask the consultant a few questions in the demo scene and save screenshots of the main window.

Run after solaris_demo_scene.py, inside a Houdini GUI session, with the assistant running:

    exec(open("integrations/houdini/demo/capture_screenshots.py").read())

Screenshots go to OPENUSD_DEMO_OUT (default: the current directory). The questions are asked
exactly as typed; the panel adds the selected prim's description when the toggle is on.
"""

import os

import hou
from hutil.Qt import QtCore, QtWidgets

OUT = os.environ.get("OPENUSD_DEMO_OUT", os.getcwd())
QUESTIONS = (
    (
        "houdini_consultant_payload.png",
        "This asset is slow to load in my shot. "
        "How can I open the stage without loading its payload?",
    ),
    (
        "houdini_consultant_variant.png",
        "How do I switch the material variant of this asset from my shot layer?",
    ),
    ("houdini_consultant_refusal.png", "What Karma XPU settings remove fireflies on this toy?"),
)
SETTLE_MS = 45_000  # let the Karma viewport converge before the first capture


def _widget():
    for tab in hou.ui.curDesktop().paneTabs():
        if tab.type() == hou.paneTabType.PythonPanel:
            interface = tab.activeInterface()
            if interface is not None and interface.name() == "openusd_consultant":
                return tab.activeInterfaceRootWidget()
    return None


def _save(name):
    """Grab the screen pixels under the main window, so the GL viewport is included."""
    window = hou.qt.mainWindow()
    window.raise_()
    window.activateWindow()
    geometry = window.frameGeometry()
    screen = QtWidgets.QApplication.screenAt(geometry.center())
    path = os.path.join(OUT, name)
    screen.grabWindow(0, geometry.x(), geometry.y(), geometry.width(), geometry.height()).save(path)
    print("saved", path)


def _select(path="/rubbertoy"):
    import openusd_consultant

    viewer = openusd_consultant.lop_viewer()
    if viewer is None:
        viewer = hou.ui.paneTabOfType(hou.paneTabType.SceneViewer)
        viewer.setPwd(hou.node("/stage"))
    viewer.setCurrentSceneGraphSelection([path])


def _ask(index):
    widget = _widget()
    if widget is None or index >= len(QUESTIONS):
        _keep_on_top(False)
        if os.environ.get("OPENUSD_DEMO_EXIT"):
            hou.exit(suppress_save_prompt=True)
        return
    name, question = QUESTIONS[index]
    _select()
    widget._refresh_context()
    print("context:", widget._context or "(none)")
    widget.question.setText(question)
    widget.submit()

    def wait():
        if widget._worker is not None:
            QtCore.QTimer.singleShot(500, wait)
            return
        QtCore.QTimer.singleShot(800, lambda: (_save(name), _ask(index + 1)))

    QtCore.QTimer.singleShot(500, wait)


def _keep_on_top(on):
    """Keep Houdini above other windows while capturing, so the screen grab shows only Houdini."""
    window = hou.qt.mainWindow()
    window.setWindowFlag(QtCore.Qt.WindowStaysOnTopHint, on)
    window.showMaximized()


_keep_on_top(True)
QtCore.QTimer.singleShot(SETTLE_MS, lambda: _ask(0))
