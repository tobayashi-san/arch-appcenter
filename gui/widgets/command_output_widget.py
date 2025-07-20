"""
Command Output Widget - Shows real-time command execution output
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollBar, QTabWidget, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor, QTextCharFormat
from datetime import datetime

class CommandOutputWidget(QWidget):
    """Enhanced command output widget with tabs and filtering"""

    def __init__(self):
        super().__init__()
        self.output_buffer = []
        self.max_lines = 1000
        self.auto_scroll = True
        self.setup_ui()

    def setup_ui(self):
        """Setup command output UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = self.create_header()
        layout.addWidget(header)

        # Content with tabs
        content = self.create_content()
        layout.addWidget(content, 1)

        self.setLayout(layout)

    def create_header(self):
        """Create output widget header"""
        header = QFrame()
        header.setObjectName("outputHeader")
        header.setStyleSheet("""
            QFrame#outputHeader {
                background-color: #f8f9fa;
                border-bottom: 1px solid #dee2e6;
                padding: 8px 16px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Title
        title = QLabel("📟 Command Output")
        title.setStyleSheet("font-size: 14px; font-weight: 600; color: #495057;")
        layout.addWidget(title)

        layout.addStretch()

        # Auto-scroll toggle
        self.autoscroll_btn = QPushButton("🔒 Auto-scroll")
        self.autoscroll_btn.setCheckable(True)
        self.autoscroll_btn.setChecked(True)
        self.autoscroll_btn.setObjectName("toggleButton")
        self.autoscroll_btn.clicked.connect(self.toggle_autoscroll)
        layout.addWidget(self.autoscroll_btn)

        # Clear button
        clear_btn = QPushButton("🗑️ Clear")
        clear_btn.setObjectName("clearButton")
        clear_btn.clicked.connect(self.clear)
        layout.addWidget(clear_btn)

        # Hide button
        hide_btn = QPushButton("📋 Hide")
        hide_btn.setObjectName("hideButton")
        hide_btn.clicked.connect(self.hide)
        layout.addWidget(hide_btn)

        header.setLayout(layout)
        return header

    def create_content(self):
        """Create content area with tabs"""
        self.tab_widget = QTabWidget()
        self.tab_widget.setObjectName("outputTabs")

        # Combined output tab
        self.combined_output = self.create_output_text_edit("combined")
        self.tab_widget.addTab(self.combined_output, "📟 All Output")

        # Stdout tab
        self.stdout_output = self.create_output_text_edit("stdout")
        self.tab_widget.addTab(self.stdout_output, "✅ Standard Out")

        # Stderr tab
        self.stderr_output = self.create_output_text_edit("stderr")
        self.tab_widget.addTab(self.stderr_output, "❌ Errors")

        # Apply tab styling
        self.tab_widget.setStyleSheet("""
            QTabWidget#outputTabs::pane {
                border: none;
                background-color: #1e1e1e;
            }

            QTabWidget#outputTabs QTabBar::tab {
                background-color: #2d2d2d;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                margin-right: 2px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-size: 12px;
                font-weight: 600;
            }

            QTabWidget#outputTabs QTabBar::tab:selected {
                background-color: #1e1e1e;
                color: #4fc3f7;
            }

            QTabWidget#outputTabs QTabBar::tab:hover:!selected {
                background-color: #404040;
            }
        """)

        return self.tab_widget

    def create_output_text_edit(self, output_type):
        """Create styled text edit for output"""
        text_edit = QTextEdit()
        text_edit.setObjectName(f"output_{output_type}")
        text_edit.setReadOnly(True)
        text_edit.setFont(QFont("Consolas", 10))

        # Terminal-like styling
        text_edit.setStyleSheet(f"""
            QTextEdit#output_{output_type} {{
                background-color: #1e1e1e;
                color: #ffffff;
                border: none;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 11px;
                line-height: 1.4;
            }}
        """)

        return text_edit

    def append_output(self, output_type, text):
        """Append output text with proper formatting"""
        if not text.strip():
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Format output line
        if output_type == "stdout":
            formatted_line = f"[{timestamp}] {text}"
            color = "#4fc3f7"  # Light blue
        elif output_type == "stderr":
            formatted_line = f"[{timestamp}] ERROR: {text}"
            color = "#f48fb1"  # Light red
        else:
            formatted_line = f"[{timestamp}] {text}"
            color = "#ffffff"  # White

        # Add to combined output
        self.append_to_text_edit(self.combined_output, formatted_line, color)

        # Add to specific output tab
        if output_type == "stdout":
            self.append_to_text_edit(self.stdout_output, formatted_line, color)
        elif output_type == "stderr":
            self.append_to_text_edit(self.stderr_output, formatted_line, color)

        # Store in buffer
        self.output_buffer.append({
            'timestamp': timestamp,
            'type': output_type,
            'text': text,
            'formatted': formatted_line
        })

        # Limit buffer size
        if len(self.output_buffer) > self.max_lines:
            self.output_buffer = self.output_buffer[-self.max_lines:]

        # Update tab titles with counters
        self.update_tab_counters()

    def append_to_text_edit(self, text_edit, text, color):
        """Append formatted text to text edit"""
        cursor = text_edit.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Set text color
        format = QTextCharFormat()
        format.setForeground(QColor(color))
        cursor.setCharFormat(format)

        # Insert text
        cursor.insertText(text + "\n")

        # Auto-scroll if enabled
        if self.auto_scroll:
            scrollbar = text_edit.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())

    def update_tab_counters(self):
        """Update tab titles with line counters"""
        total_lines = len(self.output_buffer)
        stdout_lines = len([item for item in self.output_buffer if item['type'] == 'stdout'])
        stderr_lines = len([item for item in self.output_buffer if item['type'] == 'stderr'])

        self.tab_widget.setTabText(0, f"📟 All Output ({total_lines})")
        self.tab_widget.setTabText(1, f"✅ Standard Out ({stdout_lines})")
        self.tab_widget.setTabText(2, f"❌ Errors ({stderr_lines})")

        # Highlight error tab if there are errors
        if stderr_lines > 0:
            self.tab_widget.setTabText(2, f"❌ Errors ({stderr_lines}) ⚠️")

    def toggle_autoscroll(self):
        """Toggle auto-scroll functionality"""
        self.auto_scroll = self.autoscroll_btn.isChecked()

        if self.auto_scroll:
            self.autoscroll_btn.setText("🔒 Auto-scroll")
            # Scroll to bottom
            for text_edit in [self.combined_output, self.stdout_output, self.stderr_output]:
                scrollbar = text_edit.verticalScrollBar()
                scrollbar.setValue(scrollbar.maximum())
        else:
            self.autoscroll_btn.setText("🔓 Manual scroll")

    def clear(self):
        """Clear all output"""
        self.combined_output.clear()
        self.stdout_output.clear()
        self.stderr_output.clear()
        self.output_buffer.clear()

        # Reset tab titles
        self.tab_widget.setTabText(0, "📟 All Output")
        self.tab_widget.setTabText(1, "✅ Standard Out")
        self.tab_widget.setTabText(2, "❌ Errors")

        # Add clear message
        timestamp = datetime.now().strftime("%H:%M:%S")
        clear_msg = f"[{timestamp}] === Output cleared ==="
        self.append_to_text_edit(self.combined_output, clear_msg, "#666666")

    def get_output_text(self, output_type="combined"):
        """Get output text for export"""
        if output_type == "combined":
            return self.combined_output.toPlainText()
        elif output_type == "stdout":
            return self.stdout_output.toPlainText()
        elif output_type == "stderr":
            return self.stderr_output.toPlainText()
        else:
            return ""

    def save_output_to_file(self, filename, output_type="combined"):
        """Save output to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(self.get_output_text(output_type))
            return True
        except Exception as e:
            print(f"Failed to save output: {e}")
            return False

