"""This Module holds a class FoodAddDialog
    - The dialog/pop-up of our calorie App that asks the user to input a new food."""

from __future__ import annotations

from typing import Optional

from kivymd.toast import toast
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFillRoundFlatIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField

from calorie_count.src.consts import ARIAL
from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.utils.kivy_components import RTLMDTextField


class FloatMDTextField(MDTextField):
    """TextField Input that only allows float input (0-9 or single dot)."""

    def insert_text(self, s, from_undo=False):
        if not s.isnumeric():
            if s != "." or "." in self.text:
                toast("Only numbers!")
                s = ""
        return super().insert_text(s, from_undo=from_undo)


class FoodAddDialog(MDDialog):
    """A dialog/pop-up asking the user to add a new Food."""

    last_submission: Optional[Food] = None  # Here we can store the last Food submission

    def __init__(self, app, back_dialog=None, allow_nameless: bool = False, **kwargs):

        self.allow_nameless = allow_nameless
        self.root_window = app.root_window

        # dialog buttons
        self.submit_button = MDFillRoundFlatIconButton(
            text="Submit Food",
            icon="basket-plus",
            on_press=self.on_submit_food_button_pressed,
        )
        self.clear_button = MDFillRoundFlatIconButton(
            text="Clear selection",
            icon="undo",
            on_press=self.on_clear_food_button_pressed,
        )
        # content
        self.content = MDBoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=self.root_window.height * 0.4,
        )

        # food name
        self.food_name = RTLMDTextField(
            hint_text="Enter name of the Food",
            font_name=str(ARIAL),
            icon_right="food-variant",
        )
        self.content.add_widget(self.food_name)

        # food portion
        self.food_portion = MDTextField(
            hint_text="Enter Portion (g) of the Food", icon_right="scale"
        )

        inner_content = MDGridLayout(cols=2)
        self.protein = FloatMDTextField(
            hint_text="Proteins (g)", icon_right="food-steak"
        )
        self.fats = FloatMDTextField(hint_text="Fats (g)", icon_right="fish")
        self.carbs = FloatMDTextField(hint_text="Carbs (g)", icon_right="pasta")
        self.water = FloatMDTextField(
            hint_text="Water (g)", icon_right="water-outline", text="0"
        )
        self.sugar = FloatMDTextField(
            hint_text="Sugar (g)", icon_right="food-apple-outline", text="0"
        )
        self.salt = FloatMDTextField(hint_text="Salt (mg)", icon_right="shaker-outline")
        for x in (
            self.protein,
            self.fats,
            self.carbs,
            self.water,
            self.sugar,
            self.salt,
        ):
            inner_content.add_widget(x)
        self.content.add_widget(inner_content)
        self.bind(on_dismiss=app.on_my_foods_screen_pressed)
        # building the dialog
        super().__init__(
            title="Add A new Food",
            type="custom",
            content_cls=self.content,
            buttons=[self.submit_button, self.clear_button],
            **kwargs,
        )

    def check_errors(self) -> list[str]:
        """Make sure input is ok before adding food to DB"""
        errors = []

        if not all((self.protein.text, self.fats.text, self.carbs)):
            errors.append("Must enter Protein Fats and Carbs!")

        if not self.allow_nameless and not self.food_name.text:
            errors.append("No Food Name was entered")

        if self.food_name.text:
            with FoodDB() as mdb:
                if self.food_name.text in mdb.get_all_food_names():
                    errors.append(f"Name: {self.food_name.text} already exists!")
        return errors

    def _sum_inputs(self) -> float:
        """Get the sum in grams of all of the text fields of the dialog that receive."""
        gram_inputs = (self.protein, self.fats, self.carbs, self.water)
        mg_inputs = (self.salt,)
        sum_grams = sum(float(x.text) for x in gram_inputs if x.text)
        sum_mg = sum(float(x.text) / 1000 for x in mg_inputs if x.text)
        return sum_grams + sum_mg

    def on_submit_food_button_pressed(self, *args):
        """When a 'Food' is submitted:
        1. Check for errors
        2. If no errors ad food to DB (otherwise toast)"""
        errors = self.check_errors()
        if errors:
            toast("\n".join(errors))
            return

        portion = float(self._sum_inputs())

        with FoodDB() as mdb:
            food = Food(
                name=self.food_name.text,
                portion=portion,
                proteins=float(self.protein.text),
                fats=float(self.fats.text),
                carbs=float(self.carbs.text),
                sugar=float(self.sugar.text or 0),
                sodium=float(self.salt.text or 0),
                water=float(self.water.text or 0),
            )
            mdb.add_food(food)
            self.last_submission = food
            toast(f"Food {food.name} added!")

    def on_clear_food_button_pressed(self, *args):
        """Clear all the selections."""
        for x in (
            self.food_name,
            self.food_portion,
            self.protein,
            self.fats,
            self.carbs,
            self.salt,
            self.sugar,
            self.water,
        ):
            x.text = ""
