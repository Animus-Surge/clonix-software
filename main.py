from __future__ import annotations

import argparse
import os
import signal

import urwid

import callback
import util

from screens import menu, deploy, deploy_progress
from widgets import frames

VERSION = "v0.2.0"

parser = argparse.ArgumentParser(
        prog='CloNIX',
        description='NixOS/Filesystem based OS cloner')
parser.add_argument('-c', '--config')

def render_footer(last_keypress: str = ''):
    extra_text = util.get_config('footer_text')
    return urwid.Text(f"{extra_text} {VERSION}  F1: Open Help  F12: Open Terminal  {last_keypress}")

class TUIController:
    def unhandled_input(self, uin):
        if type(uin) == str:
            self.keyboard_input(uin)
        pass

    def keyboard_input(self, key):
        self.frame.footer = render_footer(key)
        match key:
            case 'esc':
                if self.popup_open:
                    self.popup_callback(None, "popup::hide")
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

        self.screens = {}
        self.screens['main'] = menu.MainMenu(self)
        self.screens['deploy'] = deploy.DeployScreen(self)
        self.screens['deploy-prog'] = deploy_progress.DeployProgressScreen(self)

        self.footer = render_footer()
        self.frame = urwid.Frame(urwid.Text("Lalala"), footer=self.footer)
        self.switch_screen('main')


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

    def popup_hide(self):
        self.frame.body = self.frame.body.bottom_w
        self.popup_open = False

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

    def switch_screen(self, screen_name):
        screen = self.screens.get(screen_name)
        if screen == None:
            self.popup(f"No screen named {screen_name}", urwid.Text(f"There's no such screen named {screen_name}!"), attribute='popup-error')
            return

        self.screen = screen_name
        self.frame.body = screen.render()

    def set_variable(self, name:str, value=None):
        self.vars[name] = value
        pass

    def get_variable(self, name:str):
        return self.vars.get(name)


def signal_handler(sig, frame):
    if sig == signal.SIGINT:
        raise urwid.ExitMainLoop()
    pass

def init():
    args = vars(parser.parse_args())
    util.load_config(args.get('config'))
    signal.signal(signal.SIGINT, signal_handler)

    TUIController().run()

if __name__=="__main__":
    print("Loading...")
    init()
