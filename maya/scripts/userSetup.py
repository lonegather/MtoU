from maya import cmds, mel


def setup(*_):
    import pyblish.api
    import pyblish_qml.settings

    pyblish.api.register_gui('pyblish_qml')
    pyblish_qml.settings.WindowTitle = 'Submit Assistant'
    # pyblish_qml.settings.WindowPosition = [500, 100]
    # pyblish_qml.settings.WindowSize = [800, 600]

    from samgui.widget import DockerMain
    import samcon
    print('----------Samkit Init----------')
    # DockerMain.setup()
    layout = mel.eval('$tmp = $gAttributeEditorButton').split('|attributeEditorButton')[0]
    button = cmds.formLayout(layout, q=True, ca=True)[0]
    length = cmds.iconTextCheckBox(button, q=True, height=True)
    width = cmds.formLayout(layout, q=True, width=True) + length + 1
    cmds.formLayout(layout, e=True, width=width)
    btn = cmds.iconTextButton(
        parent=layout,
        width=length,
        height=length,
        image='tool_icon.svg',
        style='iconOnly',
        command=lambda *_: DockerMain.setup()
    )
    cmds.formLayout(layout, e=True, attachForm=[(btn, 'right', 1), (btn, 'top', 1)])
    cmds.scriptJob(event=['quitApplication', lambda *_: samcon.session.close()])
    cmds.evalDeferred(lambda: cmds.inViewMessage(message='Samkit Ready', position='midCenter', fade=True))


cmds.evalDeferred(setup)
