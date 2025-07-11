import os
import tempfile
import shutil
import json
import pytest
from services.metadata_manager import MetadataManager

class TestMetadataManager:
    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.temp_metadata = os.path.join(self.temp_dir, 'metadata.json')
        self.manager = MetadataManager(metadata_file=self.temp_metadata)
    def teardown_method(self):
        try:
            shutil.rmtree(self.temp_dir)
        except PermissionError:
            pass
    def test_load_metadata_empty(self):
        data = self.manager.load_metadata()
        assert data == {}
    def test_save_and_load_metadata(self):
        sample = {'abc': {'filename': 'file1.pdf'}}
        self.manager.save_metadata(sample)
        loaded = self.manager.load_metadata()
        assert loaded == sample
    def test_load_corrupt_metadata(self):
        with open(self.temp_metadata, 'w') as f:
            f.write('{invalid json')
        data = self.manager.load_metadata()
        assert data == {} 