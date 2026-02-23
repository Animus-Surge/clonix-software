import urwid

import util
import widgets.frames as frames
import widgets.inputs as inputs

class DeployProgressScreen:
    def __init__(self, controller):
        self.controller = controller

        lcol_contents = [urwid.Text("PHASE 1: Drive formatting")]
        lcol_pile = urwid.Pile(lcol_contents)
        lcol = frames.RoundedLineBox(lcol_pile, "Progress")

        rcol_contents = [urwid.Text("I BROKE SOMETHING")]
        rcol_pile = urwid.Pile(rcol_contents)
        rcol = frames.RoundedLineBox(rcol_pile, "Output")

        cols = urwid.Columns([lcol, rcol], dividechars=1)
        
        self.progressbar = urwid.ProgressBar(normal='prog-normal', complete='prog-fill')
        self.progressbar.set_completion(60)

        layout = urwid.Pile([frames.RoundedLineBox(self.progressbar, ''), cols])

        self.root = frames.DoubleLineBox(layout, "Deployment Progress")

    def render(self):
        return self.root

    def update_progress_bar(self, delta):
        self.progressbar.set_completion(self.progressbar.current + delta)
