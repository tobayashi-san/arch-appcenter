<img width="1407" height="927" alt="image" src="https://github.com/user-attachments/assets/a5672328-8fb9-4fb7-907d-eccfff6ea787" /># 🔧 Arch Linux Configuration Tool

A modern, native GUI application for Arch-based Linux distributions that provides a centralized interface for system configuration and maintenance. Built with PyQt6 and designed specifically for Arch Linux, EndeavourOS, Manjaro, and other Arch-based distributions.

## ✨ Features

- **🎯 Centralized Configuration**: Manage system tools and configurations from one interface
- **📦 Multi-Package Manager Support**: Works with pacman, flatpak, and AUR helpers (yay/paru)
- **🌐 GitHub-Based Configuration**: Automatically downloads tool configurations from GitHub
- **🎨 Adaptive Theming**: Automatically detects and adapts to your system theme (KDE, GNOME, XFCE)
- **⚡ Batch Operations**: Execute multiple tools and configurations at once
- **📋 Command History**: Track and review executed commands
- **🔍 Smart Search**: Find tools and configurations quickly
- **🛡️ Safety Features**: Built-in command validation and confirmation dialogs
- **📊 System Status**: Real-time system information and dependency checking

  
##  Screenshots
<img width="1407" height="927" alt="image" src="https://github.com/user-attachments/assets/a290b93d-3660-44d7-91db-950c15f15f50" />

## 🚀 Quick Start

### Prerequisites

- Arch Linux or Arch-based distribution (EndeavourOS, Manjaro, etc.)
- Python 3.9 or higher
- PyQt6

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/tobayashi-san/arch-appcenter.git
cd arch-appcenter
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Run the application:**
```bash
python main.py
```

## 📦 Dependencies

### Required Python Packages
- PyQt6 >= 6.5.0
- requests >= 2.31.0
- PyYAML >= 6.0

### System Dependencies (Automatically Checked)
- `pacman` - Arch package manager
- `sudo` - Superuser privileges
- `flatpak` (optional) - Universal package manager
- `yay` or `paru` (optional) - AUR helpers
- `reflector` (optional) - Mirror optimization
- `git` (optional) - Version control

## 🛠️ Usage

### Basic Operation

1. **Launch the application:**
```bash
python main.py
```

2. **Browse categories** in the left sidebar
3. **Select tools** you want to execute
4. **Use batch execution** for multiple tools
5. **Monitor progress** in the output console

### Command Line Options

```bash
python main.py --help

Options:
  --check-deps     Check system dependencies and exit
  --debug         Enable debug output
  --reset-config  Reset configuration cache
  --config-url    Use custom configuration URL
```

### Configuration Categories

- **🔧 System Maintenance**: Updates, cleanup, mirror optimization
- **🖥️ Graphics Drivers**: NVIDIA, AMD, Intel driver installation
- **💻 Development Tools**: IDEs, containers, programming languages
- **🎵 Multimedia**: Media players, image editors, streaming tools
- **🎮 Gaming**: Steam, Lutris, Wine, gaming optimizations
- **📄 Productivity**: Office suites, email clients
- **🔐 Security & Backup**: Firewalls, backup solutions
- **📦 Package Managers**: AUR helpers, Flatpak setup
- **🔧 Troubleshooting**: Common system fixes

## ⚙️ Configuration

The application uses a YAML configuration file automatically downloaded from GitHub. The configuration defines available tools, commands, and categories.

### Custom Configuration

You can use a custom configuration source:

```bash
python main.py --config-url "https://your-domain.com/custom-config.yaml"
```

### Configuration Format

```yaml
categories:
  system_maintenance:
    name: "System Maintenance"
    description: "Essential system maintenance tasks"
    order: 1
    icon: "🔧"
    tools:
      - name: "System Update"
        description: "Full system update with pacman"
        command: "sudo pacman -Syu --noconfirm"
        tags: ["update", "system"]
        requires: ["pacman"]
```

## 🎨 Theming

The application automatically detects your system theme:

- **KDE Plasma**: Reads `kdeglobals` configuration
- **GNOME**: Uses `gsettings` for theme detection

### Manual Theme Override

Themes are located in `gui/styles/`:
- `styles.css` - Base layout and structure
- `dark_theme.css` - Dark theme colors
- `light_theme.css` - Light theme colors

## 🔧 Development

### Project Structure

```
arch-appcenter/
├── main.py                 # Application entry point
├── core/                   # Backend components
│   ├── config_manager.py   # Configuration handling
│   ├── command_executor.py # Command execution
│   └── dependency_check.py # System validation
├── gui/                    # User interface
│   ├── main_window.py      # Main application window
│   ├── styles/             # CSS themes
│   └── widgets/            # Custom widgets
├── data/                   # Configuration cache
└── logs/                   # Application logs
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly on Arch Linux
5. Submit a pull request

### Adding New Tools

To add new tools, modify the configuration YAML:

```yaml
your_category:
  name: "Your Category"
  tools:
    - name: "Your Tool"
      description: "Tool description"
      command: "your-command-here"
      tags: ["tag1", "tag2"]
      requires: ["dependency"]
```

## 🐛 Troubleshooting

### Common Issues

**Application won't start:**
```bash
# Check Python version
python --version

# Check dependencies
python main.py --check-deps

# Run in debug mode
python main.py --debug
```

### Logs

Application logs are stored in the `logs/` directory:
- Error logs: `error_YYYYMMDD_HHMMSS.log`
- Debug output when using `--debug` flag

## 🤝 Support

- **GitHub Issues**: [Report bugs and request features](https://github.com/tobayashi-san/arch-appcenter/issues)
- **Arch Forums**: Community support

## 📄 License

This project is open source and available under the MIT License. You are free to use, modify, and distribute this software as long as it remains open source.

```
MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, subject to the following conditions:

- The software must remain open source
- Derivative works must also be open source
- Include the original license notice
```


## 📊 Stats

![GitHub stars](https://img.shields.io/github/stars/tobayashi-san/arch-appcenter)
![GitHub forks](https://img.shields.io/github/forks/tobayashi-san/arch-appcenter)
![GitHub issues](https://img.shields.io/github/issues/tobayashi-san/arch-appcenter)
![Python version](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-MIT-green)

