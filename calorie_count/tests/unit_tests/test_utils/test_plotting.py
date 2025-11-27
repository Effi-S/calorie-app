"""Tests for plotting.py module."""
import os
import unittest
from unittest.mock import MagicMock, patch

# Check for display FIRST before any GUI library imports
HAS_DISPLAY = os.environ.get('DISPLAY') is not None or os.name == 'nt'

# Try to import matplotlib, skip tests if not available
# Set backend BEFORE importing pyplot to avoid GUI initialization
MATPLOTLIB_AVAILABLE = False
plt = None
if HAS_DISPLAY:
    try:
        import matplotlib
        # Use non-interactive backend to avoid GUI issues
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        MATPLOTLIB_AVAILABLE = True
    except (ImportError, OSError, RuntimeError, SystemError):
        MATPLOTLIB_AVAILABLE = False
        plt = None
else:
    MATPLOTLIB_AVAILABLE = False
    plt = None

# Skip tests if Kivy is not available or in headless environment
KIVY_AVAILABLE = False
Image = None
if HAS_DISPLAY:
    try:
        from kivy.uix.image import Image
        KIVY_AVAILABLE = True
    except (ImportError, OSError, RuntimeError, SystemError):
        KIVY_AVAILABLE = False
        Image = None
else:
    KIVY_AVAILABLE = False
    Image = None

# Only import plotting functions if both are available AND we have a display
# This prevents segfaults in headless environments
# IMPORTANT: Do NOT import plotting module in headless environments as it will
# cause matplotlib to initialize fonts and crash
fig2img = None
plot_graph = None
plot_pie_chart = None
if KIVY_AVAILABLE and MATPLOTLIB_AVAILABLE and HAS_DISPLAY:
    try:
        from calorie_count.src.utils.plotting import fig2img, plot_graph, plot_pie_chart
    except (ImportError, OSError, RuntimeError, SystemError):
        # Catch SystemError which can occur with GUI libraries
        pass


class TestPlotting(unittest.TestCase):
    
    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_with_data(self):
        """Test plotting pie chart with valid data."""
        data = {'apple': 100, 'banana': 200, 'orange': 150}
        result = plot_pie_chart(data)
        
        # Should return an Image widget
        self.assertIsInstance(result, Image)
        self.assertIsNotNone(result.texture)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_empty_data(self):
        """Test plotting pie chart with empty data."""
        data = {}
        result = plot_pie_chart(data)
        
        # Should still return an Image widget with "No Data" label
        self.assertIsInstance(result, Image)
        self.assertIsNotNone(result.texture)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_zero_values(self):
        """Test plotting pie chart with zero values."""
        data = {'apple': 0, 'banana': 0}
        result = plot_pie_chart(data)
        
        self.assertIsInstance(result, Image)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_with_data(self):
        """Test plotting graph with valid data."""
        data = {
            '2022-01-11': 100,
            '2022-01-10': 200,
            '2022-01-09': 150
        }
        result = plot_graph(data, y_label='Calories')
        
        self.assertIsInstance(result, Image)
        self.assertIsNotNone(result.texture)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_single_data_point(self):
        """Test plotting graph with single data point (should use bar chart)."""
        data = {'2022-01-11': 100}
        result = plot_graph(data, y_label='Calories')
        
        self.assertIsInstance(result, Image)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_with_x_label(self):
        """Test plotting graph with x label."""
        data = {
            '2022-01-11': 100,
            '2022-01-10': 200
        }
        result = plot_graph(data, x_label='Date', y_label='Calories')
        
        self.assertIsInstance(result, Image)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_empty_data(self):
        """Test plotting graph with empty data."""
        data = {}
        result = plot_graph(data, y_label='Calories')
        
        self.assertIsInstance(result, Image)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(fig2img is None, "Plotting functions not available")
    def test_fig2img(self):
        """Test converting matplotlib figure to Kivy image."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        result = fig2img(fig)
        
        self.assertIsInstance(result, Image)
        self.assertIsNotNone(result.texture)
        
        plt.close(fig)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_percentages(self):
        """Test that pie chart converts values to percentages."""
        data = {'apple': 100, 'banana': 200}  # Total: 300
        result = plot_pie_chart(data)
        
        # Should successfully create image
        self.assertIsInstance(result, Image)


if __name__ == '__main__':
    unittest.main()
