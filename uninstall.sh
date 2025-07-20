#!/bin/bash
# Arch Appcenter User Uninstaller v2.0
# Entfernt Arch Appcenter aus Benutzer-Verzeichnissen (ohne root)
# Verwendung: curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/uninstall.sh | bash

set -e

APP_NAME="arch-appcenter"
APP_DISPLAY_NAME="Arch Appcenter"

# ✅ BENUTZER-VERZEICHNISSE (kein root erforderlich)
INSTALL_DIR="$HOME/.local/share/$APP_NAME"
BIN_DIR="$HOME/.local/bin"
BIN_LINK="$BIN_DIR/$APP_NAME"
DESKTOP_DIR="$HOME/.local/share/applications"
DESKTOP_FILE="$DESKTOP_DIR/$APP_NAME.desktop"
UNINSTALL_SCRIPT="$BIN_DIR/${APP_NAME}-uninstall"

# Zusätzliche Benutzer-Dateien
CONFIG_DIR="$HOME/.config/$APP_NAME"
CACHE_DIR="$HOME/.cache/$APP_NAME"
DESKTOP_SHORTCUT="$HOME/Desktop/$APP_NAME.desktop"
DATA_DIR="$HOME/.local/share/$APP_NAME"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
PURPLE='\033[0;35m'
NC='\033[0m'

print_banner() {
    echo -e "${RED}"
    echo "╔══════════════════════════════════════╗"
    echo "║       Arch Appcenter Uninstaller    ║"
    echo "║         (User Uninstall)            ║"
    echo "║              v2.0.0                  ║"
    echo "╚══════════════════════════════════════╝"
    echo -e "${NC}"
}

print_status() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

check_installation() {
    print_status "Überprüfe Installation..."

    # Check if running as root
    if [[ $EUID -eq 0 ]]; then
        print_error "Bitte NICHT als root ausführen!"
        print_error "Dies ist ein Benutzer-Uninstaller für Benutzer-Installation"
        exit 1
    fi

    # Check if installed
    local found=false
    local components=()

    if [ -d "$INSTALL_DIR" ]; then
        found=true
        components+=("Hauptverzeichnis")
    fi

    if [ -f "$BIN_LINK" ]; then
        found=true
        components+=("Ausführbare Datei")
    fi

    if [ -f "$DESKTOP_FILE" ]; then
        found=true
        components+=("Desktop-Eintrag")
    fi

    if [ -d "$CONFIG_DIR" ] || [ -d "$CACHE_DIR" ] || [ -d "$DATA_DIR" ]; then
        found=true
        components+=("Benutzerdaten")
    fi

    if [ "$found" = false ]; then
        print_error "Arch Appcenter ist nicht installiert oder wurde bereits entfernt"
        echo
        echo "🔍 Geprüfte Pfade:"
        echo "   • $INSTALL_DIR"
        echo "   • $BIN_LINK"
        echo "   • $DESKTOP_FILE"
        echo "   • $CONFIG_DIR"
        echo
        exit 1
    fi

    print_success "Installation gefunden: ${components[*]}"
}

show_installed_components() {
    print_status "Gefundene Komponenten:"

    components=(
        "$INSTALL_DIR:Hauptverzeichnis"
        "$BIN_LINK:Ausführbare Datei"
        "$DESKTOP_FILE:Desktop-Eintrag"
        "$UNINSTALL_SCRIPT:Uninstaller"
        "$DESKTOP_SHORTCUT:Desktop-Verknüpfung"
        "$CONFIG_DIR:Konfiguration"
        "$CACHE_DIR:Cache-Daten"
        "$DATA_DIR:Anwendungsdaten"
    )

    for component in "${components[@]}"; do
        path=$(echo "$component" | cut -d: -f1)
        desc=$(echo "$component" | cut -d: -f2)

        if [ -e "$path" ]; then
            size=""
            if [ -d "$path" ]; then
                size=" ($(du -sh "$path" 2>/dev/null | cut -f1))"
            elif [ -f "$path" ]; then
                size=" ($(du -h "$path" 2>/dev/null | cut -f1))"
            fi
            echo -e "   ${GREEN}✓${NC} $desc$size"
            echo -e "     ${BLUE}→${NC} $path"
        else
            echo -e "   ${YELLOW}✗${NC} $desc (nicht gefunden)"
        fi
    done
}

confirm_uninstall() {
    if [ "$1" = "--force" ] || [ "$1" = "-f" ]; then
        return 0
    fi

    echo
    echo -e "${YELLOW}⚠️  Warnung:${NC} Dies wird Arch Appcenter vollständig entfernen."
    echo
    echo "Folgende Aktionen werden durchgeführt:"
    echo "  • Beenden aller laufenden Instanzen"
    echo "  • Entfernen aller Programmdateien"
    echo "  • Entfernen der Desktop-Integration"
    echo "  • Aufräumen der Benutzer-Verzeichnisse"
    echo "  • Optional: Entfernen von Benutzerdaten"
    echo

    read -p "Möchten Sie fortfahren? (y/N): " -n 1 -r
    echo

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        print_status "Deinstallation abgebrochen"
        exit 0
    fi
}

stop_running_instances() {
    print_status "Überprüfe laufende Instanzen..."

    # Verschiedene Möglichkeiten wie der Prozess laufen könnte
    process_patterns=(
        "arch-appcenter"
        "$HOME/.local/bin/arch-appcenter"
        "$HOME/.local/share/arch-appcenter/main.py"
        "python.*arch-appcenter"
        "python.*main.py.*arch-appcenter"
    )

    local found_processes=false

    for pattern in "${process_patterns[@]}"; do
        if pgrep -f "$pattern" >/dev/null 2>&1; then
            found_processes=true
            print_warning "Gefundene Prozesse für: $pattern"
        fi
    done

    if [ "$found_processes" = true ]; then
        print_status "Beende laufende Instanzen..."

        # Graceful shutdown attempt
        for pattern in "${process_patterns[@]}"; do
            pkill -TERM -f "$pattern" 2>/dev/null || true
        done

        sleep 3

        # Force kill if still running
        local still_running=false
        for pattern in "${process_patterns[@]}"; do
            if pgrep -f "$pattern" >/dev/null 2>&1; then
                still_running=true
                break
            fi
        done

        if [ "$still_running" = true ]; then
            print_warning "Erzwinge Beendigung..."
            for pattern in "${process_patterns[@]}"; do
                pkill -KILL -f "$pattern" 2>/dev/null || true
            done
            sleep 1
        fi

        print_success "Instanzen beendet"
    else
        print_status "Keine laufenden Instanzen gefunden"
    fi
}

remove_application_files() {
    print_status "Entferne Anwendungs-Dateien..."

    # Hauptdateien
    app_files=(
        "$INSTALL_DIR"
        "$BIN_LINK"
        "$DESKTOP_FILE"
        "$UNINSTALL_SCRIPT"
        "$DESKTOP_SHORTCUT"
    )

    for file in "${app_files[@]}"; do
        if [ -e "$file" ]; then
            print_status "Entferne: $file"
            rm -rf "$file" 2>/dev/null || {
                print_warning "Konnte $file nicht entfernen"
            }
        fi
    done

    print_success "Anwendungs-Dateien entfernt"
}

