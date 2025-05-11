"""
Manages application configuration:
- Notes folder path
- Font size
- Theme (light/dark)
- Other preferences
Settings are typically stored in a JSON or INI file in a user-specific config directory.
"""
import json
import os

# Determine OS-specific config directory
if os.name == 'nt': # Windows
    APP_CONFIG_DIR = os.path.join(os.getenv('APPDATA'), 'MarkdownNotebook')
else: # macOS, Linux
    APP_CONFIG_DIR = os.path.join(os.getenv('HOME'), '.config', 'MarkdownNotebook')

CONFIG_FILE_PATH = os.path.join(APP_CONFIG_DIR, 'settings.json')

DEFAULT_SETTINGS = {
    "notes_folder": os.path.join(os.getenv('HOME') or os.getenv('USERPROFILE'), 'MarkdownNotebook', 'Notes'),
    "font_size": 12, # Editor font size
    "theme": "light", # "light" or "dark"
    "auto_save_interval": 2000, # milliseconds, e.g., 2 seconds
    "preview_update_delay": 500, # milliseconds for live preview
    "window_width": 1000,
    "window_height": 700,
    "splitter_sizes_main": [250, 750], # Note list, editor/viewer area
    "splitter_sizes_editor": [500, 500] # Editor, preview
}

class AppSettings:
    def __init__(self, config_path=CONFIG_FILE_PATH):
        self.config_path = config_path
        self.settings = DEFAULT_SETTINGS.copy() # Start with defaults
        self._load_settings()

    def _load_settings(self):
        """Loads settings from the config file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_settings = json.load(f)
                    # Merge loaded settings with defaults to ensure all keys are present
                    # and new default keys are added if the config file is old.
                    for key in DEFAULT_SETTINGS:
                        if key in loaded_settings:
                            self.settings[key] = loaded_settings[key]
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading settings from {self.config_path}: {e}. Using defaults.")
                self.settings = DEFAULT_SETTINGS.copy() # Reset to defaults on error
        else:
            # If no config file, use defaults and save them to create the file.
            print(f"No settings file found at {self.config_path}. Creating with defaults.")
            self.save_settings() # Save defaults if file doesn't exist

    def save_settings(self):
        """Saves the current settings to the config file."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4)
        except IOError as e:
            print(f"Error saving settings to {self.config_path}: {e}")

    def get(self, key, default=None):
        """Gets a setting value by key."""
        return self.settings.get(key, default)

    def set(self, key, value):
        """Sets a setting value by key and saves settings."""
        if key in self.settings:
            self.settings[key] = value
            # self.save_settings() # Consider if saving on every set is desired or in bulk
        else:
            print(f"Warning: Attempting to set unknown setting key '{key}'")
    
    def get_all(self):
        return self.settings.copy()

# Global instance of settings, can be imported by other modules
# from .settings import app_settings
app_settings = AppSettings()

if __name__ == '__main__':
    print(f"Config file path: {app_settings.config_path}")
    
    print("\nInitial settings:")
    for k, v in app_settings.get_all().items():
        print(f"- {k}: {v}")

    # Example: Change a setting
    current_theme = app_settings.get("theme")
    new_theme = "dark" if current_theme == "light" else "light"
    app_settings.set("theme", new_theme)
    app_settings.set("font_size", app_settings.get("font_size") + 1)
    
    # Important: Call save_settings() explicitly if not done in set()
    app_settings.save_settings() 
    print(f"\nChanged theme to: {app_settings.get('theme')}")
    print(f"Changed font_size to: {app_settings.get('font_size')}")

    # Test loading them back (by creating a new instance)
    reloaded_settings = AppSettings()
    print("\nReloaded settings:")
    for k, v in reloaded_settings.get_all().items():
        print(f"- {k}: {v}")

    # Reset to defaults for next test run if needed
    # app_settings.settings = DEFAULT_SETTINGS.copy()
    # app_settings.save_settings()
    # print("\nSettings reset to defaults.")
