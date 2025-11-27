import unittest
import os

from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.DB.meal_entry_db import MealEntryDB
from calorie_count.src.utils import config


class TestFoodDB(unittest.TestCase):

    def setUp(self):
        # Create a new instance of FoodDB for each test method
        self.test_db_path = config.set_db_path_test()
        self.db = FoodDB()
        with MealEntryDB():  # So table will exist as well
            pass
        super().setUp()

    def tearDown(self):
        """Clean up test database file."""
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except (OSError, PermissionError):
                pass  # Ignore if file is locked or already deleted
        super().tearDown()

    def test_remove(self):
        # Add food to the database
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))

            # Check that the food was added successfully
            self.assertIn('apple', self.db.get_all_food_names())

            # Remove the food from the database
            self.db.remove(['apple'])

            # Check that the food was removed successfully
            self.assertNotIn('apple', self.db.get_all_food_names())

    def test_add_food(self):
        # Create a new food
        food = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)

        # Add the food to the database
        with self.db:
            self.db.add_food(food)

            # Check that the food was added successfully
            self.assertIn('apple', self.db.get_all_food_names())

    def test_get_food_by_id(self):
        # Add a food to the database
        with self.db:
            food_to_add = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)
            self.db.add_food(food_to_add)

            # Get the food by id (Food.__post_init__ sets id = name if name exists)
            food = self.db.get_food_by_id(food_to_add.id)

            # Check that the returned food has the expected properties
            self.assertEqual(food.name, 'apple')
            self.assertEqual(food.portion, 100)
            self.assertEqual(food.proteins, 0.5)
            self.assertEqual(food.fats, 0.2)
            self.assertEqual(food.carbs, 10)
            self.assertEqual(food.sugar, 4)
            self.assertEqual(food.sodium, 0)
            self.assertEqual(food.water, 86)

    def test_get_food_by_name(self):
        # Add Food to the database
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))

            # Get the food by name
            food = self.db.get_food_by_name('apple')

            # Check that the returned food has the expected properties
            self.assertEqual(food.name, 'apple')
            self.assertEqual(food.portion, 100)
            self.assertEqual(food.proteins, 0.5)
            self.assertEqual(food.fats, 0.2)
            self.assertEqual(food.carbs, 10)
            self.assertEqual(food.sugar, 4)
            self.assertEqual(food.sodium, 0)
            self.assertEqual(food.water, 86)

    def test_add_food_update(self):
        """Test adding food with update flag."""
        with self.db:
            # Add initial food
            food1 = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)
            self.db.add_food(food1)
            
            # Update with new values
            food2 = Food('apple', 150, 1.0, 0.3, 15, 6, 1, 80)
            self.db.add_food(food2, update=True)
            
            # Verify update
            updated_food = self.db.get_food_by_name('apple')
            self.assertEqual(updated_food.portion, 150)
            self.assertEqual(updated_food.proteins, 1.0)

    def test_get_all_foods(self):
        """Test getting all foods from database."""
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.db.add_food(Food('banana', 100, 1.0, 0.3, 20, 15, 1, 75))
            
            all_foods = self.db.get_all_foods()
            self.assertEqual(len(all_foods), 2)
            food_names = [f.name for f in all_foods]
            self.assertIn('apple', food_names)
            self.assertIn('banana', food_names)

    def test_get_all_food_names(self):
        """Test getting all food names."""
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.db.add_food(Food('banana', 100, 1.0, 0.3, 20, 15, 1, 75))
            
            names = self.db.get_all_food_names()
            self.assertEqual(len(names), 2)
            self.assertIn('apple', names)
            self.assertIn('banana', names)

    def test_remove_multiple_foods(self):
        """Test removing multiple foods at once."""
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.db.add_food(Food('banana', 100, 1.0, 0.3, 20, 15, 1, 75))
            self.db.add_food(Food('orange', 100, 0.8, 0.2, 12, 9, 0, 87))
            
            self.db.remove(['apple', 'banana'])
            
            names = self.db.get_all_food_names()
            self.assertNotIn('apple', names)
            self.assertNotIn('banana', names)
            self.assertIn('orange', names)

    def test_remove_single_string(self):
        """Test removing food with string instead of list."""
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            
            self.db.remove('apple')
            
            self.assertNotIn('apple', self.db.get_all_food_names())

    def test_remove_empty_list(self):
        """Test removing with empty list does nothing."""
        with self.db:
            self.db.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            
            self.db.remove([])
            
            self.assertIn('apple', self.db.get_all_food_names())

    def test_food_calories_calculation(self):
        """Test Food calories property calculation."""
        food = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)
        # Calories = proteins*4 + carbs*4 + fats*9
        expected_cals = 0.5 * 4 + 10 * 4 + 0.2 * 9
        self.assertEqual(food.cals, expected_cals)

    def test_food_values_property(self):
        """Test Food values property."""
        food = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)
        values = food.values
        self.assertEqual(len(values), 9)  # All fields except id + calories
        self.assertEqual(values[-1], food.cals)  # Last value should be calories

    def test_food_columns(self):
        """Test Food columns static method."""
        columns = Food.columns()
        self.assertIsInstance(columns, tuple)
        self.assertIn('Name', columns)
        self.assertIn('Calories', columns)

    def test_get_food_by_id_with_session(self):
        """Test getting food by ID."""
        with self.db:
            food = Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86)
            self.db.add_food(food)
            
            retrieved = self.db.get_food_by_id(food.id)
            self.assertEqual(retrieved.name, 'apple')
            self.assertEqual(retrieved.id, food.id)


if __name__ == '__main__':
    unittest.main()