handle_user_data() {
    print_status "Verarbeite Benutzerdaten..."

    user_data_dirs=(
        "$CONFIG_DIR:Konfigurationsdateien"
        "$CACHE_DIR:Cache-Daten"
        "$DATA_DIR:Anwendungsdaten"
    )

    local keep_data=false

    # Check if any user data exists
    local has_user_data=false
    for dir_info in "${user_data_dirs[@]}"; do
        dir=$(echo "$dir_info" | cut -d: -f1)
        if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
            has_user_data=true
            break
        fi
    done

    if [ "$has_user_data" = true ]; then
        echo
        echo "📁 Gefundene Benutzerdaten:"

        for dir_info in "${user_data_dirs[@]}"; do
            dir=$(echo "$dir_info" | cut -d: -f1)
            desc=$(echo "$dir_info" | cut -d: -f2)

            if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
                size=$(du -sh "$dir" 2>/dev/null | cut -f1)
                echo "   • $desc: $dir ($size)"
            fi
        done

        echo
        read -p "Alle Benutzerdaten entfernen? (y/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for dir_info in "${user_data_dirs[@]}"; do
                dir=$(echo "$dir_info" | cut -d: -f1)
                desc=$(echo "$dir_info" | cut -d: -f2)

                if [ -d "$dir" ]; then
                    print_status "Entferne $desc: $dir"
                    rm -rf "$dir"
                fi
            done
            print_success "Alle Benutzerdaten entfernt"
        else
            print_status "Benutzerdaten beibehalten"
            keep_data=true
        fi
    else
        print_status "Keine Benutzerdaten gefunden"
    fi

    # Remove empty parent directories if no data kept
    if [ "$keep_data" = false ]; then
        # Try to remove parent dirs if empty
        rmdir "$HOME/.local/share" 2>/dev/null || true
        rmdir "$HOME/.local" 2>/dev/null || true
        rmdir "$HOME/.config" 2>/dev/null || true
        rmdir "$HOME/.cache" 2>/dev/null || true
    fi
}

cleanup_shell_integration() {
    print_status "Bereinige Shell-Integration..."

    # Check if PATH was modified
    shell_files=(
        "$HOME/.bashrc"
        "$HOME/.zshrc"
        "$HOME/.profile"
        "$HOME/.bash_profile"
    )

    local found_path_modifications=false

    for shell_file in "${shell_files[@]}"; do
        if [ -f "$shell_file" ] && grep -q "HOME/.local/bin" "$shell_file" 2>/dev/null; then
            found_path_modifications=true
            echo "   • Gefunden in: $shell_file"
        fi
    done

    if [ "$found_path_modifications" = true ]; then
        echo
        read -p "PATH-Modifikationen in Shell-Dateien entfernen? (y/N): " -n 1 -r
        echo

        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for shell_file in "${shell_files[@]}"; do
                if [ -f "$shell_file" ]; then
                    # Backup erstellen
                    cp "$shell_file" "${shell_file}.backup-$(date +%Y%m%d)"

                    # Entferne Zeilen mit .local/bin PATH export
                    grep -v 'export PATH.*\.local/bin' "$shell_file" > "${shell_file}.tmp" && mv "${shell_file}.tmp" "$shell_file"

                    print_status "Bereinigt: $shell_file"
                fi
            done
            print_success "Shell-Integration bereinigt"
            print_warning "Starte Terminal neu um Änderungen zu übernehmen"
        else
            print_status "Shell-Integration beibehalten"
        fi
    else
        print_status "Keine Shell-Modifikationen gefunden"
    fi
}

update_system_databases() {
    print_status "Aktualisiere Desktop-Datenbank..."

    # Update user's desktop database
    if command -v update-desktop-database >/dev/null 2>&1; then
        update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
        print_status "Desktop-Datenbank aktualisiert"
    fi

    # Update icon cache if needed
    if command -v gtk-update-icon-cache >/dev/null 2>&1; then
        gtk-update-icon-cache -f "$HOME/.local/share/icons/hicolor/" 2>/dev/null || true
        print_status "Icon-Cache aktualisiert"
    fi

    # Update KDE cache if in KDE
    if [ -n "$KDE_SESSION_VERSION" ] && command -v kbuildsycoca5 >/dev/null 2>&1; then
        kbuildsycoca5 --noincremental 2>/dev/null || true
        print_status "KDE-Cache aktualisiert"
    fi

    print_success "System-Datenbanken aktualisiert"
}

