"""GUI regression tests for the KivyMD 2.0 migration.

These need a real display + GL context (KivyMD 2.0 can only instantiate widgets
while an MDApp is running, and its buttons/dialogs allocate framebuffers), so
they are skipped when no DISPLAY is available -- e.g. headless CI. They run
locally (including under WSLg) and guard against regressions reported after the
migration:

* button labels invisible (native MDButton labels must render with a texture);
* Light mode showing a black background (window must follow the theme);
* the date picker's OK/Cancel not closing the dialog;
* the theme picker degrading to plain buttons instead of color swatches.
"""

import os
import unittest

os.environ.setdefault("KIVY_NO_ARGS", "1")

HAS_DISPLAY = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")) or (
    os.name == "nt"
)


def _walk(widget):
    yield widget
    for child in widget.children:
        yield from _walk(child)


@unittest.skipUnless(HAS_DISPLAY, "requires a display + GL (GUI test)")
class TestMigrationGuiRegressions(unittest.TestCase):
    """Drive the real app once (a single ``run()`` avoids re-creating Kivy's
    Window singleton) and assert every reported regression."""

    def _collect(self):
        from kivy.clock import Clock
        from kivymd.uix.pickers.datepicker import MDModalDatePicker

        from calorie_count.lib.theme.picker import PALETTES, ColorSwatch, MDThemePicker
        from calorie_count.src.utils import config
        from calorie_count.src.utils.kivy_components import get_label, set_label

        config.set_db_path_test()  # isolated temp DB, auto-cleaned
        from calorie_count.src.DB.food_db import Food, FoodDB
        from calorie_count.src.DB.meal_entry_db import MealEntryDB
        from calorie_count.src.main import CaloriesApp

        with FoodDB() as fdb:  # a known food so meal-entry/autocomplete have data
            fdb.add_food(Food("apple", 100, 0.5, 0.2, 10, 4, 0, 86))

        results = {}

        class _App(CaloriesApp):
            def build(self):
                root = super().build()
                self.theme_cls.theme_style = "Light"
                self.theme_cls.primary_palette = "Blue"
                return root

            def on_start(self):
                Clock.schedule_once(self._phase1, 1.3)

            def _phase1(self, *_a):
                from kivy.core.window import Window

                try:
                    # #2 background follows the theme (not black) in Light mode
                    results["clearcolor"] = [round(c, 3) for c in Window.clearcolor]
                    results["bg"] = [round(c, 3) for c in self.theme_cls.backgroundColor]

                    # #1 native button label renders (has text + a texture)
                    button = self.root.ids.entry_add_screen.ids.add_meal_button
                    results["label_text"] = get_label(button)
                    results["label_texture_w"] = button._button_text.texture_size[0]

                    # theme picker shows one color swatch per palette
                    picker = MDThemePicker()
                    results["swatches"] = sum(isinstance(w, ColorSwatch) for w in _walk(picker))
                    results["expected_swatches"] = len(PALETTES)
                    picker.dismiss()

                    # Submitting a meal entry must read the date button's label
                    # (not a non-existent `.text`) and add the entry.
                    entry = self.root.ids.entry_add_screen.ids
                    entry.meal_name_input.text = "apple"
                    entry.grams_input.text = "100"
                    set_label(entry.date_input, "Date:\n2026-10-06")
                    self.on_submit_meal_entry()
                    with MealEntryDB() as mdb:
                        results["entries_added"] = len(
                            mdb.get_entries_between_dates("2026-10-06", "2026-10-06")
                        )

                    # Choosing an autocomplete suggestion must close the dropdown.
                    entry.meal_name_input.text = ""
                    self.on_name_entered_in_add_entry_screen("a")
                    results["dropdown_opened"] = self._drop_down is not None
                    if self._drop_down is not None:
                        self._drop_down.items[0]["on_release"]()  # pick first suggestion
                    results["dropdown_dismissed"] = self._drop_down is None

                    # #4 date picker closes on OK
                    self.show_date_picker(button=button, is_limited=False)
                    opened = [w for w in Window.children if isinstance(w, MDModalDatePicker)]
                    results["date_picker_opened"] = len(opened) == 1
                    if opened:
                        opened[0].dispatch("on_ok")
                    Clock.schedule_once(self._phase2, 1.5)  # wait for dismiss animation
                except Exception as exc:  # pragma: no cover
                    results["error"] = f"{type(exc).__name__}: {exc}"
                    self.stop()

            def _phase2(self, *_a):
                from kivy.core.window import Window

                results["date_picker_dismissed"] = not any(
                    isinstance(w, MDModalDatePicker) for w in Window.children
                )
                self.stop()

        _App().run()
        return results

    def test_migration_gui_regressions(self):
        r = self._collect()
        self.assertNotIn("error", r, r.get("error"))

        # #2 window background tracks the theme and is not black in Light mode.
        self.assertEqual(r.get("clearcolor"), r.get("bg"))
        self.assertNotEqual(r.get("clearcolor", [])[:3], [0.0, 0.0, 0.0])

        # #1 button label present and rendered (non-zero text texture width).
        self.assertEqual(r.get("label_text"), "Submit Meal Entry")
        self.assertGreater(r.get("label_texture_w", 0), 0)

        # Theme picker renders one color swatch per palette (not plain buttons).
        self.assertEqual(r.get("swatches"), r.get("expected_swatches"))

        # #4 date picker opened and then closed on OK.
        self.assertTrue(r.get("date_picker_opened"))
        self.assertTrue(r.get("date_picker_dismissed"))

        # Submitting a meal entry works (reads the date button's label).
        self.assertEqual(r.get("entries_added"), 1)

        # Autocomplete dropdown opens and closes once a suggestion is chosen.
        self.assertTrue(r.get("dropdown_opened"))
        self.assertTrue(r.get("dropdown_dismissed"))


if __name__ == "__main__":
    unittest.main()
