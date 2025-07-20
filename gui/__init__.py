def safe_import(module_name, class_name):
    """Sicherer Import mit Fallback auf None"""
    try:
        module = __import__(f".{module_name}", package=__name__, fromlist=[class_name])
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        print(f"⚠️ Widget '{class_name}' from '{module_name}' not available: {e}")
        return None

# Sichere Imports aller Widgets
CategoryWidget = safe_import('category_widget', 'CategoryWidget')
ToolCard = safe_import('category_widget', 'ToolCard')
StatusWidget = safe_import('status_widget', 'StatusWidget')
CommandOutputWidget = safe_import('command_output_widget', 'CommandOutputWidget')
