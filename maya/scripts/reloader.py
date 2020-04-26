import sys


reload_list = [
    'samkit',
    'samcon',
    'samcon.utils',
    'samgui',
    'samgui.delegate',
    'samgui.model',
    'samgui.widget',
]


def execute():

    import samgui
    for name, widget in samgui.Docker._windows.items():
        widget.close()
    samgui.Docker._windows = []

    for mod in reload_list:
        try:
            __import__(mod)
            reload(sys.modules[mod])
        except Exception as err:
            print(err)