class CompactOutputWidget(QWidget):
    """Compact version of output widget for minimal space"""

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.setMaximumHeight(150)

    def setup_ui(self):
        """Setup compact output UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(4)

        # Header
        header_layout = QHBoxLayout()
        header_layout.setSpacing(8)

        title = QLabel("📟 Output")
        title.setStyleSheet("font-size: 12px; font-weight: 600; color: #495057;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        clear_btn = QPushButton("Clear")
        clear_btn.setFixedSize(60, 24)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #6c757d;
                color: white;
                border: none;
                border-radius: 4px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #5a6268;
            }
        """)
        clear_btn.clicked.connect(self.clear)
        header_layout.addWidget(clear_btn)

        layout.addLayout(header_layout)

        # Output area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setFont(QFont("Consolas", 9))
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 4px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.output_area, 1)
        self.setLayout(layout)

    def append_output(self, output_type, text):
        """Append output (simplified)"""
        if not text.strip():
            return

        timestamp = datetime.now().strftime("%H:%M:%S")

        # Color coding
        if output_type == "stderr":
            color_code = "\033[91m"  # Red
            prefix = "ERROR: "
        else:
            color_code = "\033[92m"  # Green
            prefix = ""

        formatted_text = f"[{timestamp}] {prefix}{text}"

        cursor = self.output_area.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)

        # Set color based on type
        format = QTextCharFormat()
        if output_type == "stderr":
            format.setForeground(QColor("#f48fb1"))
        else:
            format.setForeground(QColor("#4fc3f7"))

        cursor.setCharFormat(format)
        cursor.insertText(formatted_text + "\n")

        # Auto-scroll
        scrollbar = self.output_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def clear(self):
        """Clear output"""
        self.output_area.clear()

        # Add timestamp for clear action
        timestamp = datetime.now().strftime("%H:%M:%S")
        cursor = self.output_area.textCursor()
        format = QTextCharFormat()
        format.setForeground(QColor("#666666"))
        cursor.setCharFormat(format)
        cursor.insertText(f"[{timestamp}] === Output cleared ===\n")

