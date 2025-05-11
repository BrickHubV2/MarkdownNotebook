import unittest
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from MarkdownNotebook.file_manager import Note
from MarkdownNotebook.search import SearchIndex
from MarkdownNotebook.utils import get_current_timestamp

class TestSearch(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.notes = [
            Note(
                filepath="/test/note1.md", title="Gardening Tips for Roses",
                tags=["gardening", "plants", "roses", "hobby"], created=get_current_timestamp(), updated=get_current_timestamp(),
                content="Roses require regular watering and sunlight. Pruning is key."
            ),
            Note(
                filepath="/test/note2.md", title="Python Web Development",
                tags=["python", "web", "coding", "django"], created=get_current_timestamp(), updated=get_current_timestamp(),
                content="Django and Flask are popular Python frameworks for web apps. Python is versatile."
            ),
            Note(
                filepath="/test/note3.md", title="Healthy Tomato Soup Recipe",
                tags=["cooking", "recipe", "soup", "vegetarian", "healthy"], created=get_current_timestamp(), updated=get_current_timestamp(),
                content="A simple recipe for tomato soup. Ingredients: tomatoes, onion, garlic."
            ),
            Note(
                filepath="/test/note4.md", title="Project Ideas: Python",
                tags=["project", "ideas", "python", "planning"], created=get_current_timestamp(), updated=get_current_timestamp(),
                content="Brainstorming new python project ideas. Maybe a note-taking app with Python?"
            ),
             Note(
                filepath="/test/note5.md", title="Empty Note",
                tags=[], created=get_current_timestamp(), updated=get_current_timestamp(),
                content="" # Empty content
            )
        ]
        cls.search_index = SearchIndex()
        cls.search_index.build_index(cls.notes)

    def test_search_by_title(self):
        results = self.search_index.search("Roses")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Gardening Tips for Roses")

        results_python = self.search_index.search("Python") # Case-insensitive implicit
        self.assertEqual(len(results_python), 2)
        titles = sorted([r.title for r in results_python])
        self.assertListEqual(titles, ["Project Ideas: Python", "Python Web Development"])

    def test_search_by_tag(self):
        results = self.search_index.search("django") # Searches title, tags, content by default
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python Web Development")

        # Specifically search tags
        results_hobby = self.search_index.search("hobby", search_title=False, search_content=False, search_tags=True)
        self.assertEqual(len(results_hobby), 1)
        self.assertEqual(results_hobby[0].title, "Gardening Tips for Roses")

    def test_search_by_content(self):
        results = self.search_index.search("Flask frameworks")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Python Web Development")

        results_tomatoes = self.search_index.search("tomatoes onion")
        self.assertEqual(len(results_tomatoes), 1)
        self.assertEqual(results_tomatoes[0].title, "Healthy Tomato Soup Recipe")

    def test_search_multiple_terms_and_logic(self):
        # 'python' is in title/tags/content of note2 and note4
        # 'ideas' is in title/tags/content of note4
        # "python ideas" should match note4
        results = self.search_index.search("python ideas")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Project Ideas: Python")

    def test_search_no_results(self):
        results = self.search_index.search("nonexistent_term_xyz")
        self.assertEqual(len(results), 0)

    def test_search_empty_query(self):
        results = self.search_index.search("")
        self.assertEqual(len(results), len(self.notes)) # Should return all notes

    def test_filter_by_tag(self):
        results_python_tag = self.search_index.filter_by_tag("python")
        self.assertEqual(len(results_python_tag), 2)
        titles = sorted([r.title for r in results_python_tag])
        self.assertListEqual(titles, ["Project Ideas: Python", "Python Web Development"])

        results_roses_tag = self.search_index.filter_by_tag("roses")
        self.assertEqual(len(results_roses_tag), 1)
        self.assertEqual(results_roses_tag[0].title, "Gardening Tips for Roses")
        
        results_nonexistent_tag = self.search_index.filter_by_tag("nonexistent_tag")
        self.assertEqual(len(results_nonexistent_tag), 0)

    def test_get_all_tags(self):
        all_tags = self.search_index.get_all_tags()
        expected_tags = sorted(list(set(
            ["gardening", "plants", "roses", "hobby",
             "python", "web", "coding", "django",
             "cooking", "recipe", "soup", "vegetarian", "healthy",
             "project", "ideas", "planning"]
        )))
        self.assertListEqual(all_tags, expected_tags)
        
    def test_search_empty_content_note(self):
        # Search for something that won't be in the empty note
        results = self.search_index.search("watering", search_content=True, search_title=False, search_tags=False)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Gardening Tips for Roses")

        # Ensure empty note itself isn't found by content search for specific terms
        # (unless the term is somehow in its title or tags)

if __name__ == '__main__':
    unittest.main()
