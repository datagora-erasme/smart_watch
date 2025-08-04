import os
import sys
import pytest

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from smart_watch.utils.OSMToCustomJson import OSMParser, OsmToJsonConverter

@pytest.fixture
def parser():
    return OSMParser()

@pytest.fixture
def converter():
    return OsmToJsonConverter()

def test_parse_simple_schedule(parser):
    """Test parsing a simple weekly schedule."""
    osm_string = "Mo-Fr 09:00-17:00; Sa 10:00-14:00"
    parsed = parser.parse_osm_string(osm_string)
    
    assert parsed["weekly_schedule"]["lundi"].open
    assert parsed["weekly_schedule"]["lundi"].time_slots[0].start == "09:00"
    assert parsed["weekly_schedule"]["samedi"].time_slots[0].end == "14:00"
    assert not parsed["weekly_schedule"]["dimanche"].open

def test_parse_closed_day(parser):
    """Test parsing a closed day."""
    osm_string = "Mo-Fr 09:00-17:00; Sa-Su closed"
    parsed = parser.parse_osm_string(osm_string)
    
    assert not parsed["weekly_schedule"]["samedi"].open
    assert not parsed["weekly_schedule"]["dimanche"].open

def test_parse_special_date(parser):
    """Test parsing a specific date with a status."""
    osm_string = "2024 Dec 25 closed"
    parsed = parser.parse_osm_string(osm_string)
    
    assert len(parsed["special_dates"]) == 1
    special_date = parsed["special_dates"][0]
    assert special_date.date == "2024-12-25"
    assert special_date.status == "ferme"

def test_parse_with_occurrence(parser):
    """Test parsing a schedule with week occurrences."""
    osm_string = "Mo[1,3] 10:00-12:00"
    parsed = parser.parse_osm_string(osm_string)
    
    schedule = parsed["weekly_schedule"]["lundi"]
    assert schedule.open
    assert schedule.time_slots[0].occurrence == [1, 3]

def test_full_conversion(converter):
    """Test the full conversion from OSM string to custom JSON."""
    osm_string = "Mo-Fr 08:00-18:00; PH off"
    metadata = {"identifiant": "test_place"}
    
    json_result = converter.convert_osm_string(osm_string, metadata)
    
    assert "horaires_ouverture" in json_result
    periodes = json_result["horaires_ouverture"]["periodes"]
    
    # Check regular hours
    regular_hours = periodes["hors_vacances_scolaires"]["horaires"]
    assert regular_hours["lundi"]["ouvert"]
    assert regular_hours["lundi"]["creneaux"][0]["debut"] == "08:00"
    
    # Check public holidays
    ph_schedule = periodes["jours_feries"]
    assert ph_schedule["source_found"]
    assert ph_schedule["mode"] == "ferme"

def test_permanently_closed_conversion(converter):
    """Test conversion for a permanently closed place."""
    osm_string = "closed"
    json_result = converter.convert_osm_string(osm_string)
    
    extraction_info = json_result["horaires_ouverture"]["extraction_info"]
    assert extraction_info["permanently_closed"]
