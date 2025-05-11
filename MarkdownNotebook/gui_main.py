"""
Main GUI application assembly.
Connects all components: menus, toolbars, note list, editor/viewer.
Handles overall application logic and state.
"""
import sys
import os
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QListWidget, QListWidgetItem, QSplitter, QStatusBar, QMessageBox,
    QFileDialog, QInputDialog, QToolBar, QLabel
)
from PyQt6.QtGui import QAction, QIcon, QKeySequence
from PyQt6.QtCore import Qt, QSize, pyqtSignal

from . import APP_NAME, VERSION
from .file_manager import Note, scan_notes_directory, load_note, save_note, create_new_note, delete_note_file
from .editor import MarkdownEditor
from .viewer import MarkdownViewer
from .search import SearchIndex
from .settings import app_settings
from .utils import get_current_timestamp, format_timestamp_display

# For icons, you might use QStyle standard icons or provide your own in assets/
# from PyQt6.QtGui import QStyle

class SettingsDialog(QDialog): # Basic Settings Dialog
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Application Settings")
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)

        # Notes Folder
        folder_layout = QHBoxLayout()
        self.notes_folder_label = QLabel("Notes Folder:")
        self.notes_folder_edit = QLineEdit(app_settings.get("notes_folder"))
        self.notes_folder_button = QPushButton("Browse...")
        self.notes_folder_button.clicked.connect(self.browse_notes_folder)
        folder_layout.addWidget(self.notes_folder_label)
        folder_layout.addWidget(self.notes_folder_edit)
        folder_layout.addWidget(self.notes_folder_button)
        layout.addLayout(folder_layout)

        # Theme
        theme_layout = QHBoxLayout()
        self.theme_label = QLabel("Theme:")
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setCurrentText(app_settings.get("theme"))
        theme_layout.addWidget(self.theme_label)
        theme_layout.addWidget(self.theme_combo)
        layout.addLayout(theme_layout)
        
        # Font Size
        font_layout = QHBoxLayout()
        self.font_label = QLabel("Editor Font Size:")
        self.font_spinbox = QSpinBox()
        self.font_spinbox.setRange(8, 30)
        self.font_spinbox.setValue(app_settings.get("font_size"))
        font_layout.addWidget(self.font_label)
        font_layout.addWidget(self.font_spinbox)
        layout.addLayout(font_layout)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def browse_notes_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Notes Folder", self.notes_folder_edit.text())
        if folder:
            self.notes_folder_edit.setText(folder)

    def get_settings(self):
        return {
            "notes_folder": self.notes_folder_edit.text(),
            "theme": self.theme_combo.currentText(),
            "font_size": self.font_spinbox.value()
        }

