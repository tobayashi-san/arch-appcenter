"""
Dependency Checker - Simplified
Verifies that required package managers are installed
"""

import subprocess
import shutil
import os
from typing import Dict, List, Tuple
from PyQt6.QtWidgets import QMessageBox, QWidget

class DependencyChecker:
    def __init__(self, parent_widget: QWidget = None):
        self.parent_widget = parent_widget

        # Required dependencies
        self.required_tools = {
            'pacman': 'Arch Linux Package Manager',
            'sudo': 'Superuser privileges'
        }

        # Optional dependencies
        self.optional_tools = {
            'flatpak': 'Universal Package Manager',
            'yay': 'AUR Helper (yay)',
            'paru': 'AUR Helper (paru)',
            'reflector': 'Mirror ranking tool',
            'git': 'Version control system'
        }

    def check_command_exists(self, command: str) -> bool:
        """Check if a command exists in PATH"""
        return shutil.which(command) is not None

    def check_dependencies(self) -> Tuple[Dict[str, bool], Dict[str, bool]]:
        """Check if required and optional dependencies are available"""
        print("🔍 Checking dependencies...")

        required_status = {}
        optional_status = {}

        # Check required tools
        for tool, description in self.required_tools.items():
            exists = self.check_command_exists(tool)
            required_status[tool] = exists
            status = "✅" if exists else "❌"
            print(f"  {status} {tool}: {description}")

        # Check optional tools (including AUR helpers)
        for tool, description in self.optional_tools.items():
            if tool in ['yay', 'paru']:
                # Check if any AUR helper exists
                exists = self.check_command_exists('yay') or self.check_command_exists('paru')
                key = 'aur_helper'
            else:
                exists = self.check_command_exists(tool)
                key = tool

            optional_status[key] = exists
            status = "✅" if exists else "⚠️"
            print(f"  {status} {tool}: {description}")

        return required_status, optional_status

    def get_missing_dependencies(self, status_dict: Dict[str, bool]) -> List[str]:
        """Get list of missing dependencies"""
        return [tool for tool, exists in status_dict.items() if not exists]

    def install_missing_dependencies(self, missing: List[str]) -> bool:
        """Attempt to install missing dependencies"""
        if not missing:
            return True

        print(f"\n📦 Installing missing dependencies: {', '.join(missing)}")

        install_commands = {
            'flatpak': 'sudo pacman -S --noconfirm flatpak',
            'git': 'sudo pacman -S --noconfirm git',
            'reflector': 'sudo pacman -S --noconfirm reflector'
        }

        success = True
        for tool in missing:
            if tool in install_commands:
                try:
                    print(f"  📥 Installing {tool}...")
                    result = subprocess.run(
                        install_commands[tool].split(),
                        capture_output=True,
                        text=True,
                        timeout=300
                    )

                    if result.returncode == 0:
                        print(f"  ✅ {tool} installed successfully")
                    else:
                        print(f"  ❌ Failed to install {tool}: {result.stderr}")
                        success = False

                except Exception as e:
                    print(f"  ❌ Error installing {tool}: {e}")
                    success = False

            elif tool == 'aur_helper':
                self.show_aur_helper_instructions()

        return success

    def show_aur_helper_instructions(self):
        """Show manual installation instructions for AUR helpers"""
        instructions = """
AUR Helper Installation:

Option 1 - Install YAY:
git clone https://aur.archlinux.org/yay.git
cd yay && makepkg -si

Option 2 - Install PARU:
git clone https://aur.archlinux.org/paru.git
cd paru && makepkg -si

Note: Only one AUR helper is required!
        """

        if self.parent_widget:
            msg = QMessageBox(self.parent_widget)
            msg.setWindowTitle("Manual Installation Required")
            msg.setIcon(QMessageBox.Icon.Information)
            msg.setText("AUR Helper must be installed manually:")
            msg.setDetailedText(instructions.strip())
            msg.exec()
        else:
            print("\n📋 Manual Installation Required:")
            print(instructions)

    def get_available_aur_helper(self) -> str:
        """Return the first available AUR helper"""
        for helper in ['yay', 'paru']:
            if self.check_command_exists(helper):
                return helper
        return None

    def check_arch_linux(self) -> bool:
        """Check if running on Arch Linux or Arch-based distribution"""
        try:
            # Check /etc/os-release
            if os.path.exists('/etc/os-release'):
                with open('/etc/os-release', 'r') as f:
                    content = f.read().lower()
                    if any(distro in content for distro in ['arch', 'manjaro', 'endeavouros', 'artix']):
                        return True

            # Check if pacman exists (strong indicator)
            return self.check_command_exists('pacman')

        except:
            return False

    def run_startup_check(self) -> bool:
        """Run complete startup dependency check"""
        print("🚀 Running dependency check...")

        # Check if Arch Linux
        if not self.check_arch_linux():
            if self.parent_widget:
                msg = QMessageBox(self.parent_widget)
                msg.setWindowTitle("Warning")
                msg.setIcon(QMessageBox.Icon.Warning)
                msg.setText("This tool is designed for Arch Linux.\nYour distribution was not detected.")
                msg.setInformativeText("Do you want to continue anyway?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
                if msg.exec() != QMessageBox.StandardButton.Yes:
                    return False
            else:
                print("⚠️ Warning: No Arch-based distribution detected!")

        # Dependency check
        required_status, optional_status = self.check_dependencies()
        missing_required = self.get_missing_dependencies(required_status)
        missing_optional = self.get_missing_dependencies(optional_status)

        # Handle missing critical dependencies
        if missing_required:
            print(f"\n❌ Critical dependencies missing: {', '.join(missing_required)}")

            if self.parent_widget:
                msg = QMessageBox(self.parent_widget)
                msg.setWindowTitle("Missing Dependencies")
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("Critical dependencies are missing!")
                msg.setInformativeText(f"Missing: {', '.join(missing_required)}\n\nShould these be installed?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                if msg.exec() == QMessageBox.StandardButton.Yes:
                    success = self.install_missing_dependencies(missing_required)
                    if not success:
                        return False
                else:
                    return False
            else:
                return False

        # Handle optional dependencies
        if missing_optional:
            print(f"\n⚠️ Optional dependencies missing: {', '.join(missing_optional)}")

            if self.parent_widget:
                msg = QMessageBox(self.parent_widget)
                msg.setWindowTitle("Optional Dependencies")
                msg.setIcon(QMessageBox.Icon.Question)
                msg.setText("Optional dependencies are missing.")
                msg.setInformativeText(f"Missing: {', '.join(missing_optional)}\n\nShould these be installed?")
                msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

                if msg.exec() == QMessageBox.StandardButton.Yes:
                    self.install_missing_dependencies(missing_optional)

        print("✅ Dependency check completed!")
        return True
