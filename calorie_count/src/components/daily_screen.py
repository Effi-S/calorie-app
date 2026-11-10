import re
from datetime import date, timedelta
from datetime import datetime as dt

from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivymd.uix.list import (
    MDList,
    MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTrailingIcon,
)

from calorie_count.src.DB.meal_entry_db import MealEntry, MealEntryDB
from calorie_count.src.utils.kivy_components import toast


class ListEntry(MDListItem):
    """A meal-entry list item: tap once to reveal a delete icon, tap again to delete."""

    def __init__(
        self,
        entry_list: MDList,
        entry: MealEntry,
        text: str = "",
        secondary_text: str = "",
        **kwargs,
    ):
        self.entry_list = entry_list
        self.entry_id = entry.id
        self.entry_name = text
        self.delete_icon = MDListItemTrailingIcon(icon="delete")
        self.is_icon_hidden = True
        super().__init__(on_release=self.on_item_press, **kwargs)
        self.add_widget(MDListItemHeadlineText(text=text))
        if secondary_text:
            self.add_widget(MDListItemSupportingText(text=secondary_text))

    def on_item_press(self, *_a, **_k):
        """Reveal the delete icon on first press; delete on the second."""
        if self.is_icon_hidden:
            self.add_widget(self.delete_icon)
            self.is_icon_hidden = False
            Clock.schedule_once(self._hide_icon, 5)
        else:
            self._delete()

    def _hide_icon(self, *_a, **_k):
        """Return the item back to its normal (icon-hidden) state."""
        if not self.is_icon_hidden and self.delete_icon.parent:
            self.remove_widget(self.delete_icon)
            self.is_icon_hidden = True

    def _delete(self, *_a, **_k):
        """Remove this entry from the list and the database."""
        self.entry_list.remove_widget(self)
        with MealEntryDB() as db:
            db.delete_entry(self.entry_id)
        toast(f"{self.entry_name} Removed")


class DailyScreen(ScrollView):
    def update(self, day: date = dt.now().date()):
        """Given the App (as reference), clears and re-loads the Daily screen.
        Loads the Entries based on the date given. Default date is today"""

        # -- Set label
        today, one_day = dt.now().date(), timedelta(days=1)
        day_lbl = (
            "Today" if day == today else "Yesterday" if day == today - one_day else day.isoformat()
        )
        self.ids.total_cals_header_label.text = f"Total Calories {day_lbl}"

        # -- Set Sum
        with MealEntryDB() as me_db:
            entries = me_db.get_entries_between_dates(day.isoformat(), day.isoformat())

        cals = sum(e.food.cals for e in entries)
        self.ids.total_cals_label.text = f"{cals: .2f}"

        # -- Create List of Entries
        entry_list: MDList = self.ids.daily_entries_list
        entry_list.clear_widgets()
        for i, entry in enumerate(entries, 1):
            text = entry.food.name or f"Meal {i} (Unnamed)"
            entry_list.add_widget(
                ListEntry(
                    entry_list,
                    entry,
                    text=text,
                    secondary_text=f"Calories: {entry.food.cals: .2f}",
                )
            )

    def get_day(self) -> date:  # type: ignore
        """Get a date object parsed from the label displayed in Daily screen"""
        text = self.ids.total_cals_header_label.text
        if "today" in text.lower():
            return dt.now().date()
        elif "yesterday" in text.lower():
            return (dt.now() - timedelta(days=1)).date()
        for day in re.findall(r"\d+-\d+-\d+", text):
            return dt.fromisoformat(day).date()
        toast("Error Getting day")

    def on_prev_daily_pressed(self, *args):
        """Previous day in Daily tab"""
        day = self.get_day() - timedelta(days=1)
        self.update(day)

    def on_next_daily_pressed(self, *args):
        """Next day in Daily tab"""
        day = self.get_day() + timedelta(days=1)
        if day > dt.now().date():
            return
        self.update(day)
