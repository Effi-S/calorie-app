"""Tests for external/client.py module."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from calorie_count.src.DB.external.client import ExternalFoodsDB, FoodData


class TestExternalFoodsDB(unittest.TestCase):

    def setUp(self):
        """Create a temporary external foods database for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.temp_dir, 'external_foods')
        
        # Create the database file
        conn = sqlite3.connect(self.test_db_path)
        conn.close()

    def tearDown(self):
        """Clean up temporary files."""
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)
        os.rmdir(self.temp_dir)

    @patch('calorie_count.src.DB.external.client.Path')
    def test_add_food(self, mock_path_class):
        """Test adding food to external database."""
        # Mock Path().glob() to return our test database path
        mock_path_instance = MagicMock()
        mock_path_instance.glob.return_value = [Path(self.test_db_path)]
        mock_path_class.return_value = mock_path_instance
        
        food = FoodData(
            description='Test Apple',
            portions='cup:100,bowl:200',
            protein=0.5,
            fats=0.2,
            carbs=10.0,
            sodium=0.0,
            sugar=4.0,
            water=86.0
        )
        
        with ExternalFoodsDB(locally=True) as db:
            db.add_food(food)
            
            # Verify food was added
            results = list(db.get_similar_food_by_name('Test Apple', max_results=1))
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].description, 'Test Apple')

    @patch('calorie_count.src.DB.external.client.Path')
    def test_get_similar_food_by_name_exact_match(self, mock_path_class):
        """Test getting food by exact name match."""
        mock_path_instance = MagicMock()
        mock_path_instance.glob.return_value = [Path(self.test_db_path)]
        mock_path_class.return_value = mock_path_instance
        
        food1 = FoodData(
            description='Red Apple',
            portions='cup:100',
            protein=0.5, fats=0.2, carbs=10.0, sodium=0.0, sugar=4.0, water=86.0
        )
        food2 = FoodData(
            description='Green Banana',
            portions='cup:100',
            protein=1.0, fats=0.3, carbs=20.0, sodium=1.0, sugar=15.0, water=75.0
        )
        
        with ExternalFoodsDB(locally=True) as db:
            db.add_food(food1)
            db.add_food(food2)
            
            # Search for "Apple"
            results = list(db.get_similar_food_by_name('Apple', max_results=5))
            self.assertGreaterEqual(len(results), 1)
            self.assertIn('Apple', results[0].description)

    @patch('calorie_count.src.DB.external.client.Path')
    def test_get_similar_food_by_name_max_results(self, mock_path_class):
        """Test that max_results limits the number of results."""
        mock_path_instance = MagicMock()
        mock_path_instance.glob.return_value = [Path(self.test_db_path)]
        mock_path_class.return_value = mock_path_instance
        
        # Add multiple foods
        with ExternalFoodsDB(locally=True) as db:
            for i in range(10):
                food = FoodData(
                    description=f'Test Food {i}',
                    portions='cup:100',
                    protein=0.5, fats=0.2, carbs=10.0, sodium=0.0, sugar=4.0, water=86.0
                )
                db.add_food(food)
            
            # Request max 3 results
            results = list(db.get_similar_food_by_name('Test', max_results=3))
            self.assertLessEqual(len(results), 3)

    def test_food_data_post_init(self):
        """Test FoodData __post_init__ removes quotes."""
        food = FoodData(
            description='Test "Food"',
            portions='cup:100',
            protein=0.5, fats=0.2, carbs=10.0, sodium=0.0, sugar=4.0, water=86.0
        )
        
        self.assertNotIn('"', food.description)

    def test_food_data_attributes(self):
        """Test FoodData attributes are set correctly."""
        food = FoodData(
            description='Test Food',
            portions='cup:100,bowl:200',
            protein=1.0,
            fats=0.5,
            carbs=20.0,
            sodium=2.0,
            sugar=10.0,
            water=80.0
        )
        
        self.assertEqual(food.description, 'Test Food')
        self.assertEqual(food.portions, 'cup:100,bowl:200')
        self.assertEqual(food.protein, 1.0)
        self.assertEqual(food.fats, 0.5)
        self.assertEqual(food.carbs, 20.0)
        self.assertEqual(food.sodium, 2.0)
        self.assertEqual(food.sugar, 10.0)
        self.assertEqual(food.water, 80.0)


if __name__ == '__main__':
    unittest.main()
