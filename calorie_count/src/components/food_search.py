"""This Module holds a class FoodAddDialog
- The dialog/pop-up of our calorie App that asks the user to input a new food."""

from __future__ import annotations

from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivymd.uix.button import MDFloatingActionButton
from kivymd.uix.list import IconLeftWidget, ThreeLineAvatarListItem

from calorie_count.src.components.food_add_dialog import FoodAddDialog
from calorie_count.src.consts import ARIAL
from calorie_count.src.DB.external.client import ExternalFoodsDB, FoodData
from calorie_count.src.utils.kivy_components import RTLMDTextField

KV = """
<FoodSearchScreen>:
    name: 'food_search_screen'
    MDBoxLayout:
        orientation: "vertical"
        MDIconButton:
            id: return_button
            text: "Back"
            icon: 'chevron-left'
            on_press: 
                app.root.ids.screen_manager.transition.direction = 'right'
                app.root.ids.screen_manager.current = "default"
                
        MDBoxLayout:
            id: search_bar_layout
            size_hint: 1, .1
            padding: dp(30)
        ScrollView:
            MDList:
                id: result_list

"""
Builder.load_string(KV)


class FoodSearchScreen(Screen):
    """A dialog/pop-up asking the user to search for a new Food."""

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.search_input_field = RTLMDTextField(
            hint_text="Enter name of the food to Search",
            pos_hint={"center_y": 0.9},
            mode="rectangle",
            font_name=str(ARIAL),
        )
        Clock.schedule_once(self._post_build_)

    def _post_build_(self, *a, **k):
        # Search Bar
        search_button = MDFloatingActionButton(
            icon="magnify",
            text="Search",
            pos_hint={"center_y": 0.9},
            on_press=self.run_search,
            theme_text_color="Primary",
        )
        self.ids.search_bar_layout.add_widget(self.search_input_field)
        self.ids.search_bar_layout.add_widget(search_button)

    def run_search(self, *args):
        """Search for the desired food"""

        def _icon_from_food(f: FoodData) -> str:
            """Helper function for finding the correct icon"""
            p, f, c = f.protein, f.fats, f.carbs
            if p > f and p > c:
                return "food-steak"
            if f > p and f > c:
                return "fish"
            if c > p and c > f:
                return "noodles"
            return "food"

        to_search = self.search_input_field.text
        if not to_search:
            return
        self.ids.result_list.clear_widgets()
        with ExternalFoodsDB() as ef_db:
            for food in ef_db.get_similar_food_by_name(to_search):
                title, *desc = food.description.split(",")
                if desc:
                    title = f"{desc.pop(0)} - {title}"
                tertiary = (
                    f"Protein: {food.protein}, "
                    f"Fat: {food.fats}, "
                    f"Carbs: {food.carbs}\n"
                    f" Sodium: {food.sodium},"
                    f" Sugar: {food.sugar}, "
                    f"Water: {food.water}"
                )
                list_item = ThreeLineAvatarListItem(
                    text=title, secondary_text=",".join(desc), tertiary_text=tertiary
                )
                list_item.add_widget(IconLeftWidget(icon=_icon_from_food(food)))
                list_item.bind(on_press=lambda *a, f=food, **k: self.add_food(f))
                self.ids.result_list.add_widget(list_item)

    def add_food(self, food: FoodData):
        dialog = FoodAddDialog(self.app)
        title, *desc = food.description.split(",")
        dialog.food_name.text = str(title)
        dialog.protein.text = str(food.protein)
        dialog.fats.text = str(food.fats)
        dialog.carbs.text = str(food.carbs)
        dialog.salt.text = str(food.sodium)
        dialog.sugar.text = str(food.sugar)
        dialog.water.text = str(food.water)
        dialog.open()
