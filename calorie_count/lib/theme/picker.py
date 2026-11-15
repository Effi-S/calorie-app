"""A small theme picker dialog for KivyMD 2.0.

The original vendored picker depended on KivyMD 1.x internals that were removed in
2.0 (``color_definitions``, ``MDTabsBase``, the elevation-behavior mixins and
``accent_palette``/``accent_hue``). KivyMD 2.0 theming is driven by a single
``primary_palette`` seed color plus the ``theme_style`` (Light/Dark), so this
replacement shows a grid of colored swatches for the palette and sun/moon
buttons for the light/dark mode.
"""

from __future__ import annotations

from kivy.graphics import Color, Ellipse, Line
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.widget import Widget
from kivy.utils import get_color_from_hex, hex_colormap
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonText, MDIconButton
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
)
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel

# KivyMD 2.0 primary-palette seed colors are Kivy/CSS color names.
PALETTES = (
    "Red",
    "Pink",
    "Purple",
    "Indigo",
    "Blue",
    "Cyan",
    "Teal",
    "Green",
    "Lime",
    "Yellow",
    "Orange",
    "Brown",
)


class ColorSwatch(ButtonBehavior, Widget):
    """A circular, clickable color swatch for a single palette seed color."""

    def __init__(self, palette: str, on_pick, **kwargs):
        super().__init__(**kwargs)
        self.palette = palette
        self._on_pick = on_pick
        self.size_hint = (None, None)
        self.size = (dp(40), dp(40))
        rgba = get_color_from_hex(hex_colormap[palette.lower()])
        with self.canvas:
            Color(*rgba)
            self._circle = Ellipse(pos=self.pos, size=self.size)
            Color(0, 0, 0, 0.25)
            self._border = Line(circle=(self.center_x, self.center_y, dp(20)), width=1)
        self.bind(pos=self._redraw, size=self._redraw)

    def _redraw(self, *_args) -> None:
        self._circle.pos = self.pos
        self._circle.size = self.size
        self._border.circle = (self.center_x, self.center_y, self.width / 2)

    def on_release(self) -> None:
        self._on_pick(self.palette)


class MDThemePicker(MDDialog):
    """Dialog to choose the primary palette color and light/dark style."""

    def __init__(self, **kwargs):
        self._app = MDApp.get_running_app()

        swatches = MDGridLayout(
            cols=6, adaptive_height=True, spacing="8dp", pos_hint={"center_x": 0.5}
        )
        for name in PALETTES:
            swatches.add_widget(ColorSwatch(name, self._set_palette))

        mode_row = MDGridLayout(cols=2, adaptive_height=True, spacing="24dp", pos_hint={"center_x": 0.5})
        mode_row.add_widget(
            MDIconButton(icon="weather-sunny", on_release=lambda *_: self._set_style("Light"))
        )
        mode_row.add_widget(
            MDIconButton(icon="weather-night", on_release=lambda *_: self._set_style("Dark"))
        )

        super().__init__(
            MDDialogHeadlineText(text="Theme"),
            MDDialogContentContainer(
                MDLabel(text="Primary color", adaptive_height=True),
                swatches,
                MDLabel(text="Mode", adaptive_height=True),
                mode_row,
                orientation="vertical",
                spacing="12dp",
            ),
            MDDialogButtonContainer(
                Widget(),
                MDButton(MDButtonText(text="CLOSE"), style="text", on_release=self._close),
            ),
            **kwargs,
        )

    def _set_palette(self, name: str) -> None:
        self._app.theme_cls.primary_palette = name

    def _set_style(self, style: str) -> None:
        self._app.theme_cls.theme_style = style

    def _close(self, *_args) -> None:
        self.dismiss()
