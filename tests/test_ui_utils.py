import pytest
from unittest.mock import patch
import ui.utils as ui_utils

class TestUIUtils:
    def test_setup_page_config_runs(self):
        with patch('streamlit.set_page_config') as mock_set:
            ui_utils.setup_page_config()
            mock_set.assert_called_once()

    def test_load_css_runs(self):
        with patch('streamlit.markdown') as mock_markdown:
            ui_utils.load_css()
            mock_markdown.assert_called()

    def test_show_info_box_info(self):
        with patch('streamlit.markdown') as mock_markdown:
            ui_utils.show_info_box('Title', 'Content', 'info')
            mock_markdown.assert_called()

    def test_show_info_box_success(self):
        with patch('streamlit.markdown') as mock_markdown:
            ui_utils.show_info_box('Title', 'Content', 'success')
            mock_markdown.assert_called()

    def test_display_progress_bar(self):
        with patch('streamlit.markdown') as mock_markdown:
            ui_utils.display_progress_bar(3, 10, label='Test Progress')
            mock_markdown.assert_called()

    def test_display_progress_bar_zero_total(self):
        # Should not call markdown if total is zero
        with patch('streamlit.markdown') as mock_markdown:
            ui_utils.display_progress_bar(3, 0, label='Test Progress')
            mock_markdown.assert_not_called() 