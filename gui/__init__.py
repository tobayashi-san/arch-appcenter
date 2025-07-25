"""
GUI Widgets Package - Simple Version
"""

# Simple imports without dynamic loading
try:
    from .widgets.category_widget import CategoryWidget, ToolCard
except ImportError as e:
    print(f"⚠️ CategoryWidget not available: {e}")
    CategoryWidget = None
    ToolCard = None

try:
    from .widgets.status_widget import StatusWidget
except ImportError as e:
    print(f"⚠️ StatusWidget not available: {e}")
    StatusWidget = None

try:
    from .widgets.command_output_widget import CommandOutputWidget
except ImportError as e:
    print(f"⚠️ CommandOutputWidget not available: {e}")
    CommandOutputWidget = None

__all__ = ['CategoryWidget', 'ToolCard', 'StatusWidget', 'CommandOutputWidget']
