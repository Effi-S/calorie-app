"""Here we test the MealEntryDB methods.

Please note that adding a test requires the patch for __enter__ for FoodDB to return our test db 'self.fdb'.
This is because of  "separation of concerns", MealEntry object calls FoodDB.__enter__ .
Though a bit hacky, This patch seems simpler than injecting the test FoodDB
to MealEntryDB who injects it to MealEntry Objects.

"""
import unittest
from unittest.mock import Mock, patch

from calorie_count.src.DB.food_db import Food, FoodDB
from calorie_count.src.DB.meal_entry_db import MealEntry, MealEntryDB
from calorie_count.src.utils import config


class TestFoodDB(unittest.TestCase):

    def setUp(self):
        # Create a new instance of FoodDB for each test method
        self.test_db_path = config.set_db_path_test()
        self.fdb = FoodDB()  # So table will exist as well
        # Initialize session for fdb
        with self.fdb:
            pass
        super().setUp()

    def tearDown(self) -> None:
        # Clean up session if it exists
        if hasattr(self.fdb, '_session') and self.fdb._session:
            self.fdb._session.close()
            self.fdb._session = None
        # Clean up test database file
        if hasattr(self, 'test_db_path') and os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except (OSError, PermissionError):
                pass  # Ignore if file is locked or already deleted

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_add_meal_entry(self, mock: Mock):
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        # Test adding a new meal entry
        entry = MealEntry(name="apple", date="2022-12-15", portion=100)
        print(entry)
        with MealEntryDB() as mdb:
            mdb.add_meal_entry(entry)

            # Check that the entry was added to the database
            ret = mdb.get_entries_between_dates("2022-12-14", "2022-12-16")
            self.assertEqual(len(ret), 1)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_delete_entry(self, mock: Mock):
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        # Test deleting a meal entry
        entry = MealEntry(name="apple", date="2022-12-15", portion=100)
        with MealEntryDB() as mdb:
            mdb.add_meal_entry(entry)
            self.assertEqual(len(mdb.get_entries_between_dates("2022-12-15", "2022-12-15")), 1)
            mdb.delete_entry(entry.id)
            # Check that the entry was deleted from the database
            self.assertEqual(len(mdb.get_entries_between_dates("2022-12-15", "2022-12-15")), 0)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_get_first_last_dates(self, mock: Mock):
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.fdb.add_food(Food('banana', 100, 0.5, 0.2, 10, 4, 0, 86))
        # Test getting the first and last dates in the database
        entry1 = MealEntry(name="apple", date="2022-12-14", portion=100)
        entry2 = MealEntry(name="banana", date="2022-12-16", portion=100)
        with MealEntryDB() as mdb:
            mdb.add_meal_entry(entry1)
            mdb.add_meal_entry(entry2)
            first_date, last_date = mdb.get_first_last_dates()
            # Check that the first and last dates in the database are as expected
            self.assertEqual(first_date.isoformat(), "2022-12-14")
            self.assertEqual(last_date.isoformat(), "2022-12-16")

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_get_entries_between_dates(self, mock: Mock):
        mock.return_value = self.fdb
        # Create a MealEntryDB instance and add some MealEntry objects to it
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.fdb.add_food(Food('banana', 100, 0.5, 0.2, 10, 4, 0, 86))
            self.fdb.add_food(Food('orange', 100, 0.5, 0.2, 10, 4, 0, 86))
        meal_entry1 = MealEntry(name='apple', date='2022-01-01')
        meal_entry2 = MealEntry(name='banana', date='2022-01-02')
        meal_entry3 = MealEntry(name='orange', date='2022-01-03')
        with MealEntryDB() as mdb:
            mdb.add_meal_entry(meal_entry1)
            mdb.add_meal_entry(meal_entry2)
            mdb.add_meal_entry(meal_entry3)
            # Verify expected list of MealEntry
            start_date = '2022-01-02'
            end_date = '2022-01-03'
            entries = mdb.get_entries_between_dates(start_date, end_date)
            self.assertEqual(len(entries), 2)
            # Check that we got the right entries
            entry_dates = [e.date for e in entries]
            self.assertIn('2022-01-02', entry_dates)
            self.assertIn('2022-01-03', entry_dates)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_get_first_last_dates_empty_db(self, mock: Mock):
        """Test getting first/last dates when database is empty."""
        mock.return_value = self.fdb
        with MealEntryDB() as mdb:
            first_date, last_date = mdb.get_first_last_dates()
            # Should return today's date for both
            from datetime import datetime as dt
            today = dt.now().date()
            self.assertEqual(first_date, today)
            self.assertEqual(last_date, today)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_with_custom_portion(self, mock: Mock):
        """Test MealEntry with custom portion ratio."""
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        
        # Create entry with 200g portion (2x the base portion)
        entry = MealEntry(name='apple', date='2022-12-15', portion=200)
        
        # Verify nutrients are scaled correctly
        self.assertEqual(entry.portion, 200)
        self.assertEqual(entry.food.proteins, 1.0)  # 0.5 * 2
        self.assertEqual(entry.food.carbs, 20.0)    # 10 * 2
        self.assertEqual(entry.food.fats, 0.4)      # 0.2 * 2

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_default_date(self, mock: Mock):
        """Test MealEntry uses today's date when not provided."""
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        
        entry = MealEntry(name='apple', portion=100)
        
        from datetime import datetime as dt
        expected_date = dt.now().date().isoformat()
        self.assertEqual(entry.date, expected_date)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_default_portion(self, mock: Mock):
        """Test MealEntry uses food's default portion when not provided."""
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        
        entry = MealEntry(name='apple', date='2022-12-15')
        
        self.assertEqual(entry.portion, 100)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_with_food_object(self, mock: Mock):
        """Test MealEntry initialization with Food object."""
        mock.return_value = self.fdb
        food = Food('new_food', 150, 1.0, 0.3, 15, 8, 2, 80)
        
        entry = MealEntry(food=food, date='2022-12-15')
        
        # self.assertEqual(entry.name, 'new_food')
        self.assertEqual(entry.food, food)
        # Food should be added to database
        with self.fdb:
            self.assertIn('new_food', self.fdb.get_all_food_names())

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_columns(self, mock: Mock):
        """Test MealEntry columns static method."""
        columns = MealEntry.columns()
        self.assertIsInstance(columns, tuple)
        self.assertIn('Date', columns)
        self.assertIn('Name', columns)
        self.assertIn('Calories', columns)

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_values(self, mock: Mock):
        """Test MealEntry values property."""
        mock.return_value = self.fdb
        with self.fdb:
            self.fdb.add_food(Food('apple', 100, 0.5, 0.2, 10, 4, 0, 86))
        
        entry = MealEntry(name='apple', date='2022-12-15', portion=100)
        values = entry.values
        
        self.assertIsInstance(values, tuple)
        self.assertEqual(values[0], '2022-12-15')  # date
        self.assertEqual(values[1], 'apple')        # name
        self.assertEqual(values[2], 100)            # portion

    @patch('calorie_count.src.DB.food_db.FoodDB.__enter__')
    def test_meal_entry_requires_name_or_food(self, mock: Mock):
        """Test that MealEntry requires either name or food."""
        mock.return_value = self.fdb
        with self.assertRaises(AssertionError):
            MealEntry(date='2022-12-15', portion=100)


if __name__ == '__main__':
    # tf = TestFoodDB()
    # tf.setUp()
    # try:
    #     tf.test_meal_entry_with_food_object()
    # finally:
    #     tf.tearDown()
    
    unittest.main()
