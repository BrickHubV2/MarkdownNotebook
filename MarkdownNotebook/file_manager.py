"""
Manages file system operations for notes:
- Scanning the notes directory.
- Reading and writing Markdown files.
- Parsing and updating YAML front-matter.
- Deleting notes.
"""
import os
import glob
from datetime import datetime
import yaml # From PyYAML
from .utils import parse_yaml_front_matter, generate_yaml_front_matter, get_current_timestamp

class Note:
    def __init__(self, filepath, title="", tags=None, created=None, updated=None, content=""):
        self.filepath = filepath
        self.title = title
        self.tags = tags if tags is not None else []
        self.created = created
        self.updated = updated
        self.content = content # Markdown content without front-matter

    def __repr__(self):
        return f"<Note title='{self.title}' path='{self.filepath}'>"

def scan_notes_directory(notes_dir: str) -> list[Note]:
    """Scans the directory for .md files and loads them."""
    notes = []
    if not os.path.isdir(notes_dir):
        print(f"Error: Notes directory '{notes_dir}' not found or not a directory.")
        return notes

    for md_file in glob.glob(os.path.join(notes_dir, "*.md")):
        note = load_note(md_file)
        if note:
            notes.append(note)
    return notes

def load_note(filepath: str) -> Note | None:
    """Loads a single note from an .md file, parsing front-matter."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            full_content = f.read()

        metadata, content = parse_yaml_front_matter(full_content)

        # Ensure essential metadata, provide defaults if missing
        title = metadata.get('title', os.path.splitext(os.path.basename(filepath))[0])
        tags = metadata.get('tags', [])
        created = metadata.get('created', get_current_timestamp()) # Default to now if not present
        updated = metadata.get('updated', created) # Default to created time if not present

        return Note(
            filepath=filepath,
            title=title,
            tags=tags,
            created=created,
            updated=updated,
            content=content
        )
    except Exception as e:
        print(f"Error loading note {filepath}: {e}")
        return None

def save_note(note: Note) -> bool:
    """Saves a note object to its .md file, including front-matter."""
    try:
        metadata = {
            'title': note.title,
            'tags': note.tags,
            'created': note.created,
            'updated': note.updated
        }
        front_matter_str = generate_yaml_front_matter(metadata)
        full_content = f"{front_matter_str}\n{note.content.strip()}"

        os.makedirs(os.path.dirname(note.filepath), exist_ok=True) # Ensure directory exists
        with open(note.filepath, 'w', encoding='utf-8') as f:
            f.write(full_content)
        return True
    except Exception as e:
        print(f"Error saving note {note.filepath}: {e}")
        return False

def create_new_note(notes_dir: str, title: str, tags: list = None, content: str = "") -> Note | None:
    """Creates a new note file with basic front-matter."""
    filename = f"{title.lower().replace(' ', '_'). Gsub(r'[^a-z0-9_]', '')}.md" # Basic slugify
    if not filename.strip() or filename == ".md": # Handle empty or invalid titles
        filename = f"untitled_{datetime.now().strftime('%Y%m%d%H%M%S')}.md"

    filepath = os.path.join(notes_dir, filename)
    
    # Avoid overwriting existing file by appending number if needed
    counter = 1
    base_filepath, ext = os.path.splitext(filepath)
    while os.path.exists(filepath):
        filepath = f"{base_filepath}_{counter}{ext}"
        counter += 1

    now = get_current_timestamp()
    note = Note(
        filepath=filepath,
        title=title,
        tags=tags if tags is not None else [],
        created=now,
        updated=now,
        content=content
    )
    if save_note(note):
        return note
    return None

def delete_note_file(filepath: str) -> bool:
    """Deletes the .md file from the file system."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
        return False # File not found
    except Exception as e:
        print(f"Error deleting note {filepath}: {e}")
        return False

if __name__ == '__main__':
    # Example Usage (for testing this module)
    EXAMPLE_NOTES_DIR = os.path.join(os.path.dirname(__file__), "notes_example_runtime")
    os.makedirs(EXAMPLE_NOTES_DIR, exist_ok=True)

    print(f"Using example notes directory: {EXAMPLE_NOTES_DIR}")

    # Create a new note
    new_note_title = "My First Test Note"
    created_note = create_new_note(EXAMPLE_NOTES_DIR, new_note_title, tags=["testing", "example"], content="# Hello World\nThis is a test.")
    if created_note:
        print(f"Created note: {created_note.filepath}")

        # Load it back
        loaded_note = load_note(created_note.filepath)
        if loaded_note:
            print(f"Loaded note title: {loaded_note.title}, tags: {loaded_note.tags}")
            print(f"Content:\n{loaded_note.content[:50]}...") # Print first 50 chars of content

            # Update note
            loaded_note.content += "\n\nAn update was made."
            loaded_note.tags.append("updated")
            loaded_note.updated = get_current_timestamp()
            if save_note(loaded_note):
                print("Note updated and saved.")

        # Scan directory
        all_notes = scan_notes_directory(EXAMPLE_NOTES_DIR)
        print(f"\nFound {len(all_notes)} notes in {EXAMPLE_NOTES_DIR}:")
        for n in all_notes:
            print(f"- {n.title} (updated: {n.updated})")

        # Delete the note
        # if delete_note_file(created_note.filepath):
        #     print(f"Deleted note: {created_note.filepath}")
        # else:
        #     print(f"Failed to delete note: {created_note.filepath}")
    else:
        print("Failed to create note.")

    # Clean up example directory if empty, or manually delete it
    # import shutil
    # if os.path.exists(EXAMPLE_NOTES_DIR):
    #     shutil.rmtree(EXAMPLE_NOTES_DIR)
    #     print(f"Cleaned up example directory: {EXAMPLE_NOTES_DIR}")
