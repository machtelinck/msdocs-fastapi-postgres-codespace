import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ajoutez le répertoire parent au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # Assurez-vous d'importer votre application principale correctement

client = TestClient(app)

def print_response_details(response):
    print(f"Response status code: {response.status_code}")
    print(f"Response content type: {response.headers.get('Content-Type')}")
    print(f"Response headers: {response.headers}")
    print(f"Response text: {response.text}")

def test_verify_cp_ville_rue():
    response = client.get("/verify_cp_ville_rue/", params={
        "code_postal": 59800,
        "nom_commune": "LILLE",
        "nom_rue": "SOLFERINO"
    })
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert "top_suggestions" in data, "Expected 'top_suggestions' in response JSON"
    assert any("rue de solferino" in suggestion["nom_afnor"].lower() for suggestion in data["top_suggestions"]), "Expected 'rue de solferino' in top suggestions"

def test_verify_cp_ville_rue_with_typo():
    response = client.get("/verify_cp_ville_rue/", params={
        "code_postal": 59800,
        "nom_commune": "LILLE",
        "nom_rue": "COURT DEBOUT"
    })
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert "top_suggestions" in data, "Expected 'top_suggestions' in response JSON"
    assert any("rue du court debout" in suggestion["nom_afnor"].lower() for suggestion in data["top_suggestions"]), "Expected 'rue du court debout' in top suggestions"

def test_calculate_features():
    response = client.get("/test_calculate_features/")
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert "features" in data, "Expected 'features' in response JSON"
    assert "damerau_levenshtein" in data["features"], "Expected 'damerau_levenshtein' in features"
    assert "jaro_winkler" in data["features"], "Expected 'jaro_winkler' in features"

def test_similarity():
    response = client.get("/test_similarity/")
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    data = response.json()
    assert "damerau_levenshtein" in data, "Expected 'damerau_levenshtein' in response JSON"
    assert "jaro_winkler" in data, "Expected 'jaro_winkler' in response JSON"
