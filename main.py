#!/usr/bin/env python3
"""
Arch Linux Configuration Tool - Main Entry Point
Überarbeitet mit verbesserter Fehlerbehandlung und Initialisierung
"""

import sys
import os
import argparse
import traceback
from pathlib import Path

# Minimum Python version check
if sys.version_info < (3, 9):
    print("❌ Error: Python 3.9 or higher is required")
    print(f"   Current version: {sys.version}")
    print("   Please upgrade Python to continue.")
    sys.exit(1)

def setup_simple_theme_switcher(app):
    """Einfache Integration in bestehende App"""
    theme_switcher = SimpleThemeSwitcher(app)
    return theme_switcher

def setup_paths():
    """Setup application paths"""
    # Get script directory
    BASE_DIR = Path(__file__).resolve().parent

    # Add to Python path for imports
    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    data_dir = BASE_DIR / "data"
    data_dir.mkdir(exist_ok=True)

    logs_dir = BASE_DIR / "logs"
    logs_dir.mkdir(exist_ok=True)

    return BASE_DIR, data_dir, logs_dir


def check_dependencies():
    """Check for required dependencies"""
    print("🔍 Checking Python dependencies...")

    required_packages = {
        'PyQt6': 'PyQt6',
        'requests': 'requests',
        'yaml': 'PyYAML'
    }

    missing_packages = []

    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
            print(f"  ✅ {package_name}")
        except ImportError:
            print(f"  ❌ {package_name} - Not found")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n❌ Missing required packages: {', '.join(missing_packages)}")
        print(f"📦 Install with: pip install {' '.join(missing_packages)}")
        return False

    print("✅ All Python dependencies satisfied")
    return True

def run_system_dependency_check():
    """Run system-level dependency check"""
    print("🔍 Running system dependency check...")

    try:
        from core.dependency_check import DependencyChecker

        checker = DependencyChecker()
        success = checker.run_startup_check()

        if success:
            print("✅ System dependencies check passed")
        else:
            print("⚠️ Some system dependencies are missing")
            print("   The application will still start, but some features may be limited")

        return success

    except Exception as e:
        print(f"⚠️ System dependency check failed: {e}")
        print("   Continuing with application startup...")
        return False

def create_application():
    """Create and configure Qt application"""
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import Qt, QDir
        from PyQt6.QtGui import QIcon

        print("🎨 Creating Qt application...")

        # Create application instance
        app = QApplication(sys.argv)

        # Configure application
        app.setApplicationName("Arch Config Tool")
        app.setApplicationDisplayName("Arch Linux Configuration Tool")
        app.setApplicationVersion("2.0.0")
        app.setOrganizationName("ArchConfigTool")
        app.setOrganizationDomain("archconfig.local")

        # Set application icon (if available)
        try:
            icon_path = Path(__file__).parent / "assets" / "icon.png"
            if icon_path.exists():
                app.setWindowIcon(QIcon(str(icon_path)))
        except:
            pass  # Icon is optional

        # Enable high DPI support (PyQt6 syntax)
        try:
            # These attributes may not be available in all PyQt6 versions
            if hasattr(Qt.ApplicationAttribute, 'AA_EnableHighDpiScaling'):
                app.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)
            if hasattr(Qt.ApplicationAttribute, 'AA_UseHighDpiPixmaps'):
                app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)
        except AttributeError:
            # High DPI support is enabled by default in newer Qt6 versions
            pass

        print("✅ Qt application created successfully")
        return app

    except ImportError as e:
        print(f"❌ Failed to import Qt: {e}")
        print("💡 Install PyQt6: pip install PyQt6")
        return None
    except Exception as e:
        print(f"❌ Failed to create Qt application: {e}")
        return None

def load_application_theme(app):
    """Load and apply application theme"""
    try:
        print("🎨 Loading application theme...")

        # Try to load custom stylesheet
        style_path = Path(__file__).parent / "gui" / "styles" / "styles.css"

        if style_path.exists():
            with open(style_path, 'r', encoding='utf-8') as f:
                custom_stylesheet = f.read()
                app.setStyleSheet(custom_stylesheet)
                print("✅ Custom stylesheet loaded")
        else:
            # Fallback to embedded stylesheet
            app.setStyleSheet(get_embedded_stylesheet())
            print("✅ Embedded stylesheet loaded")

    except Exception as e:
        print(f"⚠️ Failed to load custom theme: {e}")
        # Apply basic fallback theme
        app.setStyleSheet(get_minimal_stylesheet())
        print("✅ Fallback theme applied")


def create_main_window(app):
    """Create and configure main window"""
    try:
        print("🏠 Creating main window...")

        from gui.main_window import MainWindow

        # Create main window
        window = MainWindow()

        # Center window on screen
        screen = app.primaryScreen().geometry()
        window_size = window.size()
        x = (screen.width() - window_size.width()) // 2
        y = (screen.height() - window_size.height()) // 2
        window.move(x, y)

        print("✅ Main window created successfully")
        return window

    except ImportError as e:
        print(f"❌ Failed to import MainWindow: {e}")
        return None
    except Exception as e:
        print(f"❌ Failed to create main window: {e}")
        traceback.print_exc()
        return None

