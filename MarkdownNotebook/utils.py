"""
Utility functions for YAML parsing, timestamp management, etc.
"""
import yaml # PyYAML
from datetime import datetime, timezone
import re

# --- YAML Front-matter ---
YAML_FRONT_MATTER_REGEX = re.compile(r'^---\s*\n(.*?\n)^---\s*\n', re.DOTALL | re.MULTILINE)

def parse_yaml_front_matter(file_content: str) -> tuple[dict, str]:
    """
    Parses YAML front-matter from the beginning of a string.
    Returns a tuple: (metadata_dict, content_string_without_front_matter).
    If no front-matter is found, returns ({}, original_content_string).
    """
    match = YAML_FRONT_MATTER_REGEX.match(file_content)
    if match:
        try:
            metadata_str = match.group(1)
            metadata = yaml.safe_load(metadata_str)
            if not isinstance(metadata, dict): # Ensure it's a dictionary
                metadata = {}
            content_after_front_matter = file_content[match.end():]
            return metadata, content_after_front_matter
        except yaml.YAMLError:
            # If YAML parsing fails, treat it as no valid front-matter
            return {}, file_content
    return {}, file_content

def generate_yaml_front_matter(metadata: dict) -> str:
    """
    Generates a YAML front-matter string from a dictionary.
    Ensures 'created' and 'updated' timestamps are in ISO format if present.
    """
    # Convert datetime objects to ISO format strings if they exist
    for key in ['created', 'updated']:
        if key in metadata and isinstance(metadata[key], datetime):
            metadata[key] = metadata[key].isoformat()
    
    if not metadata:
        return ""
    try:
        yaml_str = yaml.dump(metadata, sort_keys=False, allow_unicode=True, default_flow_style=False)
        return f"---\n{yaml_str}---\n"
    except yaml.YAMLError:
        return "---\n# Error generating YAML\n---\n"

# --- Timestamp Utilities ---
def get_current_timestamp() -> str:
    """Returns the current time as an ISO 8601 formatted string (UTC)."""
    return datetime.now(timezone.utc).isoformat(timespec='seconds')

def parse_timestamp(ts_str: str) -> datetime | None:
    """Parses an ISO 8601 timestamp string into a datetime object."""
    if not ts_str:
        return None
    try:
        # Handle potential 'Z' for UTC explicitly for broader compatibility, though fromisoformat should handle it.
        if ts_str.endswith('Z'):
            ts_str = ts_str[:-1] + '+00:00'
        return datetime.fromisoformat(ts_str)
    except (ValueError, TypeError):
        # Try common alternative formats if fromisoformat fails (e.g. missing timezone)
        try:
            dt_obj = datetime.strptime(ts_str, "%Y-%m-%dT%H:%M:%S")
            # Assume naive datetime is UTC if no timezone info
            return dt_obj.replace(tzinfo=timezone.utc)
        except ValueError:
            return None # Could not parse

def format_timestamp_display(dt_obj: datetime | str | None) -> str:
    """Formats a datetime object or ISO string for user-friendly display."""
    if isinstance(dt_obj, str):
        dt_obj = parse_timestamp(dt_obj)
    
    if not isinstance(dt_obj, datetime):
        return "N/A"

    # Convert to local timezone for display
    try:
        local_dt = dt_obj.astimezone(None) # None uses system's local timezone
        return local_dt.strftime("%Y-%m-%d %H:%M")
    except ValueError: # Handle naive datetime if conversion fails
        return dt_obj.strftime("%Y-%m-%d %H:%M (UTC*)")


if __name__ == '__main__':
    # Test YAML parsing
    print("--- YAML Parsing Test ---")
    md_with_front_matter = """---
title: My Test Note
tags:
  - test
  - example
created: 2023-01-01T10:00:00Z
updated: 2023-01-02T12:30:00Z
---
This is the actual content of the note.
It starts after the second '---'.
"""
    md_without_front_matter = "# Just a title\nNo front-matter here."
    md_malformed_front_matter = """---
title: Malformed
tags: [one, two
---
Content."""

    meta, content = parse_yaml_front_matter(md_with_front_matter)
    print("With Front Matter:")
    print("Meta:", meta)
    print("Content:", content.strip()[:30] + "...")

    meta, content = parse_yaml_front_matter(md_without_front_matter)
    print("\nWithout Front Matter:")
    print("Meta:", meta)
    print("Content:", content.strip()[:30] + "...")

    meta, content = parse_yaml_front_matter(md_malformed_front_matter)
    print("\nMalformed Front Matter:")
    print("Meta:", meta)
    print("Content:", content.strip()[:30] + "...")
    
    # Test YAML generation
    print("\n--- YAML Generation Test ---")
    sample_meta = {'title': 'Generated Note', 'tags': ['gen', 'test'], 'created': datetime.now(timezone.utc)}
    generated_yaml = generate_yaml_front_matter(sample_meta)
    print(generated_yaml)
    
    empty_yaml = generate_yaml_front_matter({})
    print(f"Empty Meta: '{empty_yaml}'")

    # Test Timestamp utilities
    print("\n--- Timestamp Test ---")
    now_ts_str = get_current_timestamp()
    print(f"Current Timestamp (ISO): {now_ts_str}")

    parsed_dt = parse_timestamp(now_ts_str)
    print(f"Parsed Timestamp (datetime object): {parsed_dt}")

    if parsed_dt:
        display_str = format_timestamp_display(parsed_dt)
        print(f"Formatted for Display (Local Time): {display_str}")

    display_from_str = format_timestamp_display("2024-07-15T10:30:00+02:00")
    print(f"Formatted specific ISO for Display: {display_from_str}")

    display_from_naive_str = format_timestamp_display("2024-07-15T08:30:00") # No TZ info
    print(f"Formatted naive string for Display: {display_from_naive_str}")

    print(f"Invalid timestamp: {format_timestamp_display(None)}")
    print(f"Invalid timestamp string: {format_timestamp_display('not-a-date')}")