show_completion() {
    echo
    print_success "🗑️ Arch Appcenter wurde erfolgreich deinstalliert!"
    echo
    echo "📋 Entfernte Komponenten:"
    echo "   • Programm-Verzeichnis: $INSTALL_DIR"
    echo "   • Ausführbare Datei: $BIN_LINK"
    echo "   • Desktop-Eintrag: $DESKTOP_FILE"
    echo "   • Desktop-Verknüpfung: $DESKTOP_SHORTCUT"
    echo "   • Uninstaller: $UNINSTALL_SCRIPT"
    echo

    # Show what was kept (if anything)
    kept_items=()

    if [ -d "$CONFIG_DIR" ]; then
        kept_items+=("Konfiguration: $CONFIG_DIR")
    fi

    if [ -d "$CACHE_DIR" ]; then
        kept_items+=("Cache: $CACHE_DIR")
    fi

    if [ -d "$DATA_DIR" ]; then
        kept_items+=("Daten: $DATA_DIR")
    fi

    if [ ${#kept_items[@]} -gt 0 ]; then
        echo "📦 Beibehaltene Dateien:"
        for item in "${kept_items[@]}"; do
            echo "   • $item"
        done
        echo
        echo "💡 Diese können Sie manuell entfernen falls gewünscht"
        echo
    fi

    echo "📝 Hinweise:"
    echo "   • System-Abhängigkeiten (Python, Qt) bleiben installiert"
    echo "   • Desktop-Datenbanken wurden aktualisiert"
    echo "   • Shell-Konfiguration wurde optional bereinigt"
    echo
    echo "🙏 Vielen Dank, dass Sie Arch Appcenter verwendet haben!"
    echo
    echo "📚 Bei Problemen oder Feedback:"
    echo "   GitHub: https://github.com/tobayashi-san/arch-appcenter/issues"
    echo
}

# Recovery function for partial installations
cleanup_partial_installation() {
    print_status "Bereinige unvollständige Installation..."

    # Look for any remaining traces in user directories
    search_dirs=(
        "$HOME/.local/bin"
        "$HOME/.local/share/applications"
        "$HOME/.local/share"
        "$HOME/.config"
        "$HOME/.cache"
        "$HOME/Desktop"
    )

    for search_dir in "${search_dirs[@]}"; do
        if [ -d "$search_dir" ]; then
            find "$search_dir" -name "*arch-appcenter*" -type f 2>/dev/null | while read -r file; do
                print_status "Entferne verwaiste Datei: $file"
                rm -f "$file"
            done

            find "$search_dir" -name "*arch-appcenter*" -type d -empty 2>/dev/null | while read -r dir; do
                print_status "Entferne leeres Verzeichnis: $dir"
                rmdir "$dir" 2>/dev/null || true
            done
        fi
    done

    print_success "Bereinigung abgeschlossen"
}

show_help() {
    echo "Arch Appcenter User Uninstaller v2.0"
    echo
    echo "Entfernt Arch Appcenter aus Benutzer-Verzeichnissen (ohne root-Rechte)"
    echo
    echo "Verwendung:"
    echo "  $0 [OPTION]"
    echo
    echo "Optionen:"
    echo "  --force, -f    Keine Bestätigung erforderlich"
    echo "  --cleanup      Bereinige unvollständige Installation"
    echo "  --help, -h     Zeige diese Hilfe"
    echo
    echo "Online-Verwendung:"
    echo "  curl -sSL https://raw.githubusercontent.com/tobayashi-san/arch-appcenter/main/uninstall.sh | bash"
    echo
    echo "Was wird entfernt:"
    echo "  • $HOME/.local/share/arch-appcenter (Programm)"
    echo "  • $HOME/.local/bin/arch-appcenter (Kommando)"
    echo "  • $HOME/.local/share/applications/arch-appcenter.desktop (Desktop-Eintrag)"
    echo "  • $HOME/Desktop/arch-appcenter.desktop (Desktop-Verknüpfung)"
    echo "  • Optional: Benutzerdaten und Konfiguration"
    echo
}

main() {
    print_banner

    # Handle command line arguments first
    case "${1:-}" in
        --help|-h)
            show_help
            exit 0
            ;;
        --cleanup)
            cleanup_partial_installation
            update_system_databases
            print_success "Bereinigung abgeschlossen"
            exit 0
            ;;
    esac

    print_status "Starte Deinstallation von Arch Appcenter..."
    echo

    check_installation
    show_installed_components
    confirm_uninstall "$1"
    stop_running_instances
    remove_application_files
    handle_user_data
    cleanup_shell_integration
    update_system_databases
    show_completion
}

main "$@"
