# Markdown Notebook

A standalone note-taking application that uses plain-text Markdown files for storage, with no external database.

## Core Features

*   Create/Edit/Delete notes (.md files) with YAML front-matter metadata.
*   Live Markdown preview with HTML rendering & code-block highlighting.
*   In-memory search: real-time search by title, tags, or full text.
*   Tag filter panel: click a tag to filter note list.
*   Auto-save on edit and update 'updated' timestamp.
*   Export: Save selected note(s) as HTML files for sharing.
*   Settings dialog: choose notes folder, toggle light/dark theme, adjust font size.

## Module Structure

*   `MarkdownNotebook/file_manager.py`: Scan notes folder, load/save .md, parse YAML front-matter.
*   `MarkdownNotebook/editor.py`: Markdown editor component with live preview pane.
*   `MarkdownNotebook/viewer.py`: Render markdown to styled HTML.
*   `MarkdownNotebook/search.py`: In-memory index of titles, tags, and full text for instant search.
*   `MarkdownNotebook/settings.py`: Manage app config: notes folder path, font size, theme.
*   `MarkdownNotebook/gui_main.py`: Assemble menus, toolbars, note list, editor/viewer panes.
*   `MarkdownNotebook/utils.py`: YAML parsing, timestamp utilities.

## Installation

1.  **Clone the repository (or create the project files):**
    ```bash
    # git clone <repository_url> MarkdownNotebook
    # cd MarkdownNotebook
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **(Optional) Create your notes folder:**
    The application will allow you to configure this, but you can pre-create it:
    ```bash
    mkdir -p ~/MarkdownNotebook/notes  # Example path
    ```

## Usage

1.  Launch the application:
    ```bash
    python MarkdownNotebook/gui_main.py
    ```
2.  On first launch, or via `File → Settings`, configure the path to your notes folder.

## Notes

*   No database required: all data lives as Markdown files.
*   On startup, the application scans the notes folder and builds an in-memory index.
*   YAML front-matter is used for metadata within each note.
*   HTML preview should sanitize content to prevent script injection.
*   Unit tests are planned for `file_manager` and `search` modules.
