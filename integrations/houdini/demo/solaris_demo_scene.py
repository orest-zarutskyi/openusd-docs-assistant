"""Build the small Solaris scene used for the consultant screenshots.

Run it in Houdini's Python Shell or with ``hou.session``-style execution:

    exec(open("integrations/houdini/demo/solaris_demo_scene.py").read())

It references two sample assets that ship with Houdini (rubber toy and squab, each with a payload
and material variants), adds a camera, a dome light and Karma render settings, shows the result
in the Karma viewport, selects the rubber toy and docks the consultant in the Parameters pane.
"""

import hou

ASSETS = "$HFS/houdini/usd/assets"


def build():
    stage = hou.node("/stage")
    for child in stage.children():
        child.destroy()
    toy = stage.createNode("reference", "rubbertoy")
    toy.parm("primpath").set("/rubbertoy")
    toy.parm("filepath1").set(f"{ASSETS}/rubbertoy/rubbertoy.usd")
    squab = stage.createNode("reference", "squab")
    squab.setInput(0, toy)
    squab.parm("primpath").set("/squab")
    squab.parm("filepath1").set(f"{ASSETS}/squab/squab.usd")
    move = stage.createNode("xform", "place_squab")
    move.setInput(0, squab)
    move.parm("primpattern").set("/squab")
    move.parmTuple("t").set((2.6, 0, -1.2))
    move.parmTuple("r").set((0, -25, 0))
    camera = stage.createNode("camera", "shot_cam")
    camera.setInput(0, move)
    camera.parmTuple("t").set((0.7, 0.9, 3.6))
    camera.parmTuple("r").set((-8, 8, 0))
    light = stage.createNode("domelight::3.0", "dome")
    light.setInput(0, camera)
    settings = stage.createNode("karmarenderproperties", "karma_settings")
    settings.setInput(0, light)
    rop = stage.createNode("usdrender_rop", "render")
    rop.setInput(0, settings)
    stage.layoutChildren()
    settings.setDisplayFlag(True)
    settings.setCurrent(True, clear_all_selected=True)
    return settings


def show():
    try:
        hou.ui.desktop("Solaris").setAsCurrent()
    except (AttributeError, hou.OperationFailed):
        pass
    build()
    import openusd_consultant

    viewer = openusd_consultant.lop_viewer()
    if viewer is not None:
        try:
            viewer.setHydraRenderer("Karma CPU")
        except hou.OperationFailed:
            pass
        viewer.setCurrentSceneGraphSelection(["/rubbertoy"])
    openusd_consultant.dock()


show()