class MainWindow(QMainWindow):
    notes_reloaded_signal = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_note_filepath = None
        self.notes_list_data = [] # Stores Note objects for the list
        self.search_index = SearchIndex()
        self.unsaved_changes = False

        self.init_ui()
        self.load_initial_notes()
        self.apply_settings_to_ui()

        self.notes_reloaded_signal.connect(self.update_note_list_display)
        self.notes_reloaded_signal.connect(self.update_tag_filter_panel)


    def init_ui(self):
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setGeometry(100, 100,
                         app_settings.get("window_width", 1000),
                         app_settings.get("window_height", 700))

        # --- Central Widget and Layout ---
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget) # Main layout for the central widget

        # --- Main Splitter (Note List | Editor/Viewer Area) ---
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left Pane: Note List and Tag Filter
        left_pane_widget = QWidget()
        left_pane_layout = QVBoxLayout(left_pane_widget)
        left_pane_layout.setContentsMargins(0,0,0,0)

        # Search bar for notes
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Search notes (title, tag, content)...")
        self.search_bar.textChanged.connect(self.filter_notes_list)
        left_pane_layout.addWidget(self.search_bar)

        self.notes_list_widget = QListWidget()
        self.notes_list_widget.currentItemChanged.connect(self.on_note_selected)
        left_pane_layout.addWidget(self.notes_list_widget)

        # Tag filter panel
        self.tag_filter_label = QLabel("Filter by Tag:")
        left_pane_layout.addWidget(self.tag_filter_label)
        self.tag_list_widget = QListWidget()
        self.tag_list_widget.setMaximumHeight(150) # Limit height
        self.tag_list_widget.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.tag_list_widget.itemClicked.connect(self.on_tag_filter_selected)
        left_pane_layout.addWidget(self.tag_list_widget)
        
        clear_filter_button = QPushButton("Clear Tag Filter")
        clear_filter_button.clicked.connect(self.clear_tag_filter)
        left_pane_layout.addWidget(clear_filter_button)

        self.main_splitter.addWidget(left_pane_widget)


        # Right Pane: Editor and Preview Splitter
        self.editor_viewer_splitter = QSplitter(Qt.Orientation.Vertical) # Or Horizontal

        self.markdown_editor = MarkdownEditor()
        self.markdown_editor.content_changed.connect(self.on_editor_content_changed)
        self.editor_viewer_splitter.addWidget(self.markdown_editor)

        self.markdown_viewer = MarkdownViewer()
        self.editor_viewer_splitter.addWidget(self.markdown_viewer)

        # Restore splitter sizes for editor/viewer
        editor_splitter_sizes = app_settings.get("splitter_sizes_editor", [350, 350])
        self.editor_viewer_splitter.setSizes(editor_splitter_sizes)


        self.main_splitter.addWidget(self.editor_viewer_splitter)
        main_layout.addWidget(self.main_splitter)

        # Restore main splitter sizes
        main_splitter_sizes = app_settings.get("splitter_sizes_main", [250, 750])
        self.main_splitter.setSizes(main_splitter_sizes)

        # --- Status Bar ---
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.status_label_note_count = QLabel("Notes: 0")
        self.status_label_current_note = QLabel("No note selected")
        self.statusBar.addPermanentWidget(self.status_label_note_count, 1)
        self.statusBar.addPermanentWidget(self.status_label_current_note, 2)

        self.setup_menus_and_toolbar()
        self.show()

    def setup_menus_and_toolbar(self):
        # --- Actions ---
        # File Actions
        new_action = QAction(QIcon.fromTheme("document-new", QIcon(os.path.join("assets", "new.png"))), "&New Note", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.setStatusTip("Create a new note")
        new_action.triggered.connect(self.create_new_note_dialog)

        save_action = QAction(QIcon.fromTheme("document-save", QIcon(os.path.join("assets", "save.png"))), "&Save Note", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.setStatusTip("Save the current note")
        save_action.triggered.connect(self.save_current_note)
        self.save_action = save_action # Keep a reference to enable/disable

        delete_action = QAction(QIcon.fromTheme("edit-delete", QIcon(os.path.join("assets", "delete.png"))), "&Delete Note", self)
        delete_action.setShortcut(QKeySequence.StandardKey.Delete)
        delete_action.setStatusTip("Delete the current note")
        delete_action.triggered.connect(self.delete_current_note)
        self.delete_action = delete_action

        export_html_action = QAction("&Export to HTML", self)
        export_html_action.setStatusTip("Export current note to HTML file")
        export_html_action.triggered.connect(self.export_note_to_html)

        settings_action = QAction(QIcon.fromTheme("preferences-system", QIcon(os.path.join("assets", "settings.png"))), "&Settings", self)
        settings_action.setStatusTip("Application settings")
        settings_action.triggered.connect(self.open_settings_dialog)

        exit_action = QAction(QIcon.fromTheme("application-exit", QIcon(os.path.join("assets", "exit.png"))), "E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        
        # Edit Actions (placeholders for now)
        # undo_action = QAction(QIcon.fromTheme("edit-undo"), "&Undo", self)
        # redo_action = QAction(QIcon.fromTheme("edit-redo"), "&Redo", self)
        # cut_action = QAction(QIcon.fromTheme("edit-cut"), "Cu&t", self)
        # copy_action = QAction(QIcon.fromTheme("edit-copy"), "&Copy", self)
        # paste_action = QAction(QIcon.fromTheme("edit-paste"), "&Paste", self)

        # View Actions
        reload_notes_action = QAction(QIcon.fromTheme("view-refresh", QIcon(os.path.join("assets", "reload.png"))), "&Reload Notes", self)
        reload_notes_action.setShortcut(QKeySequence("F5"))
        reload_notes_action.setStatusTip("Rescan notes folder and refresh list")
        reload_notes_action.triggered.connect(self.load_initial_notes)


        # --- Menu Bar ---
        menubar = self.menuBar()
        file_menu = menubar.addMenu("&File")
        file_menu.addAction(new_action)
        file_menu.addAction(save_action)
        file_menu.addAction(delete_action)
        file_menu.addSeparator()
        file_menu.addAction(export_html_action)
        file_menu.addSeparator()
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        edit_menu = menubar.addMenu("&Edit")
        # Add undo/redo etc. if editor supports it or manage globally
        # edit_menu.addAction(undo_action)
        # ...

        view_menu = menubar.addMenu("&View")
        view_menu.addAction(reload_notes_action)
        # Add theme toggle, font size options directly to menu if desired

        help_menu = menubar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

        # --- Toolbar ---
        toolbar = QToolBar("Main Toolbar")
        toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(toolbar)
        toolbar.addAction(new_action)
        toolbar.addAction(save_action)
        toolbar.addAction(delete_action)
        toolbar.addSeparator()
        toolbar.addAction(reload_notes_action)
        toolbar.addSeparator()
        toolbar.addAction(settings_action)

        self.update_action_states()


    def update_action_states(self):
        """Enable/disable actions based on current state."""
        has_current_note = self.current_note_filepath is not None
        self.save_action.setEnabled(has_current_note and self.unsaved_changes)
        self.delete_action.setEnabled(has_current_note)
        # export_html_action might also depend on has_current_note

    def apply_settings_to_ui(self):
        """Applies loaded settings to UI elements."""
        font_size = app_settings.get("font_size", 12)
        self.markdown_editor.set_font_size(font_size)

        theme = app_settings.get("theme", "light")
        self.markdown_viewer.set_theme(theme)
        # Re-render current preview if any
        if self.current_note_filepath:
            note = self._find_note_by_filepath(self.current_note_filepath)
            if note:
                 self.markdown_viewer.set_markdown(note.content)

        # Apply stylesheet for dark/light theme to the whole app
        if theme == "dark":
            # This is a very basic dark theme. A full theme requires more qss.
            self.setStyleSheet("""
                QMainWindow, QWidget { background-color: #333; color: #ccc; }
                QListWidget { background-color: #444; color: #ccc; border: 1px solid #555; }
                QListWidget::item:selected { background-color: #557; }
                QTextEdit { background-color: #2a2a2a; color: #ddd; border: 1px solid #555; }
                QLineEdit { background-color: #444; color: #ccc; border: 1px solid #555; }
                QPushButton { background-color: #555; color: #ccc; border: 1px solid #666; padding: 5px; }
                QPushButton:hover { background-color: #666; }
                QMenuBar { background-color: #333; color: #ccc; }
                QMenuBar::item:selected { background-color: #555; }
                QMenu { background-color: #444; color: #ccc; border: 1px solid #555; }
                QMenu::item:selected { background-color: #557; }
                QStatusBar { background-color: #333; color: #ccc; }
                QSplitter::handle { background-color: #555; }
                QLabel { color: #ccc; }
                QToolBar { background-color: #333; border: none; }
            """)
        else:
            self.setStyleSheet("") # Reset to default style

        # Ensure notes folder exists, or prompt user
        notes_dir = app_settings.get("notes_folder")
        if not os.path.isdir(notes_dir):
            QMessageBox.warning(self, "Notes Folder Not Found",
                                f"The notes folder '{notes_dir}' does not exist.\n"
                                "Please configure it in File -> Settings.")
            # Optionally, open settings dialog directly
            # self.open_settings_dialog()


    def load_initial_notes(self):
        """Scans the notes directory and populates the list and search index."""
        notes_dir = app_settings.get("notes_folder")
        if not os.path.isdir(notes_dir):
            self.statusBar.showMessage(f"Notes folder not found: {notes_dir}. Configure in Settings.", 5000)
            self.notes_list_data = []
        else:
            self.notes_list_data = scan_notes_directory(notes_dir)
            self.notes_list_data.sort(key=lambda n: (n.updated or n.created or ""), reverse=True) # Sort by date
        
        self.search_index.build_index(self.notes_list_data)
        self.clear_editor_and_preview()
        self.current_note_filepath = None
        self.unsaved_changes = False
        self.update_action_states()
        self.notes_reloaded_signal.emit() # Will call update_note_list_display and update_tag_filter_panel
        self.status_label_note_count.setText(f"Notes: {len(self.notes_list_data)}")
        self.status_label_current_note.setText("No note selected")
        self.statusBar.showMessage("Notes loaded.", 2000)


    def update_note_list_display(self, notes_to_display: list[Note] = None):
        """Updates the QListWidget with the given notes or all notes if None."""
        self.notes_list_widget.blockSignals(True) # Avoid triggering selection change during repopulation
        self.notes_list_widget.clear()

        display_list = notes_to_display if notes_to_display is not None else self.notes_list_data
        
        for note in display_list:
            # Display title and a snippet of date/tags
            item_text = f"{note.title}\n<small>{format_timestamp_display(note.updated)} | Tags: {', '.join(note.tags[:3])}</small>"
            list_item = QListWidgetItem()
            
            # Use a QLabel for rich text in QListWidgetItem for better rendering control
            label = QLabel(item_text)
            label.setStyleSheet("background-color: transparent;") # Ensure it inherits list background
            list_item.setSizeHint(label.sizeHint()) # Important for proper item sizing
            
            self.notes_list_widget.addItem(list_item)
            self.notes_list_widget.setItemWidget(list_item, label) # Set QLabel as item widget
            
            # Store the filepath in the item's data for later retrieval
            list_item.setData(Qt.ItemDataRole.UserRole, note.filepath)
        
        self.notes_list_widget.blockSignals(False)
        
        # Reselect current note if it's in the displayed list
        if self.current_note_filepath:
            for i in range(self.notes_list_widget.count()):
                item = self.notes_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_note_filepath:
                    self.notes_list_widget.setCurrentItem(item)
                    break


    def update_tag_filter_panel(self):
        """Populates the tag filter list with unique tags from all notes."""
        self.tag_list_widget.blockSignals(True)
        current_selection = self.tag_list_widget.currentItem().text() if self.tag_list_widget.currentItem() else None
        self.tag_list_widget.clear()
        
        all_tags = self.search_index.get_all_tags()
        if not all_tags:
            self.tag_list_widget.addItem(QListWidgetItem("No tags found"))
            self.tag_list_widget.setEnabled(False)
        else:
            self.tag_list_widget.setEnabled(True)
            # Add an "All Notes" option
            all_item = QListWidgetItem("✨ All Notes")
            all_item.setData(Qt.ItemDataRole.UserRole, None) # Special value for all notes
            self.tag_list_widget.addItem(all_item)

            for tag in all_tags:
                item = QListWidgetItem(tag)
                item.setData(Qt.ItemDataRole.UserRole, tag)
                self.tag_list_widget.addItem(item)
                if tag == current_selection:
                    self.tag_list_widget.setCurrentItem(item) # Reselect
            if not current_selection: # Default to "All Notes" if nothing was selected
                self.tag_list_widget.setCurrentItem(all_item)

        self.tag_list_widget.blockSignals(False)

    def filter_notes_list(self):
        """Filters the note list based on search bar text and selected tag."""
        search_query = self.search_bar.text()
        
        selected_tag_item = self.tag_list_widget.currentItem()
        tag_filter = None
        if selected_tag_item:
            tag_filter = selected_tag_item.data(Qt.ItemDataRole.UserRole) # This could be None for "All Notes"

        # Start with all notes or notes filtered by tag
        if tag_filter:
            notes_to_filter = self.search_index.filter_by_tag(tag_filter)
        else: # "All Notes" or no tag selected
            notes_to_filter = self.notes_list_data[:] # Work on a copy

        # If there's a search query, further filter these notes
        if search_query.strip():
            # We need to rebuild a temporary index or search on the fly for this subset
            # For simplicity, let's search the full index and then intersect
            search_results_notes = self.search_index.search(search_query)
            
            # Intersect search_results_notes with notes_to_filter
            search_result_filepaths = {note.filepath for note in search_results_notes}
            final_filtered_notes = [note for note in notes_to_filter if note.filepath in search_result_filepaths]
        else:
            final_filtered_notes = notes_to_filter
        
        final_filtered_notes.sort(key=lambda n: (n.updated or n.created or ""), reverse=True)
        self.update_note_list_display(final_filtered_notes)


    def on_tag_filter_selected(self, item: QListWidgetItem):
        """Handles tag selection from the filter panel."""
        # The actual filtering logic is now combined in filter_notes_list
        self.filter_notes_list()


    def clear_tag_filter(self):
        """Clears any active tag filter."""
        self.tag_list_widget.setCurrentRow(0) # Select "All Notes" if it's the first item
        # self.tag_list_widget.clearSelection() # Alternative, if "All Notes" isn't an item
        self.filter_notes_list()

    def _find_note_by_filepath(self, filepath: str) -> Note | None:
        """Finds a note in self.notes_list_data by its filepath."""
        for note in self.notes_list_data:
            if note.filepath == filepath:
                return note
        return None

    def on_note_selected(self, current_item: QListWidgetItem, previous_item: QListWidgetItem):
        """Handles selection change in the notes list."""
        if self.check_unsaved_changes(): # Prompts to save if needed
            # If user cancels save dialog, current_item might be None or selection aborted
            if not current_item: # Selection was likely cancelled or cleared
                if previous_item: # Try to reselect previous item
                    self.notes_list_widget.setCurrentItem(previous_item)
                return 
        
        if current_item:
            filepath = current_item.data(Qt.ItemDataRole.UserRole)
            note = self._find_note_by_filepath(filepath)
            if note:
                self.load_note_into_editor(note)
            else:
                self.clear_editor_and_preview()
                self.statusBar.showMessage(f"Error: Note not found in internal list - {filepath}", 3000)
        else:
            self.clear_editor_and_preview()
        
        self.update_action_states()

    def load_note_into_editor(self, note: Note):
        """Loads a note's content into the editor and preview."""
        self.current_note_filepath = note.filepath
        self.markdown_editor.set_markdown_text(note.content) # This should not trigger content_changed immediately
        self.markdown_viewer.set_markdown(note.content)
        self.unsaved_changes = False
        self.update_action_states()
        self.status_label_current_note.setText(f"Editing: {note.title}")
        self.statusBar.showMessage(f"Loaded: {note.title}", 2000)

    def clear_editor_and_preview(self):
        self.markdown_editor.clear()
        self.markdown_viewer.set_markdown("<!-- No note selected or content empty -->") # Clear preview
        self.current_note_filepath = None
        self.unsaved_changes = False
        self.status_label_current_note.setText("No note selected")
        self.update_action_states()

    def on_editor_content_changed(self, markdown_text: str):
        """Handles content changes from the editor (debounced)."""
        self.markdown_viewer.set_markdown(markdown_text)
        if self.current_note_filepath:
            self.unsaved_changes = True
            self.update_action_states()
            # Auto-save logic (can be made configurable)
            if app_settings.get("auto_save_interval", 0) > 0: # If auto-save enabled
                 # For now, direct save. Could use another QTimer here.
                self.save_current_note(auto_save=True)

    def save_current_note(self, auto_save=False):
        """Saves the content of the currently edited note."""
        if not self.current_note_filepath:
            if not auto_save: self.statusBar.showMessage("No note selected to save.", 2000)
            return False

        note = self._find_note_by_filepath(self.current_note_filepath)
        if not note:
            if not auto_save: self.statusBar.showMessage("Error: Current note not found in list.", 3000)
            return False

        current_content = self.markdown_editor.get_markdown_text()
        
        # Only save if content actually changed (or if it's a new note without content yet)
        if note.content == current_content and not auto_save and self.unsaved_changes is False: # if forced save, it will save
             if not auto_save: self.statusBar.showMessage("No changes to save.", 2000)
             return True # No changes, considered successful


        note.content = current_content
        note.updated = get_current_timestamp() # Update timestamp

        if save_note(note):
            self.unsaved_changes = False
            self.update_action_states()
            if not auto_save: self.statusBar.showMessage(f"Note '{note.title}' saved.", 2000)
            
            # Update note in the list and re-sort/re-filter if necessary
            self.notes_list_data.sort(key=lambda n: (n.updated or n.created or ""), reverse=True)
            self.filter_notes_list() # This will re-select the current item too
            return True
        else:
            if not auto_save: QMessageBox.critical(self, "Save Error", f"Could not save note: {note.filepath}")
            return False

    def create_new_note_dialog(self):
        """Opens a dialog to get title for a new note, then creates it."""
        if self.check_unsaved_changes():
            return

        title, ok = QInputDialog.getText(self, "New Note", "Enter title for the new note:")
        if ok and title.strip():
            notes_dir = app_settings.get("notes_folder")
            if not os.path.isdir(notes_dir):
                QMessageBox.warning(self, "Error", f"Notes directory not set or invalid: {notes_dir}")
                return

            new_note = create_new_note(notes_dir, title, tags=["new"], content=f"# {title}\n\nStart writing here...")
            if new_note:
                self.notes_list_data.append(new_note)
                self.search_index.build_index(self.notes_list_data) # Rebuild or update index
                
                self.notes_list_data.sort(key=lambda n: (n.updated or n.created or ""), reverse=True)
                self.filter_notes_list() # This will update display
                self.update_tag_filter_panel() # Update tags

                # Select the new note in the list
                for i in range(self.notes_list_widget.count()):
                    item = self.notes_list_widget.item(i)
                    if item.data(Qt.ItemDataRole.UserRole) == new_note.filepath:
                        self.notes_list_widget.setCurrentItem(item) # This triggers on_note_selected
                        break
                
                self.status_label_note_count.setText(f"Notes: {len(self.notes_list_data)}")
                self.statusBar.showMessage(f"Created new note: {title}", 2000)
            else:
                QMessageBox.critical(self, "Error", "Could not create the new note file.")
        elif ok and not title.strip():
            QMessageBox.warning(self, "New Note", "Title cannot be empty.")


    def delete_current_note(self):
        """Deletes the currently selected note after confirmation."""
        if not self.current_note_filepath:
            self.statusBar.showMessage("No note selected to delete.", 2000)
            return

        note_to_delete = self._find_note_by_filepath(self.current_note_filepath)
        if not note_to_delete:
            self.statusBar.showMessage("Error: Note to delete not found.", 3000)
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete the note '{note_to_delete.title}'?\nThis action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            if delete_note_file(note_to_delete.filepath):
                self.notes_list_data.remove(note_to_delete)
                self.search_index.build_index(self.notes_list_data) # Rebuild index
                
                self.clear_editor_and_preview() # Clear editor as note is gone
                self.current_note_filepath = None # Crucial
                self.unsaved_changes = False
                
                self.filter_notes_list() # Update list display
                self.update_tag_filter_panel()
                self.update_action_states()
                
                self.status_label_note_count.setText(f"Notes: {len(self.notes_list_data)}")
                self.statusBar.showMessage(f"Note '{note_to_delete.title}' deleted.", 2000)
            else:
                QMessageBox.critical(self, "Delete Error", f"Could not delete note file: {note_to_delete.filepath}")

    def export_note_to_html(self):
        """Exports the current note as a standalone HTML file."""
        if not self.current_note_filepath:
            QMessageBox.information(self, "Export HTML", "No note selected to export.")
            return

        note = self._find_note_by_filepath(self.current_note_filepath)
        if not note:
            QMessageBox.warning(self, "Export HTML", "Could not find the selected note data.")
            return

        default_filename = os.path.splitext(os.path.basename(note.filepath))[0] + ".html"
        filepath, _ = QFileDialog.getSaveFileName(self, "Export Note to HTML", default_filename,
                                                  "HTML Files (*.html);;All Files (*)")

        if filepath:
            try:
                # Use the viewer's rendering logic to get the full HTML
                # This requires viewer to expose a method to get the full styled HTML
                # For now, let's assume viewer.get_full_html_for_export(markdown_content)
                # Or, reconstruct it here:
                is_dark = app_settings.get("theme") == "dark"
                html_content = self.markdown_viewer._wrap_html_content( # Accessing protected method for now
                    markdown.markdown(note.content, extensions=['fenced_code', 'codehilite', 'tables', 'nl2br', 'extra'],
                                      extension_configs={'codehilite': {'css_class': 'codehilite'}}),
                    is_dark_theme=is_dark
                )

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                self.statusBar.showMessage(f"Note exported to {filepath}", 3000)
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Could not export note to HTML: {e}")

    def open_settings_dialog(self):
        """Opens the settings dialog and applies changes if OK is pressed."""
        # If there are unsaved changes, prompt before opening settings that might reload things
        # if self.check_unsaved_changes():
        #     return

        dialog = SettingsDialog(self)
        if dialog.exec(): # Modal execution, returns True if accepted
            new_settings = dialog.get_settings()
            restart_required = False

            if app_settings.get("notes_folder") != new_settings["notes_folder"]:
                app_settings.set("notes_folder", new_settings["notes_folder"])
                # This requires reloading notes
                self.load_initial_notes() # This will clear selection and editor
            
            if app_settings.get("theme") != new_settings["theme"]:
                app_settings.set("theme", new_settings["theme"])
                restart_required = True # Full theme change might be complex to apply live

            if app_settings.get("font_size") != new_settings["font_size"]:
                 app_settings.set("font_size", new_settings["font_size"])
            
            app_settings.save_settings()
            self.apply_settings_to_ui() # Re-apply all settings to UI
            self.statusBar.showMessage("Settings updated.", 2000)

            if restart_required:
                QMessageBox.information(self, "Settings Changed", 
                                        "Some settings require an application restart to take full effect (e.g., theme).")


    def show_about_dialog(self):
        QMessageBox.about(self, f"About {APP_NAME}",
                          f"<b>{APP_NAME}</b> v{VERSION}\n\n"
                          "A simple Markdown note-taking application.\n"
                          "Uses Markdown files with YAML front-matter for storage.\n\n"
                          "Developed as a Python project example.")

    def check_unsaved_changes(self) -> bool:
        """
        Checks for unsaved changes. If found, prompts user to save.
        Returns True if user cancels action, False otherwise (saved or discarded).
        """
        if self.unsaved_changes and self.current_note_filepath:
            note = self._find_note_by_filepath(self.current_note_filepath)
            note_title = note.title if note else "current note"
            reply = QMessageBox.question(self, "Unsaved Changes",
                                         f"You have unsaved changes in '{note_title}'.\nDo you want to save them?",
                                         QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                                         QMessageBox.StandardButton.Cancel)

            if reply == QMessageBox.StandardButton.Save:
                if not self.save_current_note():
                    return True # Save failed, consider as cancel
            elif reply == QMessageBox.StandardButton.Cancel:
                return True # User cancelled the operation
            # If Discard, do nothing, unsaved_changes will be reset by loading next note or clearing
        return False # No unsaved changes, or changes handled

    def closeEvent(self, event):
        """Handle window close event."""
        if self.check_unsaved_changes():
            event.ignore() # User cancelled, so ignore close event
            return

        # Save window geometry and splitter states
        app_settings.set("window_width", self.width())
        app_settings.set("window_height", self.height())
        app_settings.set("splitter_sizes_main", self.main_splitter.sizes())
        app_settings.set("splitter_sizes_editor", self.editor_viewer_splitter.sizes())
        app_settings.save_settings()
        event.accept()


def main():
    # For QtWebEngine to work reliably on some systems (e.g. with some Nvidia drivers on Linux)
    # It might be necessary to set:
    # QApplication.setAttribute(Qt.ApplicationAttribute.AA_UseSoftwareOpenGL)
    # Or for Wayland:
    # os.environ["QT_QPA_PLATFORM"] = "wayland"
    # However, try without first.

    # Ensure the QtWebEngineProcess is found, especially when bundled with PyInstaller
    # This might be needed if you bundle the app. For direct script execution, usually not.
    # from PyQt6.QtCore import QCoreApplication
    # QCoreApplication.setLibraryPaths([os.path.join(os.path.dirname(sys.executable), "Qt", "bin")])


    app = QApplication(sys.argv)
    
    # Set application name and version for QSettings (if used directly) and about dialog
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(VERSION)
    app.setOrganizationName("MarkdownNotebookOrg") # For QSettings path

    # Initialize settings (creates config file if not exists)
    if not os.path.exists(app_settings.config_path):
        app_settings.save_settings() # Ensure default settings file is created on first run

    main_window = MainWindow()
    sys.exit(app.exec())

if __name__ == '__main__':
    # Need to import these if running gui_main.py directly and SettingsDialog etc are in same file
    from PyQt6.QtWidgets import QLineEdit, QPushButton, QComboBox, QSpinBox, QDialogButtonBox, QDialog
    import markdown # Ensure markdown is importable here for export
    main()
