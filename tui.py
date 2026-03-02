## CloNIX tui.py
# Terminal user interface module; default use this when no `--no-tui` flag provided

import urwid

import callback
import tui
import util

from screens import menu, deploy, deploy_progress
from widgets import frames

# Render the footer text; last_keypress present for me to see the keys that don't get caught
def render_footer(last_keypress: str = ''):
    extra_text = util.get_config('footer_text')
    return urwid.Text(f"{extra_text} {util.VERSION}  F1: Open Help  F12: Open Terminal  {last_keypress}")

class TUIController:
    # Main event callback
    def unhandled_input(self, uin):
        if type(uin) == str:
            self.keyboard_input(uin)
        pass

    # Event callback for keyboard events
    def keyboard_input(self, key):
        self.frame.footer = render_footer(key)
        match key:
            case 'esc':
                if self.popup_open:
                    self.popup_callback(None, "popup::hide") # TODO: figure out what to do about nested popups
                else:
                    if self.screen == 'main':
                        raise urwid.ExitMainLoop() # TODO: confirmation
                    else:
                        self.switch_screen('main')
            case _:
                pass

    def __init__(self):
        # Initialize screens
        self.loop = None

        # flags
        self.popup_open = False

        # other members
        self.vars = {}
        self.screen = '';

        # Screens
        self.screens = {}
        self.screens['main'] = menu.MainMenu(self)
        self.screens['deploy'] = deploy.DeployScreen(self)
        self.screens['deploy-prog'] = deploy_progress.DeployProgressScreen(self)

        # Master root element
        self.footer = render_footer()
        self.frame = urwid.Frame(urwid.Text("Lalala"), footer=self.footer)
        self.switch_screen('main')


    # Creates a popup frame; default button destroys the popup. `attribute` defines the look of the popup (in terms of colors)
    def popup(self, title, content, action=['popup:Okay:hide'], attribute='popup-regular'):
        popup_content = [content, urwid.Divider(util.LINE_SINGLE_HORIZONTAL)]
        if len(action) >= 1:
            for ac in action:
                ac_parts = ac.split(":")
                popup_content.append(urwid.Button(ac_parts[1], on_press=self.popup_callback, user_data=ac))

        popup_pile = urwid.Pile(popup_content)
        popup_frame = urwid.AttrMap(frames.RoundedLineBox(popup_pile, title=title), attribute)
        popup_overlay = urwid.Overlay(popup_frame, self.frame.body, align='center', width=('relative', 40), valign='middle', height='pack')

        self.frame.body = popup_overlay
        self.popup_open = True

    # "Destroy" (i.e. hide) the popup
    def popup_hide(self):
        self.frame.body = self.frame.body.bottom_w
        self.popup_open = False

    # Popup button callback; TODO: allow for better integration with the callback module, for custom actions
    def popup_callback(self, button, data):
        if data.startswith('popup'):
            data_parts = data.split(":")
            match data_parts[2]:
                case 'hide':
                    self.popup_hide()

                case 'deploy':
                    callback.callback(self, 'act:deploy')

                case _:
                    return
            return
        callback.callback(self, data)

    def run(self):
        self.loop = urwid.MainLoop(self.frame, palette=util.MASTER_PALETTE, unhandled_input=self.unhandled_input)
        self.loop.run()

    # Redefines the root element's body, i.e. changes the screen
    def switch_screen(self, screen_name):
        screen = self.screens.get(screen_name)
        if screen == None:
            self.popup(f"No screen named {screen_name}", urwid.Text(f"There's no such screen named {screen_name}!"), attribute='popup-error')
            return

        self.screen = screen_name
        self.frame.body = screen.render()

    # "Variables" that can get passed around to other screens, useful for deploying
    def set_variable(self, name:str, value=None):
        self.vars[name] = value
        pass
    def get_variable(self, name:str):
        return self.vars.get(name)
