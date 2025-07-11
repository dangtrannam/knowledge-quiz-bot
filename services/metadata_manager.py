import os
import json
import logging

class MetadataManager:
    def __init__(self, metadata_file: str = "./processed_files.json"):
        self.metadata_file = metadata_file

    def load_metadata(self):
        try:
            if os.path.exists(self.metadata_file):
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    processed_files = json.load(f)
                logging.info(f"Loaded metadata for {len(processed_files)} processed files")
                return processed_files
            else:
                logging.info("No existing metadata found, starting fresh")
                return {}
        except Exception as e:
            logging.error(f"Error loading metadata: {e}")
            return {}

    def save_metadata(self, processed_files):
        try:
            os.makedirs(os.path.dirname(self.metadata_file) if os.path.dirname(self.metadata_file) else '.', exist_ok=True)
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(processed_files, f, indent=2, ensure_ascii=False)
            logging.info(f"Saved metadata for {len(processed_files)} processed files")
        except Exception as e:
            logging.error(f"Error saving metadata: {e}") 