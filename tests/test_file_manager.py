import unittest
import os
import shutil
from datetime import datetime, timezone

# Adjust import path if running tests from project root
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MarkdownNotebook.file_manager import Note, scan_notes_directory, load_note, save_note, create_new_note, delete_note_file
from MarkdownNotebook.utils import get_current_timestamp, parse_yaml_front_matter, generate_yaml_front_matter

TEST_NOTES_DIR = os.path.join(os.path.dirname(__file__), "temp_test_notes")

class TestFileManager(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Create a temporary directory for test notes
        if os.path.exists(TEST_NOTES_DIR):
            shutil.rmtree(TEST_NOTES_DIR)
        os.makedirs(TEST_NOTES_DIR, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        # Clean up the temporary directory
        if os.path.exists(TEST_NOTES_DIR):
            shutil.rmtree(TEST_NOTES_DIR)

    def setUp(self):
        # Clear out any files from previous tests within this class
        for item in os.listdir(TEST_NOTES_DIR):
            item_path = os.path.join(TEST_NOTES_DIR, item)
            if os.path.isfile(item_path):
                os.unlink(item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)

    def test_01_create_new_note(self):
        title = "My Test Note for Creation"
        content = "# Test Content\nThis is a test."
        tags = ["test", "creation"]
        
        note = create_new_note(TEST_NOTES_DIR, title, tags=tags, content=content)
        self.assertIsNotNone(note)
        self.assertTrue(os.path.exists(note.filepath))
        self.assertEqual(note.title, title)
        self.assertEqual(note.content.strip(), content.strip())
        self.assertListEqual(sorted(note.tags), sorted(tags))
        
        # Verify timestamps are recent (within a few seconds)
        now = datetime.now(timezone.utc)
        created_dt = datetime.fromisoformat(note.created.replace('Z', '+00:00'))
        updated_dt = datetime.fromisoformat(note.updated.replace('Z', '+00:00'))
        self.assertLess((now - created_dt).total_seconds(), 5)
        self.assertLess((now - updated_dt).total_seconds(), 5)

    def test_02_load_note(self):
        # First, create a note manually to load
        filepath = os.path.join(TEST_NOTES_DIR, "load_me.md")
        title = "Note to Load"
        tags = ["loading", "test"]
        created = "2023-01-01T10:00:00Z"
        updated = "2023-01-01T11:00:00Z"
        content_md = "This is the content to be loaded."
        
        metadata = {'title': title, 'tags': tags, 'created': created, 'updated': updated}
        yaml_front_matter = generate_yaml_front_matter(metadata)
        full_file_content = f"{yaml_front_matter}\n{content_md}"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(full_file_content)
            
        loaded_note = load_note(filepath)
        self.assertIsNotNone(loaded_note)
        self.assertEqual(loaded_note.title, title)
        self.assertListEqual(sorted(loaded_note.tags), sorted(tags))
        self.assertEqual(loaded_note.created, created)
        self.assertEqual(loaded_note.updated, updated)
        self.assertEqual(loaded_note.content.strip(), content_md.strip())

    def test_03_save_note(self):
        filepath = os.path.join(TEST_NOTES_DIR, "save_test.md")
        initial_title = "Initial Save Title"
        now_ts = get_current_timestamp()

        note = Note(filepath, title=initial_title, tags=["saving"], created=now_ts, updated=now_ts, content="Initial content.")
        self.assertTrue(save_note(note))
        
        # Verify by loading and checking front-matter and content
        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        meta, content_part = parse_yaml_front_matter(raw_content)
        
        self.assertEqual(meta.get('title'), initial_title)
        self.assertListEqual(meta.get('tags'), ["saving"])
        self.assertEqual(content_part.strip(), "Initial content.")

        # Modify and save again
        note.title = "Updated Save Title"
        note.content = "Updated content."
        note.tags.append("modified")
        note.updated = get_current_timestamp() # New updated timestamp
        self.assertTrue(save_note(note))

        with open(filepath, 'r', encoding='utf-8') as f:
            raw_content_updated = f.read()
        
        meta_updated, content_part_updated = parse_yaml_front_matter(raw_content_updated)
        self.assertEqual(meta_updated.get('title'), "Updated Save Title")
        self.assertIn("modified", meta_updated.get('tags'))
        self.assertNotEqual(meta_updated.get('updated'), now_ts) # Timestamp should have changed
        self.assertEqual(content_part_updated.strip(), "Updated content.")

    def test_04_scan_notes_directory(self):
        # Create a couple of notes
        create_new_note(TEST_NOTES_DIR, "Scan Note 1", content="Content 1")
        create_new_note(TEST_NOTES_DIR, "Scan Note 2", content="Content 2")
        
        # Create a non-md file, should be ignored
        with open(os.path.join(TEST_NOTES_DIR, "ignore_me.txt"), 'w') as f:
            f.write("This is not a markdown file.")
            
        notes = scan_notes_directory(TEST_NOTES_DIR)
        self.assertEqual(len(notes), 2)
        titles = sorted([note.title for note in notes])
        self.assertListEqual(titles, ["Scan Note 1", "Scan Note 2"])

    def test_05_delete_note_file(self):
        note = create_new_note(TEST_NOTES_DIR, "Note to Delete", content="Will be deleted.")
        self.assertTrue(os.path.exists(note.filepath))
        self.assertTrue(delete_note_file(note.filepath))
        self.assertFalse(os.path.exists(note.filepath))
        # Test deleting non-existent file
        self.assertFalse(delete_note_file(os.path.join(TEST_NOTES_DIR, "does_not_exist.md")))

    def test_06_load_note_no_front_matter(self):
        filepath = os.path.join(TEST_NOTES_DIR, "no_front_matter.md")
        content_md = "# Just Content\nNo YAML here."
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content_md)

        note = load_note(filepath)
        self.assertIsNotNone(note)
        self.assertEqual(note.title, "no_front_matter") # Should default to filename
        self.assertEqual(note.content.strip(), content_md.strip())
        self.assertListEqual(note.tags, [])
        self.assertIsNotNone(note.created) # Should default to now
        self.assertEqual(note.updated, note.created) # Should default to created

    def test_07_load_note_partial_front_matter(self):
        filepath = os.path.join(TEST_NOTES_DIR, "partial_front_matter.md")
        partial_yaml = "---\ntitle: Partial Only\n---\nContent here."
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(partial_yaml)

        note = load_note(filepath)
        self.assertIsNotNone(note)
        self.assertEqual(note.title, "Partial Only")
        self.assertEqual(note.content.strip(), "Content here.")
        self.assertListEqual(note.tags, []) # Default empty list
        self.assertIsNotNone(note.created) # Default
        self.assertEqual(note.updated, note.created) # Default
        
    def test_08_create_note_with_duplicate_title_slug(self):
        title = "Duplicate Title Slug Test"
        create_new_note(TEST_NOTES_DIR, title, content="First instance")
        note2 = create_new_note(TEST_NOTES_DIR, title, content="Second instance")
        
        self.assertIsNotNone(note2)
        self.assertTrue(os.path.exists(note2.filepath))
        # Filename should be different, e.g., duplicate_title_slug_test_1.md
        self.assertRegex(os.path.basename(note2.filepath), r"duplicate_title_slug_test_\d+\.md")

if __name__ == '__main__':
    unittest.main()
