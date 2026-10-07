"""Here we store custom Kivy components and small KivyMD-2.0 compatibility helpers."""

import re

from kivy.metrics import dp
from kivymd.uix.button import MDButton
from kivymd.uix.snackbar import MDSnackbar, MDSnackbarText
from kivymd.uix.textfield import MDTextField, MDTextFieldHintText, MDTextFieldTrailingIcon


def toast(text: str, duration: float = 2.0) -> None:
    """Drop-in replacement for the removed ``kivymd.toast.toast`` (Android-only in 2.0).

    Shows a short-lived snackbar at the bottom of the screen. If the GL context
    can't build the snackbar's framebuffer (some headless/software renderers,
    e.g. WSLg), it degrades to a console message instead of crashing the app.
    """
    text = str(text)
    try:
        MDSnackbar(
            MDSnackbarText(text=text),
            y=dp(24),
            pos_hint={"center_x": 0.5},
            size_hint_x=0.8,
            duration=duration,
        ).open()
    except Exception as exc:  # pragma: no cover - rendering/GL environment dependent
        print(f"[toast] {text}  ({type(exc).__name__}: {exc})")


def get_label(button: MDButton) -> str:
    """Return the text of an ``MDButton``'s ``MDButtonText`` child (or "").

    KivyMD 2.0 keeps a button's label in a child widget rather than a ``text``
    property; ``MDButton`` records it as ``_button_text``.
    """
    label = getattr(button, "_button_text", None)
    return label.text if label is not None else ""


def set_label(button: MDButton, text: str) -> None:
    """Set the text of an ``MDButton``'s ``MDButtonText`` child, if present."""
    label = getattr(button, "_button_text", None)
    if label is not None:
        label.text = text


def make_text_field(field: MDTextField, hint: str = "", icon: str = "") -> MDTextField:
    """Attach a hint and/or trailing icon to a text field via 2.0 child widgets.

    In KivyMD 2.0 ``hint_text=``/``icon_right=`` kwargs were replaced by
    ``MDTextFieldHintText`` / ``MDTextFieldTrailingIcon`` child widgets.
    """
    if hint:
        field.add_widget(MDTextFieldHintText(text=hint))
    if icon:
        field.add_widget(MDTextFieldTrailingIcon(icon=icon))
    return field


class RTLMDTextField(MDTextField):
    """TextField Input that allows rtl."""

    _reg = re.compile(r"[a-zA-Z]")

    def insert_text(self, s, from_undo=False):
        if s.isalpha() and not self._reg.findall(s):
            self.text = s + self.text
            return super().insert_text("", from_undo=from_undo)
        return super().insert_text(s, from_undo=from_undo)
