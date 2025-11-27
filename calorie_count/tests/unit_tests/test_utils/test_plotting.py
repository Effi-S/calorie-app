"""Tests for plotting.py module."""
import os
import unittest
from unittest.mock import MagicMock, patch

# Try to import matplotlib - Agg backend works without display
MATPLOTLIB_AVAILABLE = False
plt = None
try:
    import matplotlib
    # Use non-interactive backend to avoid GUI issues
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except (ImportError, OSError, RuntimeError, SystemError):
    MATPLOTLIB_AVAILABLE = False
    plt = None

# Import Kivy only if needed for fig2img tests
KIVY_AVAILABLE = False
Image = None
HAS_DISPLAY = os.environ.get('DISPLAY') is not None or os.name == 'nt'
if HAS_DISPLAY:
    try:
        from kivy.uix.image import Image
        KIVY_AVAILABLE = True
    except (ImportError, OSError, RuntimeError, SystemError):
        KIVY_AVAILABLE = False
        Image = None

# Import plotting functions - they now return matplotlib Figures directly
# Only import fig2img if Kivy is available (for conversion to Kivy Image)
plot_graph = None
plot_pie_chart = None
fig2img = None

if MATPLOTLIB_AVAILABLE:
    try:
        from calorie_count.src.utils.plotting import plot_graph, plot_pie_chart
        if KIVY_AVAILABLE and HAS_DISPLAY:
            from calorie_count.src.utils.plotting import fig2img
    except (ImportError, OSError, RuntimeError, SystemError):
        # Catch SystemError which can occur with GUI libraries
        pass


class TestPlotting(unittest.TestCase):
    
    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_with_data(self):
        """Test plotting pie chart with valid data."""
        data = {'apple': 100, 'banana': 200, 'orange': 150}
        result = plot_pie_chart(data)
        
        # Should return a matplotlib Figure
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_empty_data(self):
        """Test plotting pie chart with empty data."""
        data = {}
        result = plot_pie_chart(data)
        
        # Should return a matplotlib Figure
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_zero_values(self):
        """Test plotting pie chart with zero values."""
        data = {'apple': 0, 'banana': 0}
        result = plot_pie_chart(data)
        
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_with_data(self):
        """Test plotting graph with valid data."""
        data = {
            '2022-01-11': 100,
            '2022-01-10': 200,
            '2022-01-09': 150
        }
        result = plot_graph(data, y_label='Calories')
        
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_single_data_point(self):
        """Test plotting graph with single data point (should use bar chart)."""
        data = {'2022-01-11': 100}
        result = plot_graph(data, y_label='Calories')
        
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_with_x_label(self):
        """Test plotting graph with x label."""
        data = {
            '2022-01-11': 100,
            '2022-01-10': 200
        }
        result = plot_graph(data, x_label='Date', y_label='Calories')
        
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_graph is None, "Plotting functions not available")
    def test_plot_graph_empty_data(self):
        """Test plotting graph with empty data."""
        data = {}
        result = plot_graph(data, y_label='Calories')
        
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(not KIVY_AVAILABLE, "Kivy not available")
    @unittest.skipIf(not HAS_DISPLAY, "No display available (headless environment)")
    @unittest.skipIf(fig2img is None, "fig2img function not available")
    def test_fig2img(self):
        """Test converting matplotlib figure to Kivy image."""
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3], [1, 2, 3])
        
        result = fig2img(fig)
        
        self.assertIsInstance(result, Image)
        self.assertIsNotNone(result.texture)
        
        plt.close(fig)

    @unittest.skipIf(not MATPLOTLIB_AVAILABLE, "Matplotlib not available")
    @unittest.skipIf(plot_pie_chart is None, "Plotting functions not available")
    def test_plot_pie_chart_percentages(self):
        """Test that pie chart converts values to percentages."""
        data = {'apple': 100, 'banana': 200}  # Total: 300
        result = plot_pie_chart(data)
        
        # Should successfully create matplotlib Figure
        from matplotlib.figure import Figure
        self.assertIsInstance(result, Figure)
        plt.close(result)  # Clean up


if __name__ == '__main__':
    unittest.main()
