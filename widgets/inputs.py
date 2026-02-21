import urwid

import util

class CheckRadioBox(urwid.WidgetWrap):
    signals = ['post_change']

    def __init__(self, label, group=None, state=False):
        self.label = label
        self.state = state

        if group is not None:
            group.append(self)
        self.group = group

        self._icon = urwid.SelectableIcon("", 0)
        self._update_widget()

        super().__init__(urwid.AttrMap(self._icon, 'button-regular', 'button-highlight'))

    def _update_widget(self):
        if self.group is None:
            icon = util.CHK_CHECKED if self.state else util.CHK_UNCHECKED
        else:
            icon = util.RADIO_SELECTED if self.state else util.RADIO_UNSELECTED
        self._icon.set_text(f'{icon} {self.label}')

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key in (' ', 'enter'):
            self.toggle()
            return None
        return key

    def mouse_event(self, size, event, button, col, row, focus):
        if event == 'mouse press' and button == 1:
            self.toggle()
            return True
        return False

    def toggle(self):
        if self.group is not None:
            if self.state: return # Do nothing.
            for button in self.group:
                button.state = False
                button._update_widget()

        self.state = not self.state
        self._update_widget()
        urwid.emit_signal(self, 'post_change', self, self.state)

    def get_state(self):
        return self.state

class Togglegroup(urwid.WidgetWrap):
    def __init__(self, labels, is_checkboxes=False):
        self.widgets = []
        self.group = [] if not is_checkboxes else None

        for label in labels:
            if isinstance(label, str):
                w = CheckRadioBox(label, group=self.group)
                self.widgets.append(w)
                
            elif isinstance(label, tuple):
                if len(label) == 2:
                    w = CheckRadioBox(label[0], group=self.group, state=label[1])
                    self.widgets.append(w)

        self.pile = urwid.Pile(self.widgets)
        super().__init__(self.pile)

    def get_selected(self):
        i = 0
        if self.group is None:
            checked = []
            for button in self.widgets:
                if button.get_state() == True:
                    checked.append(i)
                i+=1
            return checked

        else:
            for button in self.widgets:
                if button.get_state() == True:
                    return i
                i+=1
        return None
