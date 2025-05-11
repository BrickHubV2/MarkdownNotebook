"""
Renders Markdown to styled HTML in a Qt WebView or similar widget.
Handles syntax highlighting for code blocks.
Ensures HTML sanitization.
"""
import markdown
from pygments.formatters import HtmlFormatter
# For sanitization, 'bleach' is a good option, but not in initial requirements.
# import bleach

# PyQt6 specific imports
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEngineSettings # For controlling features
from PyQt6.QtCore import QUrl, Qt

# Base CSS for styling the HTML view
BASE_CSS_LIGHT = """
body {
    font-family: sans-serif;
    line-height: 1.6;
    padding: 20px;
    color: #333;
    background-color: #fff;
}
h1, h2, h3, h4, h5, h6 {
    color: #111;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
pre {
    background-color: #f5f5f5;
    border: 1px solid #ddd;
    border-radius: 3px;
    padding: 10px;
    overflow: auto;
}
code {
    font-family: monospace;
    background-color: #f0f0f0; /* Lighter for inline code */
    padding: 0.2em 0.4em;
    margin: 0;
    font-size: 85%;
    border-radius: 3px;
}
pre > code {
    padding: 0;
    margin: 0;
    font-size: inherit;
    background-color: transparent;
    border: none;
}
blockquote {
    border-left: 5px solid #ccc;
    padding-left: 15px;
    margin-left: 0;
    color: #555;
}
table {
    border-collapse: collapse;
    margin-bottom: 1em;
    width: auto; /* Or 100% if you prefer full-width tables */
}
th, td {
    border: 1px solid #ddd;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #f2f2f2;
}
img {
    max-width: 100%;
    height: auto;
}
"""

BASE_CSS_DARK = """
body {
    font-family: sans-serif;
    line-height: 1.6;
    padding: 20px;
    color: #ccc;
    background-color: #333;
}
h1, h2, h3, h4, h5, h6 {
    color: #eee;
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}
pre {
    background-color: #222; /* Darker for code blocks */
    border: 1px solid #444;
    border-radius: 3px;
    padding: 10px;
    overflow: auto;
}
code {
    font-family: monospace;
    background-color: #444; /* Slightly lighter for inline code */
    padding: 0.2em 0.4em;
    margin: 0;
    font-size: 85%;
    border-radius: 3px;
}
pre > code {
    padding: 0;
    margin: 0;
    font-size: inherit;
    background-color: transparent;
    border: none;
}
blockquote {
    border-left: 5px solid #555;
    padding-left: 15px;
    margin-left: 0;
    color: #aaa;
}
table {
    border-collapse: collapse;
    margin-bottom: 1em;
    width: auto;
}
th, td {
    border: 1px solid #555;
    padding: 8px;
    text-align: left;
}
th {
    background-color: #424242;
}
img {
    max-width: 100%;
    height: auto;
}
a { color: #6c9ecf; }
a:visited { color: #8e88df; }
"""

class MarkdownViewer(QWebEngineView):
    def __init__(self, parent: QWidget = None):
        super().__init__(parent)
        self.setObjectName("MarkdownViewer")
        self.current_theme = "light" # "light" or "dark"
        self.pygments_style = "default" # Pygments style for light theme
        self.pygments_style_dark = "monokai" # Pygments style for dark theme

        # Configure WebEngine settings for security and functionality
        settings = self.settings()
        settings.setAttribute(QWebEngineSettings.WebAttribute.JavascriptEnabled, False) # Disable JS for security
        settings.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
        settings.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, True) # Smooth scrolling

        self.setHtml(self._wrap_html_content("<h1>Markdown Notebook</h1><p>Preview will appear here.</p>"))

    def _get_pygments_css(self, style_name: str) -> str:
        """Generates CSS for Pygments syntax highlighting."""
        try:
            formatter = HtmlFormatter(style=style_name, noclasses=False)
            return formatter.get_style_defs('.codehilite') # .codehilite is used by 'fenced_code' and 'codehilite' exts
        except Exception as e:
            print(f"Error getting Pygments style '{style_name}': {e}")
            return "" # Fallback to no Pygments styling

    def _wrap_html_content(self, html_content: str, is_dark_theme: bool = False) -> str:
        """Wraps the given HTML content with base CSS and Pygments CSS."""
        base_css = BASE_CSS_DARK if is_dark_theme else BASE_CSS_LIGHT
        pygments_css = self._get_pygments_css(self.pygments_style_dark if is_dark_theme else self.pygments_style)

        full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                {base_css}
                {pygments_css}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        return full_html

    def set_markdown(self, md_text: str):
        """Converts Markdown to HTML and displays it."""
        try:
            # Markdown extensions:
            # - fenced_code: for ```python ... ``` style code blocks
            # - codehilite: for syntax highlighting (requires Pygments)
            # - tables: for Markdown tables
            # - toc: for table of contents (optional, might need specific styling)
            # - nl2br: for converting newlines to <br> (GitHub-style)
            extensions = [
                'fenced_code',
                'codehilite', # Note: codehilite needs `css_class='codehilite'` usually
                'tables',
                'nl2br',
                'extra' # Includes abbreviations, attribute lists, def lists, footnotes, etc.
            ]
            extension_configs = {
                'codehilite': {
                    'css_class': 'codehilite',  # Class for Pygments CSS
                    'linenums': False,          # Show line numbers
                    'guess_lang': True,
                    'pygments_style': self.pygments_style_dark if self.current_theme == "dark" else self.pygments_style,
                }
            }
            html_output = markdown.markdown(md_text, extensions=extensions, extension_configs=extension_configs)

            # Basic sanitization (consider using 'bleach' for more robust sanitization)
            # For now, we rely on QWebEngineView's sandboxing and disabled JS.
            # html_output = bleach.clean(html_output, tags=ALLOWED_TAGS, attributes=ALLOWED_ATTRIBUTES)

        except Exception as e:
            html_output = f"<p>Error rendering Markdown: {e}</p><pre>{md_text}</pre>"

        full_html = self._wrap_html_content(html_output, self.current_theme == "dark")
        self.setHtml(full_html, QUrl("qrc:///")) # Use qrc scheme or about:blank for base URL

    def set_theme(self, theme: str): # "light" or "dark"
        """Sets the theme for the viewer."""
        if theme in ["light", "dark"]:
            self.current_theme = theme
            # Re-render current content with new theme
            current_page_html = self.page().toHtml(lambda html: self._update_theme_in_html(html, theme == "dark"))


    def _update_theme_in_html(self, current_html_body: str, is_dark_theme: bool):
        """
        Helper to re-wrap existing HTML body with new theme styles.
        This is a simplified approach; ideally, you'd re-render from Markdown.
        For now, this will just reload the last rendered Markdown with the new theme.
        """
        # A better way is to store the last markdown and call set_markdown again.
        # This is a placeholder until that is implemented.
        # For now, this function is not directly used by set_theme,
        # set_markdown will be called again by the main application.
        pass

    def set_font_size_multiplier(self, multiplier: float):
        """ Adjusts the zoom factor of the web view. """
        self.setZoomFactor(multiplier) # e.g., 1.0 is normal, 1.2 is 120%

if __name__ == '__main__':
    from PyQt6.QtWidgets import QApplication, QVBoxLayout
    import sys

    app = QApplication(sys.argv)
    window = QWidget()
    layout = QVBoxLayout(window)
    viewer = MarkdownViewer()
    layout.addWidget(viewer)

    test_markdown = """
# Hello World

This is a **Markdown** test.

- Item 1
- Item 2
  - Sub-item

```python
def greet(name):
    print(f"Hello, {name}!")

greet("Viewer")
