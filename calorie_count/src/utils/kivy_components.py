"""Here we store custom Kivy components"""

import re

from kivymd.uix.textfield import MDTextField


class RTLMDTextField(MDTextField):
    """TextField Input that allows rtl."""

    _reg = re.compile(r"[a-zA-Z]")

    def insert_text(self, s, from_undo=False):
        if s.isalpha() and not self._reg.findall(s):
            self.text = s + self.text
            return super().insert_text("", from_undo=from_undo)
        return super().insert_text(s, from_undo=from_undo)
