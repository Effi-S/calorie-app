"""This test case simply opens all Tabs and navigation Drawer"""

import pathlib
import sys
import time
import unittest

path = pathlib.Path(__file__).absolute().parent.parent.parent
sys.path.insert(0, str(path))


def _pause():
    time.sleep(0.000001)


class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        return super().setUpClass()

    def test_startup(self):
        """TODO: Finish this Test.
        Simply test an App instance can be created."""

    #        print(sys.path)
    #        from main import CaloriesApp

    #        def _run_test(_app, *args):
    #            """ main test function """
    #            Clock.schedule_interval(_pause, 0.000001)
    #            _app.stop()
    #
    #        app = CaloriesApp()
    #        p = partial(_run_test, app)
    #        Clock.schedule_once(p, 0.000001)
    #        app.run()
    def test_open_food_search(self):
        """TODO : Finish this test. Test that opens Food Search"""


if __name__ == "__main__":
    unittest.main()
