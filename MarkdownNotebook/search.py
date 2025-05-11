"""
In-memory index of titles, tags, and full text for instant search.
"""
from .file_manager import Note # Assuming Note class is defined in file_manager
import re

class SearchIndex:
    def __init__(self):
        self.notes_data = [] # List of dictionaries or Note objects
        self.index = {} # Could be more sophisticated (e.g., inverted index)

    def build_index(self, notes: list[Note]):
        """Builds or rebuilds the search index from a list of Note objects."""
        self.notes_data = []
        self.index = {} # Clear existing index

        for i, note in enumerate(notes):
            # Store a reference or key to the original note.
            # For simplicity, we store the note object itself, but an ID could be better.
            self.notes_data.append({
                'id': note.filepath, # Use filepath as a unique ID
                'title': note.title.lower(),
                'tags': [tag.lower() for tag in note.tags],
                'content': note.content.lower(), # Full text content for searching
                'original_note': note # Reference to the original Note object
            })
        print(f"Search index built with {len(self.notes_data)} notes.")


    def search(self, query: str, search_title=True, search_tags=True, search_content=True) -> list[Note]:
        """
        Performs a search across the indexed notes.
        Returns a list of matching Note objects.
        """
        if not query.strip():
            # If query is empty, return all notes (or handle as no results)
            return [item['original_note'] for item in self.notes_data]

        query_lower = query.lower()
        results = []
        seen_filepaths = set() # To avoid duplicate results if a note matches multiple criteria

        # Simple keyword matching. Can be improved with more advanced techniques
        # like TF-IDF, fuzzy matching, or splitting query into multiple terms.
        # For now, we treat the query as a single phrase or set of keywords.
        # Consider splitting query by space and matching all terms (AND) or any term (OR).
        query_terms = query_lower.split()


        for item in self.notes_data:
            match_score = 0
            text_to_search = []

            if search_title:
                text_to_search.append(item['title'])
            if search_tags:
                text_to_search.extend(item['tags']) # item['tags'] is already a list of lowercased strings
            if search_content:
                text_to_search.append(item['content'])

            # Combine all searchable text into one string for simple matching
            # A more refined approach would weight matches in title/tags higher.
            combined_text = " ".join(text_to_search)

            # Match all terms (AND logic)
            all_terms_match = True
            for term in query_terms:
                if term not in combined_text:
                    all_terms_match = False
                    break
            
            if all_terms_match:
                if item['id'] not in seen_filepaths:
                    results.append(item['original_note'])
                    seen_filepaths.add(item['id'])
        
        # Could sort results by relevance if match_score was implemented
        return results

    def filter_by_tag(self, tag: str) -> list[Note]:
        """Filters notes by a specific tag."""
        if not tag.strip():
            return [item['original_note'] for item in self.notes_data]

        tag_lower = tag.lower()
        results = []
        for item in self.notes_data:
            if tag_lower in item['tags']:
                results.append(item['original_note'])
        return results
    
    def get_all_tags(self) -> list[str]:
        """Returns a sorted list of unique tags from all notes."""
        all_tags = set()
        for item in self.notes_data:
            for tag in item['original_note'].tags: # Use original tags for case preservation if desired
                all_tags.add(tag)
        return sorted(list(all_tags))


if __name__ == '__main__':
    # Example Usage
    from .file_manager import Note # Relative import for testing
    from .utils import get_current_timestamp

    # Create some dummy notes
    note1 = Note(
        filepath="/path/to/note1.md",
        title="Gardening Tips",
        tags=["gardening", "plants", "hobby"],
        created=get_current_timestamp(),
        updated=get_current_timestamp(),
        content="Remember to water your plants regularly. Sun is also important for most plants."
    )
    note2 = Note(
        filepath="/path/to/note2.md",
        title="Python Programming",
        tags=["python", "coding", "programming", "Hobby"],
        created=get_current_timestamp(),
        updated=get_current_timestamp(),
        content="Python is a versatile language. Use virtual environments for projects."
    )
    note3 = Note(
        filepath="/path/to/note3.md",
        title="Recipe: Tomato Soup",
        tags=["cooking", "recipe", "vegetarian"],
        created=get_current_timestamp(),
        updated=get_current_timestamp(),
        content="Ingredients: tomatoes, onion, garlic. A healthy and tasty soup."
    )
    note4 = Note(
        filepath="/path/to/note4.md",
        title="Project Ideas",
        tags=["project", "planning", "python"],
        created=get_current_timestamp(),
        updated=get_current_timestamp(),
        content="Brainstorming new project ideas. Maybe a note-taking app?"
    )

    all_notes = [note1, note2, note3, note4]

    search_engine = SearchIndex()
    search_engine.build_index(all_notes)

    print("--- Search for 'python' ---")
    results_python = search_engine.search("python")
    for note in results_python:
        print(f"- {note.title} (Tags: {note.tags})")

    print("\n--- Search for 'plants hobby' ---")
    results_hobby_plants = search_engine.search("plants hobby")
    for note in results_hobby_plants:
        print(f"- {note.title} (Tags: {note.tags})")


    print("\n--- Search for 'soup' (content only) ---")
    results_soup = search_engine.search("soup", search_title=False, search_tags=False, search_content=True)
    for note in results_soup:
        print(f"- {note.title} (Content: ...{note.content[-30:]})")

    print("\n--- Filter by tag 'hobby' ---")
    results_tag_hobby = search_engine.filter_by_tag("hobby")
    for note in results_tag_hobby:
        print(f"- {note.title}")
        
    print("\n--- Get all tags ---")
    tags = search_engine.get_all_tags()
    print(tags) # Should be ['coding', 'cooking', 'gardening', 'hobby', 'Hobby', 'planning', 'plants', 'programming', 'project', 'python', 'recipe', 'vegetarian'] -> sorted unique
