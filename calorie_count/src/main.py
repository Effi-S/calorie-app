"""This module holds:
1. Initialization of our Calorie App.
2. Events referenced by .kv files."""

from __future__ import annotations

import os
from datetime import datetime as dt
from datetime import timedelta

# from calorie_count.src.consts import ARIAL

try:
    pass
except (Exception,):
    os.environ["KIVY_GL_BACKEND"] = "angle_sdl2"  # (debug w/ Windows + GPU)
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.datatables import MDDataTable
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogHeadlineText,
    MDDialogSupportingText,
)
from kivymd.uix.filemanager import MDFileManager
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.navigationbar import MDNavigationItem
from kivymd.uix.pickers.datepicker import MDModalDatePicker

from calorie_count.lib.theme.picker import MDThemePicker
from calorie_count.src.components.daily_screen import DailyScreen
from calorie_count.src.components.food_add_dialog import FoodAddDialog
from calorie_count.src.components.food_search import FoodSearchScreen
from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.DB.meal_entry_db import MealEntry, MealEntryDB
from calorie_count.src.utils import config, consts, xlsx
from calorie_count.src.utils.kivy_components import get_label, set_label, toast
from calorie_count.src.utils.plotting import fig2img, plot_graph, plot_pie_chart
from calorie_count.src.utils.utils import sort_by_similarity


def _dialog_button(text: str, on_release, icon: str | None = None, style: str = "text") -> MDButton:
    """Build an MDButton for use inside an MDDialogButtonContainer."""
    btn = MDButton(MDButtonText(text=text), style=style, on_release=on_release)
    if icon:
        btn.add_widget(MDButtonIcon(icon=icon))
    return btn


class NavItem(MDNavigationItem):
    """Bottom-navigation item that remembers which tab-screen it selects."""

    screen = StringProperty("")


class CaloriesApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.add_food_dialog = None
        self.food_table = None
        self._drop_down = None

    def build(self):
        # Apply persisted theme (KivyMD 2.0: theme_style + primary_palette only)
        theme_style, primary_palette = config.get_theme()
        self.theme_cls.theme_style = theme_style
        self.theme_cls.primary_palette = primary_palette

        Clock.schedule_once(self._post_build_)

        from kivy.core.window import Window

        Window.size = (500, 700)
        # Paint the window with the theme background so screens aren't black
        # (plain Screens don't fill a background in KivyMD 2.0); keep it in sync
        # when the user changes the theme.
        Window.clearcolor = self.theme_cls.backgroundColor
        self.theme_cls.bind(
            backgroundColor=lambda _inst, color: setattr(Window, "clearcolor", color)
        )
        return Builder.load_file(consts.MAIN_KV)

    def _post_build_(self, *a, **k):
        self.on_my_foods_screen_pressed()  # loading table
        self._switch_tab()  # setting default tab
        self.food_search_screen = FoodSearchScreen(self)
        self.root.ids.screen_manager.add_widget(self.food_search_screen)

        # setting entry date to today
        set_label(
            self.root.ids.entry_add_screen.ids.date_input,
            f"Date:\n{dt.now().date().isoformat()}",
        )

    def _switch_tab(self, name: str = "add_entry"):
        """Helper for switching the current tab (inner ScreenManager + nav bar)."""
        self.root.ids.tab_manager.current = name
        for item in self.root.ids.bottom_navigation.children:
            item.active = getattr(item, "screen", None) == name

    def on_switch_tabs(self, *args):
        """Called by MDNavigationBar when the active tab changes.

        The kv ``on_switch_tabs`` event dispatches the bar instance plus
        ``(item, item_icon, item_text)``, so accept ``*args`` and pick out the
        navigation item (the one carrying a ``screen``) rather than relying on a
        fixed arity.
        """
        item = next((a for a in args if hasattr(a, "screen")), None)
        name = getattr(item, "screen", "")
        if not name:
            return
        self.root.ids.tab_manager.current = name
        if name == "my_foods":
            self.on_my_foods_screen_pressed()
        elif name == "daily_screen":
            self.on_daily_screen_pressed()
        elif name == "trends_screen":
            self.on_trends_pressed()

    def on_choose_entry_date_pressed(self):
        """Set a custom date for the entry"""
        self.show_date_picker(
            button=self.root.ids.entry_add_screen.ids.date_input, is_limited=False
        )

    def on_daily_screen_pressed(self, *args):
        """Init Daily screen"""
        daily_screen: DailyScreen = self.root.ids.daily_screen
        daily_screen.update()

    def on_my_foods_screen_pressed(self, *args):
        with FoodDB() as fdb:
            foods = fdb.get_all_foods()

        table_layout = self.root.ids.foods_screen.ids.my_foods_layout
        table_layout.clear_widgets()
        self.food_table = MDDataTable(
            column_data=[(col, dp(30)) for col in Food.columns()],
            row_data=[m.values for m in foods],
            # font_name=str(ARIAL),
            check=True,
            use_pagination=True,
        )
        if not foods:
            toast("No Foods Yet")

        table_layout.add_widget(self.food_table)

    def on_add_food_pressed(self, *args):
        if not self.add_food_dialog:
            self.add_food_dialog = FoodAddDialog(self)
        self.add_food_dialog.open()

    def on_trends_pressed(self, *args, _once=[]):  # Mutable default parameter on purpose
        """Event when entering the "Trends" screen"""
        if not _once:
            # Setting the Dates in trends between today and 7 days ago
            today = dt.now().date().isoformat()
            a_week_ago = dt.now().date() - timedelta(days=7)
            start = self.root.ids.trends_screen.ids.trend_start_date_button
            end = self.root.ids.trends_screen.ids.trend_end_date_button
            set_label(start, f"{get_label(start)}\n{a_week_ago}")
            set_label(end, f"{get_label(end)}\n{today}")
            _once.append(1)
        self.generate_trend()

    def _dismiss_drop_down(self, *args):
        """Safely dismiss dropdown"""
        if self._drop_down:
            self._drop_down.dismiss()
            self._drop_down = None

    def on_name_entered_in_add_entry_screen(self, c: str, *args):
        """c is the additional character entered by the user"""

        def _callback(txt: str) -> None:
            self.root.ids.entry_add_screen.ids.meal_name_input.text = txt
            with FoodDB() as db:
                self.root.ids.entry_add_screen.ids.grams_input.text = str(
                    db.get_food_by_name(txt).portion
                )
            self._dismiss_drop_down()  # close the menu once a name is chosen

        text_field = self.root.ids.entry_add_screen.ids.meal_name_input
        target = text_field.text + c

        # -- Create Dropdown Items from similar names in DB to our target
        with FoodDB() as mdb:
            names = sort_by_similarity(mdb.get_all_food_names(), target)[:5]
        if not names:
            return c

        items = [
            {
                "viewclass": "MDDropdownTextItem",
                "text": name,
                "on_release": lambda txt=name: _callback(txt),
            }
            for name in names
        ]

        # -- Update Dropdown if exists and Only appending needed
        if self._drop_down:
            current_names = {x.get("text") for x in self._drop_down.items}
            print(current_names, names, current_names.issubset(set(names)))
            if current_names.issubset(set(names)):
                self._drop_down.items = items
                return c

        # -- Re-create dop-down
        self._dismiss_drop_down()
        self._drop_down = MDDropdownMenu(caller=text_field, items=items, width_mult=4)
        self._drop_down.bind(on_dismiss=self._dismiss_drop_down)
        self._drop_down.open()
        return c

    def on_submit_meal_entry(self, *args):
        name = self.root.ids.entry_add_screen.ids.meal_name_input.text
        portion = self.root.ids.entry_add_screen.ids.grams_input.text
        entry_date = get_label(self.root.ids.entry_add_screen.ids.date_input).splitlines()[-1]
        dialog = None
        with FoodDB() as mdb:
            names = mdb.get_all_food_names()
        if name not in names:

            def open_plus_dialog(*_):
                dialog.dismiss()
                d = FoodAddDialog(self)
                d.food_name.text = name
                d.headline.text = f'"{name}" not in Foods, Please add it below:'
                d.open()

            def start_search(*_):
                dialog.dismiss()
                self.on_search_food_pressed(query=name)

            dialog = MDDialog(
                MDDialogHeadlineText(text=f'"{name}" not in Foods'),
                MDDialogSupportingText(text="Try One of the options below:"),
                MDDialogButtonContainer(
                    Widget(),
                    _dialog_button("Search", start_search, icon="magnify"),
                    _dialog_button("Add new", open_plus_dialog, icon="plus"),
                ),
            )
            dialog.open()
        else:
            with MealEntryDB() as me_db:
                me = MealEntry(name=name, portion=float(portion or 0), date=entry_date)
                me_db.add_meal_entry(me)
                toast(f"Added Meal entry!\n({me}")

    def on_delete_foods_pressed(self, *args):
        names = [x[0] for x in self.food_table.get_row_checks()]

        def remove(*a, **k):
            with FoodDB() as mdb:
                mdb.remove(names)
                dialog.dismiss()
                self.on_my_foods_screen_pressed()
                toast(f"Removed {len(names)} Food/s")

        dialog = MDDialog(
            MDDialogSupportingText(text=f"Are you sure you want to delete {len(names)} rows?"),
            MDDialogButtonContainer(
                Widget(),
                _dialog_button("CANCEL", lambda *a: dialog.dismiss()),
                _dialog_button("DELETE", remove),
            ),
        )
        dialog.open()

    @staticmethod
    def show_date_picker(button, is_limited: bool = True, *args, **kwargs):
        """Helper function for binding a button with a date it displays.
        Preferably the text of the button should be set to "Date:" in .kv file."""

        def got_date(instance, *a, **k):
            dates = instance.get_date()
            if dates:
                set_label(button, get_label(button).splitlines()[0] + "\n" + dates[0].isoformat())
            instance.dismiss()

        if is_limited:
            with MealEntryDB() as me_db:
                first, last = me_db.get_first_last_dates()
            if first == last:
                first -= timedelta(days=1)
            picker = MDModalDatePicker(min_date=first, max_date=last)
        else:
            picker = MDModalDatePicker()

        # MDModalDatePicker's OK/Cancel only fire events; they don't close the
        # dialog, so dismiss it ourselves.
        picker.bind(on_ok=got_date, on_cancel=lambda inst, *a: inst.dismiss())
        picker.open()

    def set_trends_date_range(self, days_back: int):
        """Callback for binding event to setting trends date range."""
        end_date = dt.now().date()
        start_date = end_date - timedelta(days=days_back)
        start_button = self.root.ids.trends_screen.ids.trend_start_date_button
        end_button = self.root.ids.trends_screen.ids.trend_end_date_button
        set_label(
            start_button,
            "\n".join((get_label(start_button).splitlines()[0], start_date.isoformat())),
        )
        set_label(
            end_button, "\n".join((get_label(end_button).splitlines()[0], end_date.isoformat()))
        )

    def generate_trend(self, *args, **kwargs):
        # -- Getting The relevant entries
        start_date = get_label(
            self.root.ids.trends_screen.ids.trend_start_date_button
        ).splitlines()[-1]
        end_date = get_label(self.root.ids.trends_screen.ids.trend_end_date_button).splitlines()[-1]

        with MealEntryDB() as me_db:
            entries = me_db.get_entries_between_dates(str(start_date), str(end_date))

        trends_layout = self.root.ids.trends_screen.ids.trends_layout
        trends_layout.clear_widgets()
        # -- Adding Graph of calorie sum
        data = dict.fromkeys((e.date for e in entries), 0)
        for e in entries:
            data[e.date] += e.food.cals

        graph_fig = plot_graph(data, y_label="Calories")
        graph = fig2img(graph_fig)
        trends_layout.add_widget(graph)

        # -- Adding Graph of sodium
        data = dict.fromkeys((e.date for e in entries), 0)
        for e in entries:
            data[e.date] += e.food.sodium
        graph_fig = plot_graph(data, y_label="Sodium")
        graph = fig2img(graph_fig)
        trends_layout.add_widget(graph)

        # -- Adding Pie Chart
        data = {
            "Protein": sum(e.food.proteins for e in entries),
            "Carbs": sum(e.food.carbs for e in entries),
            "Fats": sum(e.food.fats for e in entries),
        }
        pie_chart_fig = plot_pie_chart(data)
        pie_chart = fig2img(pie_chart_fig)
        trends_layout.add_widget(pie_chart)

    def on_search_food_pressed(self, *_, query: str = "", **kwargs):
        """Search for a food button pressed."""
        self.root.ids.screen_manager.transition.direction = "left"
        self.root.ids.screen_manager.current = "food_search_screen"
        if query:
            self.food_search_screen.search_input_field.text = query

    def show_theme_picker(self, *args, **kwargs):

        def _set_theme(*a, **k):
            config.set_theme(self.theme_cls.theme_style, self.theme_cls.primary_palette)

        theme_dialog = MDThemePicker()
        theme_dialog.bind(on_dismiss=_set_theme)
        theme_dialog.open()

    def open_xlsx_dropdown(self, *args, **kwargs):
        def save_to_xlsx():  # option 1 - Save
            def _on_selected(fl, *a):  # file selected  => Are you sure Dialog
                def _save(*a_, **k):  # User chooses to save selected file
                    xlsx.save_to_excel(target)
                    toast(f"Saved: {target}")
                    dialog.dismiss()

                target = f"{fl}/Calorie_Counting_{dt.now():%F}.xlsx"
                dialog = MDDialog(
                    MDDialogSupportingText(text=f"Are you sure you want to Save:\n{target}?"),
                    MDDialogButtonContainer(
                        Widget(),
                        _dialog_button("CANCEL", lambda *a_: dialog.dismiss()),
                        _dialog_button("SAVE", _save),
                    ),
                    on_dismiss=lambda *a_: file_manager.close(),
                )
                dialog.open()

            file_manager = MDFileManager(search="dirs", select_path=_on_selected)
            file_manager.show(os.path.expanduser("~"))

        def import_xlsx():  # option 2 - Save
            def _on_selected(fl):  # file selected  => Are you sure Dialog
                def _load(*a_, **k_):  # User finally chose
                    print("Loading:", fl)
                    xlsx.import_excel(fl)

                dialog = MDDialog(
                    MDDialogSupportingText(text=f"Are you sure you want to Load:\n{fl}?"),
                    MDDialogButtonContainer(
                        Widget(),
                        _dialog_button("CANCEL", lambda *a_: dialog.dismiss()),
                        _dialog_button("LOAD", _load),
                    ),
                    on_dismiss=lambda *a_: file_manager.close(),
                )
                dialog.open()
                print(fl)
                file_manager.close()

            file_manager = MDFileManager(
                ext=[
                    ".xlsx",
                ],
                select_path=_on_selected,  # function called when selecting a file/directory
            )
            file_manager.show(os.path.expanduser("~"))

        self._dismiss_drop_down()
        self._drop_down = MDDropdownMenu(
            items=[
                {
                    "viewclass": "MDDropdownLeadingIconItem",
                    "text": "Save",
                    "leading_icon": "attachment",
                    "on_release": save_to_xlsx,
                },
                {
                    "viewclass": "MDDropdownLeadingIconItem",
                    "text": "Import existing",
                    "leading_icon": "attachment",
                    "on_release": import_xlsx,
                },
            ],
            position="center",
            caller=self.root.ids.top_app_bar,
        )
        self._drop_down.open()


def main():
    CaloriesApp().run()


if __name__ == "__main__":
    main()
