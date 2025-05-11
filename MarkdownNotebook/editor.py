"""
Markdown editor component with live preview pane.
This will heavily depend on the chosen GUI toolkit.
For PyQt6, this might involve a QTextEdit for Markdown input
and a QWebEngineView (or QTextBrowser for simpler HTML) for preview.
"""
from PyQt6.QtWidgets import QWidget, QTextEdit, QVBoxLayout, QSplitter
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
# from .viewer import MarkdownViewer # Assuming viewer.py has a preview widget

class MarkdownEditor(QWidget):
    """
    A widget combining a Markdown text editor and a live preview.
    """
    content_changed = pyqtSignal(str) # Emits the raw markdown text

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("MarkdownEditor")

        self.markdown_input = QTextEdit(self)
        self.markdown_input.setPlaceholderText("Enter your Markdown here...")
        self.markdown_input.setAcceptRichText(False) # Ensure plain text

        # Preview pane (placeholder, will be replaced by actual viewer widget)
        # For now, let's use another QTextEdit to show it's distinct
        # self.preview_pane = QTextEdit(self)
        # self.preview_pane.setReadOnly(True)
        # A more advanced approach would use self.viewer = MarkdownViewer(self)

        # Using a QSplitter to allow resizing
        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.addWidget(self.markdown_input)
        # self.splitter.addWidget(self.preview_pane) # Add actual preview later
        # self.splitter.setSizes([self.width() // 2, self.width() // 2]) # Initial sizes

        layout = QVBoxLayout(self)
        layout.addWidget(self.splitter)
        layout.setContentsMargins(0,0,0,0)
        self.setLayout(layout)

        # Timer for delayed preview update (auto-save and preview)
        self.update_timer = QTimer(self)
        self.update_timer.setSingleShot(True)
        self.update_timer.setInterval(1000) # 1 second delay
        self.update_timer.timeout.connect(self._emit_content_changed)

        self.markdown_input.textChanged.connect(self.on_text_changed)

    def on_text_changed(self):
        """Called when text in the markdown input changes."""
        self.update_timer.start() # Restart timer

    def _emit_content_changed(self):
        """Emits the content_changed signal with current markdown."""
        current_markdown = self.get_markdown_text()
        self.content_changed.emit(current_markdown)
        # The main GUI will catch this signal, update the preview, and trigger auto-save

    def set_markdown_text(self, text: str):
        """Sets the text in the Markdown input field."""
        self.markdown_input.blockSignals(True) # Avoid triggering textChanged during set
        self.markdown_input.setPlainText(text)
        self.markdown_input.blockSignals(False)
        # Optionally, trigger an immediate preview update if needed
        # self._emit_content_changed()

    def get_markdown_text(self) -> str:
        """Gets the current text from the Markdown input field."""
        return self.markdown_input.toPlainText()

    def set_font_size(self, size: int):
        """Sets the font size for the editor."""
        font = self.markdown_input.font()
        font.setPointSize(size)
        self.markdown_input.setFont(font)
        # If preview pane has separate font settings, update it too.

    def clear(self):
        """Clears the editor."""
        self.markdown_input.clear()

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)
    editor_widget = MarkdownEditor()

    def handle_content_change(md_text):
        print("Editor content changed (debounced):")
        # print(md_text[:100] + "...") # Print first 100 chars
        # In a real app, this would update the preview pane and auto-save
        # editor_widget.preview_pane.setMarkdown(md_text) # If preview pane supports setMarkdown
        print("Preview would be updated here.")


    editor_widget.content_changed.connect(handle_content_change)
    editor_widget.set_markdown_text("# Hello\n\nThis is a *test*.\n\n```python\nprint('hello')\n```")
    editor_widget.setWindowTitle("Markdown Editor Test")
    editor_widget.resize(800, 600)
    editor_widget.show()
    sys.exit(app.exec())
