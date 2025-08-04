import os
import sys
import pytest
from unittest.mock import MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.MarkdownCleaner import MarkdownCleaner

@pytest.fixture
def config():
    """Fixture for a mock config object."""
    mock_config = MagicMock()
    mock_config.processing.char_replacements = {
        "\\n": " ",
        "  ": " ",
        "&nbsp;": " "
    }
    return mock_config

@pytest.fixture
def logger():
    """Fixture for a mock logger."""
    return MagicMock()

@pytest.fixture
def cleaner(config, logger):
    """Fixture for a MarkdownCleaner instance."""
    return MarkdownCleaner(config, logger)

def test_remove_markdown_links(cleaner):
    text = "This is a [link](http://example.com) and an ![image](http://example.com/img.png)."
    cleaned = cleaner._remove_markdown_links(text)
    assert "link" not in cleaned
    assert "image" not in cleaned
    assert "This is a" in cleaned

def test_apply_char_replacements(cleaner):
    text = "Hello&nbsp;world\\nThis is a test."
    cleaned = cleaner._apply_char_replacements(text)
    assert "&nbsp;" not in cleaned
    assert "\\n" not in cleaned
    assert "Hello world This is a test." in cleaned

def test_clean_multiple_newlines(cleaner):
    text = "Line 1\n\n\n\nLine 2"
    cleaned = cleaner._clean_multiple_newlines(text)
    assert "\n\n\n" not in cleaned
    assert "Line 1\n\nLine 2" in cleaned

def test_remove_formatting_lines(cleaner):
    text = "Hello\n---\nWorld"
    cleaned = cleaner._remove_formatting_lines(text)
    assert "---" not in cleaned
    assert "Hello\nWorld" in cleaned

def test_remove_consecutive_duplicate_lines(cleaner):
    text = "Line 1\nLine 1\nLine 2\nLine 2"
    cleaned = cleaner._remove_consecutive_duplicate_lines(text)
    assert cleaned.count("Line 1") == 1
    assert cleaned.count("Line 2") == 1

def test_full_cleaning_pipeline(cleaner):
    raw_text = (
        "## Welcome\n\n"
        "This is a [test link](http://example.com).\n"
        "This is a [test link](http://example.com).\n\n\n"
        "---"
    )
    cleaned_text = cleaner.clean_markdown_content(raw_text)
    assert "test link" not in cleaned_text
    assert "---" not in cleaned_text
    assert cleaned_text.count("\n") <= 2
    assert "Welcome" in cleaned_text
