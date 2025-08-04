import os
import sys
import json
import pytest
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.CustomJsonToOSM import JsonToOsmConverter, TimeSlot, OSMDayMapper, DateParser

# Test TimeSlot
def test_timeslot_valid():
    slot = TimeSlot("09:00", "17:00")
    assert slot.to_osm_format() == "09:00-17:00"

def test_timeslot_invalid_format():
    with pytest.raises(ValueError):
        TimeSlot("9:00", "17:00")
    with pytest.raises(ValueError):
        TimeSlot("09:00", "25:00")

# Test OSMDayMapper
def test_osm_day_mapper():
    assert OSMDayMapper.normalize_day("Lundi") == "Mo"
    assert OSMDayMapper.normalize_day("Mardi") == "Tu"
    assert OSMDayMapper.normalize_day("Unknown") is None

def test_compress_day_ranges():
    assert OSMDayMapper.compress_day_ranges(["Mo", "Tu", "We"]) == "Mo-We"
    assert OSMDayMapper.compress_day_ranges(["Mo", "We", "Fr"]) == "Mo,We,Fr"
    assert OSMDayMapper.compress_day_ranges(["Mo", "Tu", "Th", "Fr"]) == "Mo-Tu,Th-Fr"
    assert OSMDayMapper.compress_day_ranges([]) == ""

# Test DateParser
def test_date_parser():
    assert DateParser.parse_date_to_osm("25 decembre 2023") == "2023 Dec 25"
    assert DateParser.parse_date_to_osm("1er janvier 2024") == "2024 Jan 01"
    assert DateParser.parse_date_to_osm("2024-03-15") == "2024 Mar 15"
    assert DateParser.parse_date_to_osm("invalid date") is None

# Test JsonToOsmConverter
@pytest.fixture
def converter():
    return JsonToOsmConverter()

def test_weekly_schedule_simple(converter):
    data = {
        "horaires_ouverture": {
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {"ouvert": True, "creneaux": [{"debut": "09:00", "fin": "12:00"}]},
                        "mardi": {"ouvert": True, "creneaux": [{"debut": "09:00", "fin": "12:00"}]},
                        "mercredi": {"ouvert": False}
                    }
                }
            }
        }
    }
    result = converter.convert_to_osm(data)
    assert "hors_vacances_scolaires" in result.osm_periods
    # Expected: Mo-Tu 09:00-12:00; We off; Th-Su off
    assert "Mo-Tu 09:00-12:00" in result.osm_periods["hors_vacances_scolaires"]
    assert "We off" in result.osm_periods["hors_vacances_scolaires"]

def test_special_days_public_holidays(converter):
    data = {
        "horaires_ouverture": {
            "periodes": {
                "jours_feries": {
                    "source_found": True,
                    "mode": "ferme"
                }
            }
        }
    }
    result = converter.convert_to_osm(data)
    assert result.osm_periods.get("jours_feries") == "PH off"

def test_specific_special_day(converter):
    data = {
        "horaires_ouverture": {
            "periodes": {
                "jours_speciaux": {
                    "source_found": True,
                    "horaires_specifiques": {
                        "2023-12-25": {"ouvert": False}
                    }
                }
            }
        }
    }
    result = converter.convert_to_osm(data)
    assert result.osm_periods.get("jours_speciaux") == "2023-12-25 off"

def test_occurrence_in_schedule(converter):
    data = {
        "horaires_ouverture": {
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {
                            "ouvert": True,
                            "creneaux": [
                                {"debut": "10:00", "fin": "12:00", "occurence": [1, 3]}
                            ]
                        }
                    }
                }
            }
        }
    }
    result = converter.convert_to_osm(data)
    assert "Mo[1,3] 10:00-12:00" in result.osm_periods["hors_vacances_scolaires"]

def test_definitive_closure(converter):
    data = {
        "horaires_ouverture": {
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {"ouvert": False},
                        "mardi": {"ouvert": False},
                        "mercredi": {"ouvert": False},
                        "jeudi": {"ouvert": False},
                        "vendredi": {"ouvert": False},
                        "samedi": {"ouvert": False},
                        "dimanche": {"ouvert": False}
                    }
                }
            }
        }
    }
    result = converter.convert_to_osm(data)
    assert result.osm_periods.get("general") == "off"

@pytest.fixture
def create_test_json(tmp_path):
    """Create a dummy JSON file for testing file conversion."""
    json_content = {
        "horaires_ouverture": {
            "metadata": {"identifiant": "test_id"},
            "periodes": {
                "hors_vacances_scolaires": {
                    "source_found": True,
                    "horaires": {
                        "lundi": {"ouvert": True, "creneaux": [{"debut": "08:00", "fin": "18:00"}]}
                    }
                }
            }
        }
    }
    json_path = tmp_path / "test.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(json_content, f)
    return json_path

def test_convert_file(converter, create_test_json):
    """Test converting a whole JSON file."""
    results = converter.convert_file(create_test_json)
    assert "test_id" in results
    assert "hors_vacances_scolaires" in results["test_id"].osm_periods
    assert "Mo 08:00-18:00" in results["test_id"].osm_periods["hors_vacances_scolaires"]
