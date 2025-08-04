import os
import sys
import pytest
import requests
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.JoursFeries import get_jours_feries

@patch("requests.get")
def test_get_jours_feries_success(mock_get):
    """Test successfully fetching public holidays."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "2024-01-01": "Jour de l'an",
        "2024-04-01": "Lundi de Pâques",
    }
    mock_get.return_value = mock_response

    holidays = get_jours_feries(zone="metropole", annee=2024)
    
    assert "2024-01-01" in holidays
    assert holidays["2024-01-01"] == "Jour de l'an"
    mock_get.assert_called_once_with(
        "https://calendrier.api.gouv.fr/jours-feries/metropole/2024.json",
        timeout=30
    )

@patch("requests.get")
def test_get_jours_feries_http_error(mock_get):
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
    mock_get.return_value = mock_response

    with pytest.raises(requests.exceptions.HTTPError):
        get_jours_feries(annee=2024)

def test_get_jours_feries_current_year():
    """Test that the current year is used by default."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response
        
        get_jours_feries()
        
        current_year = datetime.now().year
        expected_url = f"https://calendrier.api.gouv.fr/jours-feries/metropole/{current_year}.json"
        mock_get.assert_called_with(expected_url, timeout=30)
