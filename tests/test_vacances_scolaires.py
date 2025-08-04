import os
import sys
import pytest
import polars as pl
import requests
from unittest.mock import patch, MagicMock

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.VacancesScolaires import get_vacances_scolaires

@patch("requests.get")
def test_get_vacances_scolaires_success(mock_get):
    """Test successfully fetching school holidays."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [
            {
                "description": "Vacances de la Toussaint",
                "start_date": "2023-10-21T00:00:00+00:00",
                "end_date": "2023-11-06T00:00:00+00:00",
                "zones": "Zone A, Zone B, Zone C",
                "annee_scolaire": "2023-2024"
            }
        ]
    }
    mock_get.return_value = mock_response

    df = get_vacances_scolaires(zone="A", annee_scolaire="2023-2024")

    assert isinstance(df, pl.DataFrame)
    assert not df.is_empty()
    assert df.shape == (1, 5)
    assert "description" in df.columns

@patch("requests.get")
def test_get_vacances_scolaires_http_error(mock_get):
    """Test handling of HTTP errors."""
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError
    mock_get.return_value = mock_response

    result = get_vacances_scolaires()
    assert result is None

@patch("requests.get")
def test_get_vacances_scolaires_no_results(mock_get):
    """Test handling of an empty response."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_get.return_value = mock_response

    df = get_vacances_scolaires()
    
    assert df is None

def test_get_vacances_scolaires_params_building():
    """Test that query parameters are built correctly."""
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {}
        mock_get.return_value = mock_response

        get_vacances_scolaires(
            localisation="Lyon",
            zone="A",
            annee_scolaire="2023-2024"
        )

        # Check that the 'where' clause was constructed correctly
        called_args, called_kwargs = mock_get.call_args
        params = called_kwargs.get("params", {})
        where_clause = params.get("where", "")

        assert "location like 'Lyon'" in where_clause
        assert "zones like 'Zone A'" in where_clause
        assert "annee_scolaire like '2023-2024'" in where_clause
