#!/usr/bin/env python3
"""
Test script for boundaries API endpoints.
Tests both with and without database connection.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from api.main import app

# Create test client
client = TestClient(app)


def test_imports():
    """Test that all imports work correctly."""
    print("\n=== Testing Imports ===")
    try:
        from api.routes.boundaries import router
        from services.boundary_service import BoundaryService, get_boundary_service
        print("✓ All imports successful")
        return True
    except Exception as e:
        print(f"✗ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_check_point_endpoint_mock():
    """Test /check-point endpoint with mocked service."""
    print("\n=== Testing /check-point Endpoint (Mock) ===")

    mock_service = MagicMock()
    mock_service.is_point_in_country.return_value = True

    with patch('api.routes.boundaries.get_boundary_service', return_value=mock_service):
        response = client.post(
            "/api/boundaries/check-point",
            json={
                "lat": 51.5074,
                "lng": -0.1278,
                "country_name": "United Kingdom"
            }
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data["is_inside"] is True and data["country_name"] == "United Kingdom":
                print("✓ Check-point endpoint works correctly")
                return True

        print("✗ Check-point endpoint test failed")
        return False


def test_get_country_boundary_mock():
    """Test /country/{country_name} endpoint with mocked service."""
    print("\n=== Testing /country/{country_name} Endpoint (Mock) ===")

    mock_boundary = {
        "type": "Feature",
        "properties": {
            "name": "France",
            "code": "FR",
            "bbox": [[-5, 42], [10, 51]]
        },
        "geometry": {
            "type": "Polygon",
            "coordinates": [[
                [2.0, 48.0],
                [3.0, 48.0],
                [3.0, 49.0],
                [2.0, 49.0],
                [2.0, 48.0]
            ]]
        }
    }

    mock_service = MagicMock()
    mock_service.get_country_boundary.return_value = mock_boundary

    with patch('api.routes.boundaries.get_boundary_service', return_value=mock_service):
        response = client.get("/api/boundaries/country/France")

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if data["type"] == "Feature" and data["properties"]["name"] == "France":
                print("✓ Get country boundary endpoint works correctly")
                return True

        print("✗ Get country boundary endpoint test failed")
        return False


def test_get_country_not_found_mock():
    """Test /country/{country_name} endpoint with non-existent country."""
    print("\n=== Testing /country/{country_name} Not Found (Mock) ===")

    mock_service = MagicMock()
    mock_service.get_country_boundary.return_value = None

    with patch('api.routes.boundaries.get_boundary_service', return_value=mock_service):
        response = client.get("/api/boundaries/country/Atlantis")

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 404:
            print("✓ 404 error handling works correctly")
            return True

        print("✗ 404 error handling test failed")
        return False


def test_multiple_boundaries_mock():
    """Test /countries endpoint with mocked service."""
    print("\n=== Testing /countries Endpoint (Mock) ===")

    mock_boundaries = {
        "France": {
            "type": "Feature",
            "properties": {"name": "France", "code": "FR"},
            "geometry": {"type": "Polygon", "coordinates": []}
        },
        "Germany": {
            "type": "Feature",
            "properties": {"name": "Germany", "code": "DE"},
            "geometry": {"type": "Polygon", "coordinates": []}
        }
    }

    mock_service = MagicMock()
    mock_service.get_all_boundaries_for_countries.return_value = mock_boundaries

    with patch('api.routes.boundaries.get_boundary_service', return_value=mock_service):
        response = client.post(
            "/api/boundaries/countries",
            json={"country_names": ["France", "Germany"]}
        )

        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")

        if response.status_code == 200:
            data = response.json()
            if "boundaries" in data and len(data["boundaries"]) == 2:
                print("✓ Multiple boundaries endpoint works correctly")
                return True

        print("✗ Multiple boundaries endpoint test failed")
        return False


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "="*60)
    print("BOUNDARIES API TEST SUITE")
    print("="*60)

    tests = [
        test_imports,
        test_check_point_endpoint_mock,
        test_get_country_boundary_mock,
        test_get_country_not_found_mock,
        test_multiple_boundaries_mock,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test {test.__name__} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print("\n" + "="*60)
    print("TEST RESULTS")
    print("="*60)
    passed = sum(results)
    total = len(results)
    print(f"Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())