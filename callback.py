## CloNIX callback.py
# System callbacks

import tui

import urwid

def callback(controller, data):
    data_parts = data.split(':')

    match data_parts[0]:
        case 'scr':
            controller.switch_screen(data_parts[1])

        case 'act':
            match data_parts[1]:
                case 'quit':
                    raise urwid.ExitMainLoop() #TODO: confirmation
                
                case 'deploy':
                    controller.popup_hide()
                    controller.switch_screen("deploy-prog")

        case 'var':
            pass

        case _:
            pass # Do nothing