class LogViewerWidget(QWidget):
    """Advanced log viewer with search and filtering"""

    def __init__(self):
        super().__init__()
        self.log_entries = []
        self.filtered_entries = []
        self.search_term = ""
        self.filter_level = "all"
        self.setup_ui()

    def setup_ui(self):
        """Setup log viewer UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Search and filter bar
        filter_bar = self.create_filter_bar()
        layout.addWidget(filter_bar)

        # Log display
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 10))
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #ffffff;
                border: 1px solid #404040;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 10px;
            }
        """)

        layout.addWidget(self.log_display, 1)
        self.setLayout(layout)

    def create_filter_bar(self):
        """Create search and filter bar"""
        bar = QFrame()
        bar.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 4px;
                padding: 4px;
            }
        """)

        layout = QHBoxLayout()
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Search input
        from PyQt6.QtWidgets import QLineEdit
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search logs...")
        self.search_input.textChanged.connect(self.on_search_changed)
        self.search_input.setStyleSheet("""
            QLineEdit {
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 4px;
                background-color: white;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.search_input, 1)

        # Filter buttons
        filter_buttons = [
            ("All", "all"),
            ("Info", "info"),
            ("Warning", "warning"),
            ("Error", "error")
        ]

        for text, level in filter_buttons:
            btn = QPushButton(text)
            btn.setCheckable(True)
            btn.setChecked(level == "all")
            btn.clicked.connect(lambda checked, l=level: self.set_filter_level(l))
            btn.setStyleSheet("""
                QPushButton {
                    padding: 4px 12px;
                    border: 1px solid #ced4da;
                    border-radius: 4px;
                    background-color: white;
                    font-size: 11px;
                    font-weight: 600;
                }
                QPushButton:checked {
                    background-color: #4f46e5;
                    color: white;
                    border-color: #4f46e5;
                }
                QPushButton:hover {
                    background-color: #e9ecef;
                }
                QPushButton:checked:hover {
                    background-color: #3730a3;
                }
            """)
            layout.addWidget(btn)

        bar.setLayout(layout)
        return bar

    def on_search_changed(self, text):
        """Handle search term change"""
        self.search_term = text.lower()
        self.update_display()

    def set_filter_level(self, level):
        """Set filter level"""
        self.filter_level = level

        # Update button states
        parent = self.sender().parent()
        for btn in parent.findChildren(QPushButton):
            btn.setChecked(False)

        self.sender().setChecked(True)
        self.update_display()

    def add_log_entry(self, level, message, timestamp=None):
        """Add log entry"""
        if timestamp is None:
            timestamp = datetime.now()

        entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }

        self.log_entries.append(entry)

        # Limit entries
        if len(self.log_entries) > 1000:
            self.log_entries = self.log_entries[-1000:]

        self.update_display()

    def update_display(self):
        """Update log display with filtering"""
        # Filter entries
        self.filtered_entries = []

        for entry in self.log_entries:
            # Level filter
            if self.filter_level != "all" and entry['level'] != self.filter_level:
                continue

            # Search filter
            if self.search_term and self.search_term not in entry['message'].lower():
                continue

            self.filtered_entries.append(entry)

        # Update display
        self.log_display.clear()

        for entry in self.filtered_entries:
            timestamp_str = entry['timestamp'].strftime("%H:%M:%S")
            level = entry['level'].upper()
            message = entry['message']

            # Color coding
            if entry['level'] == 'error':
                color = "#f48fb1"
            elif entry['level'] == 'warning':
                color = "#ffb74d"
            elif entry['level'] == 'info':
                color = "#4fc3f7"
            else:
                color = "#ffffff"

            formatted_line = f"[{timestamp_str}] {level}: {message}"

            cursor = self.log_display.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.End)

            format = QTextCharFormat()
            format.setForeground(QColor(color))
            cursor.setCharFormat(format)
            cursor.insertText(formatted_line + "\n")

        # Auto-scroll
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
