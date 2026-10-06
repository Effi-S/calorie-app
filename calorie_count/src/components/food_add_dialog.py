"""This Module holds a class FoodAddDialog
- The dialog/pop-up of our calorie App that asks the user to input a new food."""

from __future__ import annotations

from kivy.uix.widget import Widget
from kivymd.uix.button import MDButton, MDButtonIcon, MDButtonText
from kivymd.uix.dialog import (
    MDDialog,
    MDDialogButtonContainer,
    MDDialogContentContainer,
    MDDialogHeadlineText,
)
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.textfield import MDTextField

from calorie_count.src.consts import ARIAL
from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.utils.kivy_components import RTLMDTextField, make_text_field, toast


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

    last_submission: Food | None = None  # Here we can store the last Food submission

    def __init__(self, app, back_dialog=None, allow_nameless: bool = False, **kwargs):
        self.allow_nameless = allow_nameless
        self.root_window = app.root_window

        # Headline (exposed so callers can customise the title text).
        self.headline = MDDialogHeadlineText(text="Add A new Food")

        # dialog buttons
        self.submit_button = MDButton(
            MDButtonIcon(icon="basket-plus"),
            MDButtonText(text="Submit Food"),
            style="filled",
            on_release=self.on_submit_food_button_pressed,
        )
        self.clear_button = MDButton(
            MDButtonIcon(icon="undo"),
            MDButtonText(text="Clear selection"),
            style="tonal",
            on_release=self.on_clear_food_button_pressed,
        )

        # food name
        self.food_name = make_text_field(
            RTLMDTextField(font_name=str(ARIAL)),
            hint="Enter name of the Food",
            icon="food-variant",
        )

        # food portion (kept for the clear-selection handler; not shown directly)
        self.food_portion = make_text_field(
            MDTextField(), hint="Enter Portion (g) of the Food", icon="scale"
        )

        inner_content = MDGridLayout(cols=2, adaptive_height=True)
        self.protein = make_text_field(FloatMDTextField(), hint="Proteins (g)", icon="food-steak")
        self.fats = make_text_field(FloatMDTextField(), hint="Fats (g)", icon="fish")
        self.carbs = make_text_field(FloatMDTextField(), hint="Carbs (g)", icon="pasta")
        self.water = make_text_field(
            FloatMDTextField(text="0"), hint="Water (g)", icon="water-outline"
        )
        self.sugar = make_text_field(
            FloatMDTextField(text="0"), hint="Sugar (g)", icon="food-apple-outline"
        )
        self.salt = make_text_field(FloatMDTextField(), hint="Salt (mg)", icon="shaker-outline")
        for x in (
            self.protein,
            self.fats,
            self.carbs,
            self.water,
            self.sugar,
            self.salt,
        ):
            inner_content.add_widget(x)

        self.bind(on_dismiss=app.on_my_foods_screen_pressed)
        # building the dialog (KivyMD 2.0 composition API)
        super().__init__(
            self.headline,
            MDDialogContentContainer(
                self.food_name,
                inner_content,
                orientation="vertical",
            ),
            MDDialogButtonContainer(
                Widget(),
                self.clear_button,
                self.submit_button,
            ),
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
