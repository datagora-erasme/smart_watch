import os
import sys
import pytest
import polars as pl
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.CSVToPolars import CSVToPolars

@pytest.fixture
def create_test_csv(tmp_path):
    """Create a dummy CSV file for testing."""
    csv_content = "col1,col2,col3\n1,a,x\n2,b,y\n3,c,z"
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(csv_content)
    return csv_path

def test_load_csv_from_local_path(create_test_csv):
    """Test loading a CSV from a local file path."""
    loader = CSVToPolars(source=str(create_test_csv), separator=",")
    df = loader.load_csv()
    assert isinstance(df, pl.DataFrame)
    assert df.shape == (3, 3)
    assert df.columns == ["col1", "col2", "col3"]

@patch("requests.get")
def test_load_csv_from_url(mock_get, tmp_path):
    """Test loading a CSV from a URL."""
    csv_content = "col1;col2\n1;a\n2;b"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = csv_content.encode("utf-8")
    mock_get.return_value = mock_response

    loader = CSVToPolars(source="http://test.com/test.csv", separator=";")
    df = loader.load_csv()

    assert isinstance(df, pl.DataFrame)
    assert df.shape == (2, 2)
    assert df.columns == ["col1", "col2"]
    mock_get.assert_called_once_with("http://test.com/test.csv", timeout=30)

def test_auto_detect_separator(tmp_path):
    """Test automatic separator detection."""
    csv_content = "col1;col2|col3\n1;a|x\n2;b|y"
    csv_path = tmp_path / "test_sep.csv"
    # Write with a different separator to test detection
    csv_path.write_text(csv_content.replace("|", ";"))

    loader = CSVToPolars(source=str(csv_path), separator="auto")
    df = loader.load_csv()
    # The sniffer should detect ';'
    assert loader.separator == ";"
    assert df.shape == (2, 3)

def test_file_not_found():
    """Test FileNotFoundError for a non-existent file."""
    loader = CSVToPolars(source="non_existent_file.csv")
    with pytest.raises(FileNotFoundError):
        loader.load_csv()

def test_empty_csv(tmp_path):
    """Test loading an empty CSV file."""
    csv_path = tmp_path / "empty.csv"
    csv_path.write_text("")
    loader = CSVToPolars(source=str(csv_path))
    df = loader.load_csv()
    assert df.is_empty()

def test_no_header(tmp_path):
    """Test loading a CSV with no header."""
    csv_content = "1,a,x\n2,b,y"
    csv_path = tmp_path / "no_header.csv"
    csv_path.write_text(csv_content)
    loader = CSVToPolars(source=str(csv_path), has_header=False, separator=",")
    df = loader.load_csv()
    assert df.shape == (2, 3)
    # Polars creates default column names
    assert df.columns == ["column_1", "column_2", "column_3"]
