# 🚀 Arch Appcenter

A modern, native GUI application for Arch-based Linux distributions that provides a centralized interface for system configuration and maintenance. Built with PyQt6 and designed specifically for Arch Linux, EndeavourOS, Manjaro, and other Arch-based distributions.

## ⚡ Quick Install

```bash
curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/install.sh -o install.sh
./install.sh
```

**No root required!** Installs to user directories (`~/.local/`).

## ✨ Features

- **🎯 User-Friendly Installation**: No root privileges required
- **📦 Multi-Package Manager Support**: Works with pacman, flatpak, and AUR helpers (yay/paru)
- **🌐 GitHub-Based Configuration**: Automatically downloads tool configurations
- **🎨 Adaptive Theming**: Automatically detects and adapts to your system theme
- **⚡ Batch Operations**: Execute multiple tools and configurations at once
- **🔍 Smart Search**: Find tools and configurations quickly
- **🛡️ Safety Features**: Built-in command validation and confirmation dialogs
- **📊 System Status**: Real-time system information and dependency checking

## 🖥️ Screenshots

![Arch Appcenter Screenshot](https://github.com/user-attachments/assets/a290b93d-3660-44d7-91db-950c15f15f50)

## 📦 Installation Options

### Option 1: One-Line Install (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/install.sh -o install.sh
./install.sh
```

### Option 2: Manual Installation
```bash
git clone https://github.com/tobayashi-san/arch-appcenter.git
cd arch-appcenter
./install.sh
```

### Option 3: Direct Run (Development)
```bash
git clone https://github.com/tobayashi-san/arch-appcenter.git
cd arch-appcenter
python main.py
```

## 🗑️ Uninstallation

```bash
# If installed via installer
arch-appcenter-uninstall

# Or online uninstaller
curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/uninstall.sh -o uninstall.sh
./uninstall.sh
```

## 🎯 Installation Details

- **Install Location**: `~/.local/share/arch-appcenter/`
- **Executable**: `~/.local/bin/arch-appcenter`
- **Desktop Entry**: `~/.local/share/applications/`
- **User Data**: `~/.local/share/arch-appcenter/`
- **Configuration**: `~/.config/arch-appcenter/`

## 🔧 Usage

### Terminal Commands
```bash
# Start GUI
arch-appcenter

# Check dependencies
arch-appcenter --check-deps

# Reset configuration
arch-appcenter --reset-config

# Show help
arch-appcenter --help

# Uninstall
arch-appcenter-uninstall
```

### Desktop Integration
- **Application Menu**: Search for "Arch Appcenter"
- **Desktop Shortcut**: Double-click desktop icon
- **Right-click Actions**: Check deps, refresh config, uninstall

## 📋 System Requirements

### Required
- Arch Linux or Arch-based distribution
- Python 3.9+
- PyQt6
- requests
- PyYAML

### Automatic Installation
The installer automatically installs missing dependencies:
```bash
sudo pacman -S python python-pyqt6 python-requests python-yaml
```

### Optional (Enhanced Features)
- `flatpak` - Universal package manager
- `yay` or `paru` - AUR helpers
- `reflector` - Mirror optimization
- `git` - Version control

## 🛠️ Configuration Categories

- **🔧 System Maintenance**: Updates, cleanup, mirror optimization
- **🖥️ Graphics Drivers**: NVIDIA, AMD, Intel driver installation
- **💻 Development Tools**: IDEs, containers, programming languages
- **🎵 Multimedia**: Media players, image editors, streaming tools
- **🎮 Gaming**: Steam, Lutris, Wine, gaming optimizations
- **📄 Productivity**: Office suites, email clients
- **🔐 Security & Backup**: Firewalls, backup solutions
- **📦 Package Managers**: AUR helpers, Flatpak setup
- **🔧 Troubleshooting**: Common system fixes

## 🎨 Theming

The application automatically detects your system theme:
- **KDE Plasma**: Reads `kdeglobals` configuration
- **GNOME**: Uses `gsettings` for theme detection
- **XFCE**: Reads `xfconf` configuration
- **Fallback**: Qt palette detection

## 🔧 Development

### Project Structure
```
arch-appcenter/
├── main.py                 # Application entry point
├── install.sh              # User installer
├── uninstall.sh            # User uninstaller
├── core/                   # Backend components
├── gui/                    # User interface
├── config.yaml             # Tool configuration
└── requirements.txt        # Dependencies
```

### Local Development
```bash
git clone https://github.com/tobayashi-san/arch-appcenter.git
cd arch-appcenter

# Install dependencies
sudo pacman -S python-pyqt6 python-requests python-yaml

# Run directly
python main.py --debug
```

### Adding New Tools
Modify `config.yaml` to add new tools:
```yaml
your_category:
  name: "Your Category"
  tools:
    - name: "Your Tool"
      description: "Tool description"
      command: "your-command-here"
      tags: ["tag1", "tag2"]
```

## 🐛 Troubleshooting

### Common Issues

**Installation fails:**
```bash
# Check dependencies
arch-appcenter --check-deps

# Manual dependency install
sudo pacman -S python-pyqt6 python-requests python-yaml
```

**PATH issues:**
```bash
# Add to shell configuration
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

**Permission errors:**
- Never run as root - this is a user installation
- Check if `~/.local/bin` exists and is writable

### Logs
- Application logs: `~/.local/share/arch-appcenter/logs/`
- Error logs include timestamp and debug information

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test on Arch Linux
5. Submit a pull request

## 📄 License

This project is open source and available under the MIT License.

## 📊 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/tobayashi-san/arch-appcenter/issues)
- **Discussions**: [Community support and ideas](https://github.com/tobayashi-san/arch-appcenter/discussions)

## 🎖️ Stats

![GitHub stars](https://img.shields.io/github/stars/tobayashi-san/arch-appcenter)
![GitHub forks](https://img.shields.io/github/forks/tobayashi-san/arch-appcenter)
![GitHub issues](https://img.shields.io/github/issues/tobayashi-san/arch-appcenter)
![Python version](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)
