import sys
import os
import pytest
from fastapi.testclient import TestClient

# Ajoutez le répertoire parent au PYTHONPATH
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app  # Assurez-vous d'importer votre application principale correctement
# ou
# from main_copy import app

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
    assert "SOLFERINO" in response.text, "Expected 'SOLFERINO' in response text"

def test_verify_cp_ville_rue_with_typo():
    response = client.get("/verify_cp_ville_rue/", params={
        "code_postal": 59800,
        "nom_commune": "LILLE",
        "nom_rue": "COURT DEBOUT"
    })
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "COURT DEBOUT" in response.text, "Expected 'COURT DEBOUT' in response text"

def test_calculate_features():
    response = client.get("/test_calculate_features/")
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "features" in response.text, "Expected 'features' in response text"

def test_similarity():
    response = client.get("/test_similarity/")
    print_response_details(response)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "damerau_levenshtein" in response.text, "Expected 'damerau_levenshtein' in response text"
