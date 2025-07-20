#!/bin/bash
# Arch Appcenter User-Friendly Installer v2.0
# Installiert ohne root-Rechte in Benutzer-Verzeichnisse

set -e

# Configuration
REPO_URL="https://github.com/tobayashi-san/arch-appcenter"
APP_NAME="arch-appcenter"
APP_DISPLAY_NAME="Arch Appcenter"

# ✅ BENUTZER-VERZEICHNISSE (kein root erforderlich)
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
BIN_LINK="$BIN_DIR/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"
UNINSTALL_SCRIPT="$BIN_DIR/${APP_NAME}-uninstall"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_banner() {
    echo -e "${PURPLE}"
    echo "╔══════════════════════════════════════╗"
    echo "║         Arch Appcenter Installer    ║"
    echo "║         (User Installation)         ║"
    echo "║              v2.0.0                  ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

check_system() {
    print_status "Überprüfe System..."

    # Check if Arch-based
    if ! grep -qi "arch\|manjaro\|endeavour\|artix\|garuda\|cachyos" /etc/os-release 2>/dev/null; then
        print_warning "Dieses Tool ist für Arch-basierte Distributionen optimiert"
        read -p "Trotzdem fortfahren? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "Bitte NICHT als root ausführen!"
        print_error "Diese Installation erfolgt im Benutzer-Verzeichnis"
        exit 1
    fi

    # Check if already installed
    if [ -f "$BIN_LINK" ]; then
        print_warning "Arch Appcenter ist bereits installiert"
        read -p "Neu installieren? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installation abgebrochen"
            exit 0
        fi
        print_status "Entferne alte Installation..."
        rm -rf "$INSTALL_DIR" "$BIN_LINK" "$DESKTOP_FILE" "$UNINSTALL_SCRIPT" 2>/dev/null || true
    fi

    print_success "System-Check bestanden"
}

check_dependencies() {
    print_status "Überprüfe Abhängigkeiten..."

    missing_deps=()

    # Check Python
    if ! command -v python3 >/dev/null 2>&1; then
        missing_deps+=("python")
    fi

    # Check Python modules with correct import names
    print_status "Prüfe Python-Module..."

    # PyQt6 check
    if ! python3 -c "import PyQt6.QtWidgets" 2>/dev/null; then
        missing_deps+=("python-pyqt6")
        print_status "PyQt6.QtWidgets nicht gefunden"
    else
        print_status "✅ PyQt6 verfügbar"
    fi

    # requests check
    if ! python3 -c "import requests" 2>/dev/null; then
        missing_deps+=("python-requests")
        print_status "requests nicht gefunden"
    else
        print_status "✅ requests verfügbar"
    fi

    # yaml check
    if ! python3 -c "import yaml" 2>/dev/null; then
        missing_deps+=("python-yaml")
        print_status "yaml nicht gefunden"
    else
        print_status "✅ yaml verfügbar"
    fi

    if [ ${#missing_deps[@]} -gt 0 ]; then
        print_error "Fehlende Abhängigkeiten: ${missing_deps[*]}"
        echo
        echo "📦 Installiere sie mit:"
        echo "   sudo pacman -S ${missing_deps[*]}"
        echo
        read -p "Jetzt installieren? (y/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Installiere Abhängigkeiten..."
            if sudo pacman -S --needed --noconfirm "${missing_deps[@]}"; then
                print_success "Abhängigkeiten installiert"
            else
                print_error "Installation der Abhängigkeiten fehlgeschlagen"
                exit 1
            fi
        else
            print_error "Installation kann nicht fortgesetzt werden"
            exit 1
        fi
    else
        print_success "Alle Abhängigkeiten sind verfügbar"
    fi
}

create_directories() {
    print_status "Erstelle Benutzer-Verzeichnisse..."

    # Erstelle alle benötigten Verzeichnisse
    directories=(
        "$INSTALL_DIR"
        "$BIN_DIR"
        "$DESKTOP_DIR"
        "$HOME/.config/$APP_NAME"
        "$HOME/.local/share/$APP_NAME/data"
        "$HOME/.local/share/$APP_NAME/logs"
        "$HOME/.cache/$APP_NAME"
    )

    for dir in "${directories[@]}"; do
        mkdir -p "$dir"
    done

    print_success "Verzeichnisse erstellt"
}

download_and_install() {
    print_status "Lade Arch Appcenter herunter..."

    # Create temporary directory
    TEMP_DIR=$(mktemp -d)
    cd "$TEMP_DIR"

    # Clone repository
    git clone --depth 1 "$REPO_URL" .

    # Install to user directory
    cp -r * "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/main.py"

    # Create executable launcher
    cat > "$BIN_LINK" << EOF
#!/bin/bash
# Arch Appcenter User Launcher
export PYTHONPATH="$INSTALL_DIR:\$PYTHONPATH"
cd "$INSTALL_DIR"
exec python3 main.py "\$@"
EOF
    chmod +x "$BIN_LINK"

    # Cleanup
    cd ~
    rm -rf "$TEMP_DIR"

    print_success "Arch Appcenter installiert in: $INSTALL_DIR"
}

create_desktop_integration() {
    print_status "Erstelle Desktop-Integration..."

    # Create desktop entry
    cat > "$DESKTOP_FILE" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=$APP_DISPLAY_NAME
Comment=System Configuration Tool for Arch Linux
Comment[de]=Systemkonfigurations-Tool für Arch Linux
GenericName=System Configuration Tool
GenericName[de]=Systemkonfigurations-Tool
Exec=$BIN_LINK
Icon=preferences-system
Terminal=false
StartupNotify=true
Categories=System;Settings;PackageManager;Utility;
Keywords=arch;linux;configuration;package;manager;system;pacman;aur;flatpak;
Keywords[de]=arch;linux;konfiguration;paket;manager;system;pacman;aur;flatpak;
MimeType=application/x-arch-package;

# Actions for right-click menu
Actions=CheckDeps;RefreshConfig;Uninstall;

[Desktop Action CheckDeps]
Name=Check Dependencies
Name[de]=Abhängigkeiten prüfen
Exec=$BIN_LINK --check-deps
Icon=dialog-information

[Desktop Action RefreshConfig]
Name=Refresh Configuration
Name[de]=Konfiguration aktualisieren
Exec=$BIN_LINK --reset-config
Icon=view-refresh

[Desktop Action Uninstall]
Name=Uninstall Arch Appcenter
Name[de]=Arch Appcenter deinstallieren
Exec=$UNINSTALL_SCRIPT
Icon=edit-delete
EOF

    # Update user's desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
    fi

    print_success "Desktop-Integration erstellt"
}

create_uninstall_script() {
    print_status "Erstelle Uninstall-Script..."

    cat > "$UNINSTALL_SCRIPT" << EOF
#!/bin/bash
# Arch Appcenter User Uninstaller

APP_NAME="$APP_NAME"
INSTALL_DIR="$INSTALL_DIR"
BIN_LINK="$BIN_LINK"
DESKTOP_FILE="$DESKTOP_FILE"
UNINSTALL_SCRIPT="$UNINSTALL_SCRIPT"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() { echo -e "\${BLUE}[INFO]\${NC} \$1"; }
print_success() { echo -e "\${GREEN}[SUCCESS]\${NC} \$1"; }
print_warning() { echo -e "\${YELLOW}[WARNING]\${NC} \$1"; }

echo -e "\${YELLOW}"
echo "╔══════════════════════════════════════╗"
echo "║       Arch Appcenter Uninstaller    ║"
echo "╚══════════════════════════════════════╝"
echo -e "\${NC}"

if [ "\$1" != "--force" ]; then
    echo -e "\${YELLOW}Warnung:\${NC} Dies wird Arch Appcenter vollständig entfernen."
    echo
    read -p "Möchten Sie fortfahren? (y/N): " -n 1 -r
    echo
    if [[ ! \$REPLY =~ ^[Yy]\$ ]]; then
        print_status "Deinstallation abgebrochen"
        exit 0
    fi
fi

print_status "Deinstalliere Arch Appcenter..."

# Stop running instances
if pgrep -f "arch-appcenter" >/dev/null; then
    print_status "Beende laufende Instanzen..."
    pkill -f "arch-appcenter" 2>/dev/null || true
    sleep 2
fi

# Remove files
files_to_remove=(
    "\$INSTALL_DIR"
    "\$BIN_LINK"
    "\$DESKTOP_FILE"
    "\$UNINSTALL_SCRIPT"
    "\$HOME/.config/\$APP_NAME"
    "\$HOME/.cache/\$APP_NAME"
)

for file in "\${files_to_remove[@]}"; do
    if [ -e "\$file" ]; then
        print_status "Entferne: \$file"
        rm -rf "\$file"
    fi
done

# Ask about user data
user_data_dir="\$HOME/.local/share/\$APP_NAME"
if [ -d "\$user_data_dir" ]; then
    read -p "Benutzerdaten auch entfernen? (\$user_data_dir) (y/N): " -n 1 -r
    echo
    if [[ \$REPLY =~ ^[Yy]\$ ]]; then
        rm -rf "\$user_data_dir"
        print_status "Benutzerdaten entfernt"
    fi
fi

# Update desktop database
if command -v update-desktop-database >/dev/null 2>&1; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

print_success "🗑️ Arch Appcenter erfolgreich deinstalliert!"
echo
echo "Vielen Dank, dass Sie Arch Appcenter verwendet haben!"
EOF

    chmod +x "$UNINSTALL_SCRIPT"
    print_success "Uninstaller erstellt: ${APP_NAME}-uninstall"
}

create_kde_desktop_shortcut() {
    print_status "Erstelle Desktop-Verknüpfung..."

    # Check if Desktop directory exists
    if [ -d "$HOME/Desktop" ]; then
        shortcut_file="$HOME/Desktop/$APP_NAME.desktop"

        cp "$DESKTOP_FILE" "$shortcut_file"
        chmod +x "$shortcut_file"

        # Make it trusted in KDE
        if [ -n "$KDE_SESSION_VERSION" ] && command -v kwriteconfig5 >/dev/null 2>&1; then
            kwriteconfig5 --file "$shortcut_file" --group "Desktop Entry" --key "X-KDE-Trusted" true
        fi

        print_success "Desktop-Verknüpfung erstellt"
    else
        print_status "Desktop-Verzeichnis nicht gefunden - übersprungen"
    fi
}

check_path() {
    print_status "Überprüfe \$PATH..."

    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        print_warning "\$HOME/.local/bin ist nicht in \$PATH"
        echo
        echo "📋 Füge folgende Zeile zu deiner ~/.bashrc oder ~/.zshrc hinzu:"
        echo "   export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo
        echo "🔄 Oder führe aus:"
        echo "   echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc"
        echo "   source ~/.bashrc"
        echo

        read -p "Automatisch zu ~/.bashrc hinzufügen? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if ! grep -q "HOME/.local/bin" ~/.bashrc 2>/dev/null; then
                echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
                print_success "PATH zu ~/.bashrc hinzugefügt"
                print_warning "Starte Terminal neu oder führe aus: source ~/.bashrc"
            else
                print_status "PATH bereits in ~/.bashrc"
            fi
        fi
    else
        print_success "\$PATH ist korrekt konfiguriert"
    fi
}

run_post_install() {
    print_status "Führe Post-Installation Checks durch..."

    # Test installation
    if "$BIN_LINK" --check-deps &>/dev/null; then
        print_success "Installation erfolgreich getestet"
    else
        print_warning "Installation test fehlgeschlagen - Tool sollte aber funktionieren"
    fi

    # Check optional dependencies
    print_status "Überprüfe optionale Abhängigkeiten..."

    optional_deps=(
        "flatpak:Universal package manager"
        "yay:AUR helper"
        "paru:Alternative AUR helper"
        "reflector:Mirror optimization"
    )

    for dep_info in "${optional_deps[@]}"; do
        dep=$(echo "$dep_info" | cut -d: -f1)
        desc=$(echo "$dep_info" | cut -d: -f2)

        if command -v "$dep" >/dev/null 2>&1; then
            print_success "$dep ist verfügbar ($desc)"
        else
            print_warning "$dep nicht gefunden ($desc) - optional"
        fi
    done
}

show_completion_info() {
    echo
    print_success "🎉 Arch Appcenter erfolgreich installiert!"
    echo
    echo "📍 Installation:"
    echo "   • Programm: $INSTALL_DIR"
    echo "   • Kommando: $BIN_LINK"
    echo "   • Desktop: $DESKTOP_FILE"
    echo
    echo "🚀 Verwendung:"
    echo "   • Anwendungsmenü: Suche nach 'Arch Appcenter'"
    echo "   • Desktop: Doppelklick auf Verknüpfung"
    echo "   • Terminal: '$BIN_LINK'"
    echo
    echo "🔧 Verfügbare Kommandos:"
    echo "   • $APP_NAME --check-deps       - Prüfe Abhängigkeiten"
    echo "   • $APP_NAME --reset-config     - Reset Konfiguration"
    echo "   • ${APP_NAME}-uninstall        - Deinstalliere Tool"
    echo
    echo "📚 Support:"
    echo "   GitHub: $REPO_URL"
    echo "   Issues: $REPO_URL/issues"
    echo
}

main() {
    print_banner

    print_status "Starte Benutzer-Installation von Arch Appcenter..."
    echo

    check_system
    check_dependencies
    create_directories
    download_and_install
    create_desktop_integration
    create_uninstall_script
    create_kde_desktop_shortcut
    run_post_install
    show_completion_info
}

# Handle command line arguments
case "${1:-}" in
    --help)
        echo "Arch Appcenter User Installer v2.0"
        echo
        echo "Diese Installation erfolgt OHNE root-Rechte!"
        echo
        echo "Installation in:"
        echo "  • Programm: ~/.local/share/arch-appcenter"
        echo "  • Kommando: ~/.local/bin/arch-appcenter"
        echo "  • Desktop: ~/.local/share/applications/"
        echo
        echo "Verwendung:"
        echo "  curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/install.sh | bash"
        echo
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac
