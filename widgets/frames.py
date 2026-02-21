import urwid

import util

class DoubleLineBox(urwid.LineBox):
    def __init__(self, original_widget, title=""):
        super().__init__(
                original_widget,
                title = title,
                tlcorner = util.CORNER_DOUBLE_TOP_LEFT,
                tline    = util.LINE_DOUBLE_HORIZONTAL,
                trcorner = util.CORNER_DOUBLE_TOP_RIGHT,
                blcorner = util.CORNER_DOUBLE_BOTTOM_LEFT,
                bline    = util.LINE_DOUBLE_HORIZONTAL,
                brcorner = util.CORNER_DOUBLE_BOTTOM_RIGHT,
                lline    = util.LINE_DOUBLE_VERTICAL,
                rline    = util.LINE_DOUBLE_VERTICAL
        )

class RoundedLineBox(urwid.LineBox):
    def __init__(self, original_widget, title=""):
        super().__init__(
                original_widget,
                title = title,
                tlcorner = util.CORNER_ROUND_TOP_LEFT,
                tline    = util.LINE_SINGLE_HORIZONTAL,
                trcorner = util.CORNER_ROUND_TOP_RIGHT,
                blcorner = util.CORNER_ROUND_BOTTOM_LEFT,
                bline    = util.LINE_SINGLE_HORIZONTAL,
                brcorner = util.CORNER_ROUND_BOTTOM_RIGHT,
                lline    = util.LINE_SINGLE_VERTICAL,
                rline    = util.LINE_SINGLE_VERTICAL
        )
