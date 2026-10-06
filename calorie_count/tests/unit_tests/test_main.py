"""Regression tests for app-level wiring in main.py.

Importing ``calorie_count.src.main`` pulls in kivy/kivymd, which can hard-crash
the interpreter on a truly headless machine (no display at all, e.g. CI) -- a
crash that a ``try/except`` around the import cannot catch and that would abort
pytest collection. So these are display-gated and import kivy lazily inside the
tests (same approach as test_gui.py / test_plotting.py); they run locally and
under WSLg, and skip in headless CI.
"""

import os
import types
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("KIVY_NO_ARGS", "1")

HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) or (
    os.name == "nt"
)


@unittest.skipUnless(HAS_DISPLAY, "requires a display (imports kivy/kivymd)")
class TestOnSwitchTabs(unittest.TestCase):
    """Regression: MDNavigationBar's ``on_switch_tabs`` dispatches the bar
    instance plus (item, icon, text) -- 4 positional args. The handler must
    accept that arity (previously it declared only 3 and raised TypeError)."""

    def _app(self):
        from calorie_count.src.main import CaloriesApp

        app = CaloriesApp()
        app.root = MagicMock()
        return app

    def test_accepts_kv_dispatch_arity_and_switches_tab(self):
        app = self._app()
        item = types.SimpleNamespace(screen="add_entry")  # no per-tab handler branch
        # kv binding is `on_switch_tabs: app.on_switch_tabs(*args)` where args is
        # (bar, item, item_icon, item_text).
        app.on_switch_tabs(object(), item, "calendar-plus", "Add Entry")
        self.assertEqual(app.root.ids.tab_manager.current, "add_entry")

    def test_finds_nav_item_regardless_of_arg_order(self):
        app = self._app()
        item = types.SimpleNamespace(screen="add_entry")
        app.on_switch_tabs(item, "icon", "text")  # 3-arg form also works
        self.assertEqual(app.root.ids.tab_manager.current, "add_entry")

    def test_no_screen_item_is_a_noop(self):
        app = self._app()
        tab_manager = types.SimpleNamespace(current="UNSET")
        app.root.ids.tab_manager = tab_manager
        # No argument carries a `screen`; must not raise and must not switch.
        app.on_switch_tabs("bar", "icon", "text")
        self.assertEqual(tab_manager.current, "UNSET")


@unittest.skipUnless(HAS_DISPLAY, "requires a display (imports kivy/kivymd)")
class TestButtonLabelHelpers(unittest.TestCase):
    """Regression: KivyMD 2.0 buttons hold their label in an MDButtonText child
    (``_button_text``), not a ``text`` property. The get/set helpers must read
    and write that child so date/trend buttons keep working."""

    def test_get_and_set_label(self):
        from calorie_count.src.utils.kivy_components import get_label, set_label

        button = types.SimpleNamespace(_button_text=types.SimpleNamespace(text="Start"))
        self.assertEqual(get_label(button), "Start")
        set_label(button, "Start\n2026-01-01")
        self.assertEqual(button._button_text.text, "Start\n2026-01-01")

    def test_missing_label_child_is_safe(self):
        from calorie_count.src.utils.kivy_components import get_label, set_label

        button = types.SimpleNamespace(_button_text=None)
        self.assertEqual(get_label(button), "")
        set_label(button, "x")  # must not raise


if __name__ == "__main__":
    unittest.main()