def setup_error_handling():
    """Setup global error handling"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Handle Ctrl+C gracefully
            print("\n🛑 Application interrupted by user")
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Log the error
        error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        print(f"\n💥 Uncaught exception occurred:")
        print(error_msg)

        # Try to save error to log file
        try:
            log_dir = Path(__file__).parent / "logs"
            log_dir.mkdir(exist_ok=True)

            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = log_dir / f"error_{timestamp}.log"

            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(f"Arch Config Tool Error Log\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write(f"Python: {sys.version}\n")
                f.write(f"Platform: {sys.platform}\n\n")
                f.write(error_msg)

            print(f"📝 Error logged to: {log_file}")

        except Exception as log_error:
            print(f"⚠️ Failed to write error log: {log_error}")

        # Show error dialog if Qt is available
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox

            app = QApplication.instance()
            if app:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setWindowTitle("Application Error")
                msg.setText("An unexpected error occurred.")
                msg.setInformativeText("The application may need to be restarted.")
                msg.setDetailedText(error_msg)
                msg.exec()
        except:
            pass

    # Set the exception handler
    sys.excepthook = handle_exception

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Arch Linux Configuration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Start GUI normally
  %(prog)s --check-deps       # Check dependencies and exit
  %(prog)s --debug            # Start with debug output
  %(prog)s --reset-config     # Reset configuration cache
        """
    )

    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check system dependencies and exit'
    )

    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug output'
    )

    parser.add_argument(
        '--reset-config',
        action='store_true',
        help='Reset configuration cache'
    )

    parser.add_argument(
        '--config-url',
        type=str,
        help='Custom configuration URL'
    )

    parser.add_argument(
        '--no-splash',
        action='store_true',
        help='Skip splash screen'
    )

    return parser.parse_args()

def handle_special_modes(args):
    """Handle special command line modes"""
    if args.check_deps:
        print("🔍 Dependency Check Mode")
        print("=" * 50)

        # Check Python dependencies
        python_deps_ok = check_dependencies()

        # Check system dependencies
        system_deps_ok = run_system_dependency_check()

        print("\n📋 Dependency Check Summary:")
        print(f"  Python Dependencies: {'✅ OK' if python_deps_ok else '❌ Missing'}")
        print(f"  System Dependencies: {'✅ OK' if system_deps_ok else '⚠️ Partial'}")

        if python_deps_ok and system_deps_ok:
            print("\n🎉 All dependencies satisfied! You're ready to go.")
            sys.exit(0)
        elif python_deps_ok:
            print("\n⚠️ Application can start but some features may be limited.")
            sys.exit(1)
        else:
            print("\n❌ Cannot start application. Install missing Python packages first.")
            sys.exit(2)

    if args.reset_config:
        print("🗑️ Resetting configuration cache...")
        try:
            config_cache = Path(__file__).parent / "data" / "config_cache.yaml"
            if config_cache.exists():
                config_cache.unlink()
                print("✅ Configuration cache cleared")
            else:
                print("ℹ️ No configuration cache found")
        except Exception as e:
            print(f"❌ Failed to clear cache: {e}")
        sys.exit(0)

def show_startup_info(args):
    """Show startup information"""
    print("🚀 Arch Linux Configuration Tool v2.0")
    print("=" * 50)
    print(f"Python: {sys.version.split()[0]}")
    print(f"Platform: {sys.platform}")

    if args.debug:
        print(f"Script path: {Path(__file__).parent}")
        print(f"Working directory: {Path.cwd()}")
        print(f"Arguments: {vars(args)}")

    print()

def main():
    """Main application entry point"""
    # Parse command line arguments
    args = parse_arguments()

    # Setup error handling
    setup_error_handling()

    # Show startup info
    show_startup_info(args)

    # Handle special modes
    handle_special_modes(args)

    # Setup application paths
    script_dir, data_dir, logs_dir = setup_paths()

    if args.debug:
        print(f"📁 Application directories:")
        print(f"  Script: {script_dir}")
        print(f"  Data: {data_dir}")
        print(f"  Logs: {logs_dir}")
        print()

    # Check Python dependencies
    if not check_dependencies():
        print("\n❌ Cannot start application due to missing dependencies.")
        sys.exit(1)

    # Run system dependency check (non-blocking)
    run_system_dependency_check()

    # Create Qt application
    app = create_application()
    if not app:
        print("❌ Failed to create Qt application")
        sys.exit(1)

    # Load theme
    load_application_theme(app)

    # Create main window
    window = create_main_window(app)
    if not window:
        print("❌ Failed to create main window")
        sys.exit(1)

    # Apply any custom configuration
    if args.config_url:
        try:
            window.config_manager.github_url = args.config_url
            print(f"🔗 Using custom config URL: {args.config_url}")
        except:
            print(f"⚠️ Failed to set custom config URL")

    # Show window
    window.show()

    print("✅ Application started successfully!")
    print("💡 Use Ctrl+C to exit from terminal")

    # Run event loop
    try:
        exit_code = app.exec()
        print(f"\n👋 Application exited with code: {exit_code}")
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n🛑 Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n💥 Application crashed: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
