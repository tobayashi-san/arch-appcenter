"""
Category Widget - Production Version
Clean, modern design without debug output
"""

import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QScrollArea, QFrame, QMessageBox, QGridLayout,
    QButtonGroup
)
from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QFont, QColor

class ToolCard(QFrame):
    """Modern tool card with clean design"""

    tool_selected = pyqtSignal(object)
    selection_changed = pyqtSignal(object, bool)

    def __init__(self, tool):
        super().__init__()
        self.tool = tool
        self.is_selected = False
        self.is_hovered = False
        self.setup_ui()
        self.setup_animations()

    def setup_ui(self):
        """Setup tool card UI with modern design"""
        self.setMinimumHeight(100)
        self.setMinimumWidth(250)
        self.setObjectName("toolCard")
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(5)

        # Header with checkbox and tool name
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Selection checkbox
        self.checkbox = QCheckBox()
        self.checkbox.setObjectName("toolCheckbox")
        self.checkbox.stateChanged.connect(self.on_selection_changed)
        header_layout.addWidget(self.checkbox)

        # Tool name
        self.title_label = QLabel(self.tool.name)
        self.title_label.setObjectName("toolTitle")
        self.title_label.setWordWrap(True)
        header_layout.addWidget(self.title_label, 1)

        # Execute button
        self.exec_btn = QPushButton("Execute")
        self.exec_btn.setObjectName("executeButton")
        self.exec_btn.setToolTip("Execute this tool")
        self.exec_btn.clicked.connect(lambda: self.tool_selected.emit(self.tool))
        header_layout.addWidget(self.exec_btn)

        layout.addLayout(header_layout)

        # Description
        self.desc_label = QLabel(self.tool.description)
        self.desc_label.setObjectName("toolDescription")
        self.desc_label.setWordWrap(True)
        self.desc_label.setMaximumHeight(40)
        layout.addWidget(self.desc_label)

        # Command preview
        cmd_preview = self.tool.command
        if len(cmd_preview) > 70:
            cmd_preview = cmd_preview[:67] + "..."

        self.cmd_label = QLabel(f"{cmd_preview}")
        self.cmd_label.setObjectName("commandPreview")
        layout.addWidget(self.cmd_label)

        # Tags and category info
        footer_layout = QHBoxLayout()
        footer_layout.setSpacing(5)

        # Tags (show max 3)
        if hasattr(self.tool, 'tags') and self.tool.tags:
            tags_to_show = self.tool.tags[:3]
            for tag in tags_to_show:
                tag_label = QLabel(f"#{tag}")
                tag_label.setObjectName("toolTag")
                footer_layout.addWidget(tag_label)

            if len(self.tool.tags) > 3:
                more_label = QLabel(f"+{len(self.tool.tags) - 3}")
                more_label.setObjectName("moreTagsLabel")
                footer_layout.addWidget(more_label)

        footer_layout.addStretch()

        # Category indicator
        if hasattr(self.tool, 'category'):
            category_label = QLabel(f"📂 {self.tool.category}")
            category_label.setObjectName("categoryLabel")
            footer_layout.addWidget(category_label)

        layout.addLayout(footer_layout)
        self.setLayout(layout)


    def setup_animations(self):
        """Setup hover animations"""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(150)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)



    def on_selection_changed(self, state):
        """Handle selection state change"""
        self.is_selected = state == Qt.CheckState.Checked.value
        self.selection_changed.emit(self.tool, self.is_selected)

    def set_selected(self, selected):
        """Programmatically set selection state"""
        self.checkbox.setChecked(selected)

    def enterEvent(self, event):
        """Mouse enter event"""
        self.is_hovered = True
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Mouse leave event"""
        self.is_hovered = False
        super().leaveEvent(event)

class CategoryWidget(QWidget):
    """Modern category widget"""

    tool_selected = pyqtSignal(object)
    tools_selected = pyqtSignal(list)

    def __init__(self, category):
        super().__init__()
        self.category = category
        self.selected_tools = {}
        self.tool_cards = []
        self.view_mode = "grid"  # grid or list
        self.setup_ui()

    def setup_ui(self):
        """Setup category widget UI"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(20)

        # Header
        header = self.create_category_header()
        layout.addWidget(header)

        # Control panel
        controls = self.create_enhanced_control_panel()
        layout.addWidget(controls)

        # Tools area
        tools_area = self.create_tools_area()
        layout.addWidget(tools_area, 1)

        self.setLayout(layout)

    def create_category_header(self):
        """Create elegant category header"""
        header = QFrame()
        header.setObjectName("categoryHeader")

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Title row
        title_layout = QHBoxLayout()

        # Category icon and name
        title_text = f"{self.category.icon}  {self.category.name}"
        title = QLabel(title_text)
        title.setObjectName("categoryTitle")

        title_layout.addWidget(title)
        title_layout.addStretch()

        # Tools count badge
        count_badge = QLabel(f"{len(self.category.items)} tools")
        count_badge.setObjectName("countBadge")
        title_layout.addWidget(count_badge)

        layout.addLayout(title_layout)

        # Description
        if self.category.description:
            desc = QLabel(self.category.description)
            desc.setObjectName("categoryDescription")
            desc.setWordWrap(True)
            layout.addWidget(desc)

        header.setLayout(layout)
        return header

    def create_enhanced_control_panel(self):
        """Create enhanced control panel"""
        controls = QFrame()
        controls.setObjectName("controlPanel")

        layout = QVBoxLayout()
        layout.setSpacing(12)

        # Top row: Selection controls and view options
        top_row = QHBoxLayout()
        top_row.setSpacing(12)

        # Selection controls
        selection_group = self.create_selection_controls()
        top_row.addWidget(selection_group)

        top_row.addStretch()

        # View mode toggle
        view_toggle = self.create_view_toggle()
        top_row.addWidget(view_toggle)

        layout.addLayout(top_row)

        # Bottom row: Stats and execute button
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(12)

        # Selection stats
        self.stats_label = QLabel("0 tools selected")
        self.stats_label.setObjectName("selectionStats")
        bottom_row.addWidget(self.stats_label)

        bottom_row.addStretch()

        # Execute button
        self.execute_btn = QPushButton("🚀 Execute Selected Tools")
        self.execute_btn.setObjectName("executeSelectedButton")
        self.execute_btn.setEnabled(False)
        self.execute_btn.clicked.connect(self.execute_selected_tools)
        bottom_row.addWidget(self.execute_btn)

        layout.addLayout(bottom_row)
        controls.setLayout(layout)
        return controls

    def create_selection_controls(self):
        """Create selection control buttons"""
        group = QFrame()
        group.setObjectName("selectionGroup")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Select all button
        select_all_btn = QPushButton("✅ Select All")
        select_all_btn.setObjectName("selectionButton")
        select_all_btn.clicked.connect(self.select_all_tools)

        # Select none button
        select_none_btn = QPushButton("❌ Clear Selection")
        select_none_btn.setObjectName("selectionButton")
        select_none_btn.clicked.connect(self.select_no_tools)

        layout.addWidget(select_all_btn)
        layout.addWidget(select_none_btn)

        group.setLayout(layout)
        return group

    def create_view_toggle(self):
        """Create view mode toggle"""
        toggle_group = QFrame()
        toggle_group.setObjectName("viewToggle")

        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Grid view button
        self.grid_btn = QPushButton("⊞ Grid")
        self.grid_btn.setObjectName("gridViewButton")  # 👈 CSS-Targeting
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(lambda: self.set_view_mode("grid"))

        # List view button
        self.list_btn = QPushButton("☰ List")
        self.list_btn.setObjectName("listViewButton")  # 👈 CSS-Targeting
        self.list_btn.setCheckable(True)
        self.list_btn.clicked.connect(lambda: self.set_view_mode("list"))

        # Button group for exclusive selection
        self.view_button_group = QButtonGroup()
        self.view_button_group.addButton(self.grid_btn)
        self.view_button_group.addButton(self.list_btn)


        layout.addWidget(self.grid_btn)
        layout.addWidget(self.list_btn)
        toggle_group.setLayout(layout)
        return toggle_group

    def create_tools_area(self):
        """Create scrollable tools area"""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("toolsScrollArea")

        # Tools container
        self.tools_container = QWidget()
        self.tools_container.setObjectName("toolsContainer")

        # Initial grid layout
        self.tools_layout = QGridLayout()
        self.tools_layout.setSpacing(10)
        self.tools_layout.setContentsMargins(0, 0, 0, 0)

        # Add tool cards
        self.populate_tools()

        self.tools_container.setLayout(self.tools_layout)
        scroll_area.setWidget(self.tools_container)

        return scroll_area

    def populate_tools(self):
        """Populate tools based on current view mode"""
        # Clear existing cards
        for card in self.tool_cards:
            card.setParent(None)
        self.tool_cards.clear()

        # Create new cards
        for i, tool in enumerate(self.category.items):
            tool_card = ToolCard(tool)
            tool_card.selection_changed.connect(self.on_tool_selection_changed)
            tool_card.tool_selected.connect(self.tool_selected.emit)

            self.tool_cards.append(tool_card)

            # Add to layout based on view mode
            if self.view_mode == "grid":
                row = i // 2  # 2 columns
                col = i % 2
                self.tools_layout.addWidget(tool_card, row, col)
            else:  # list mode
                self.tools_layout.addWidget(tool_card, i, 0, 1, 2)

        # Add stretch at the end
        if self.view_mode == "grid":
            self.tools_layout.setRowStretch(len(self.category.items) // 2 + 1, 1)
        else:
            self.tools_layout.setRowStretch(len(self.category.items), 1)

    def set_view_mode(self, mode):
        """Set view mode (grid or list)"""
        if self.view_mode == mode:
            return

        self.view_mode = mode

        # Update button states
        self.grid_btn.setChecked(mode == "grid")
        self.list_btn.setChecked(mode == "list")

        # Recreate layout
        self.populate_tools()

    def on_tool_selection_changed(self, tool, selected):
        """Handle tool selection change"""
        if selected:
            self.selected_tools[tool.name] = tool
        else:
            self.selected_tools.pop(tool.name, None)

        self.update_selection_ui()

    def update_selection_ui(self):
        """Update selection-related UI elements"""
        count = len(self.selected_tools)
        total = len(self.category.items)

        # Update stats label
        if count == 0:
            self.stats_label.setText("No tools selected")
        elif count == total:
            self.stats_label.setText(f"All {total} tools selected")
        else:
            self.stats_label.setText(f"{count} of {total} tools selected")

        # Update execute button
        self.execute_btn.setEnabled(count > 0)
        if count > 0:
            if count == 1:
                self.execute_btn.setText("🚀 Execute 1 Tool")
            else:
                self.execute_btn.setText(f"🚀 Execute {count} Tools")
        else:
            self.execute_btn.setText("🚀 Execute Selected Tools")

    def select_all_tools(self):
        """Select all tools"""
        for card in self.tool_cards:
            card.set_selected(True)

    def select_no_tools(self):
        """Deselect all tools"""
        for card in self.tool_cards:
            card.set_selected(False)

    def execute_selected_tools(self):
        """Execute selected tools with confirmation"""
        if not self.selected_tools:
            self.show_no_selection_message()
            return

        selected_list = list(self.selected_tools.values())

        # Confirmation dialog
        reply = QMessageBox.question(
            self,
            "Confirm Execution",
            f"Execute {len(selected_list)} selected tools?\n\nThis will run system commands with sudo privileges.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.tools_selected.emit(selected_list)

    def show_no_selection_message(self):
        """Show message when no tools are selected"""
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle("No Selection")
        msg.setText("Please select at least one tool to execute.")
        msg.exec()

    def get_selected_tools(self):
        """Get list of selected tools"""
        return list(self.selected_tools.values())

    def clear_selection(self):
        """Clear all selections"""
        self.select_no_tools()

# Export classes
__all__ = ['CategoryWidget', 'ToolCard']
