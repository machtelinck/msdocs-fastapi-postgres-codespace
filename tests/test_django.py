import pytest
from django.test import Client
from django.urls import reverse

# Créez un client de test Django
client = Client()

def test_home_view():
    url = reverse('home')
    response = client.get(url)
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    

def test_verifier_rue_view():
    url = reverse('verifier_rue')
    response = client.get(url, {
        'code_postal': '59800',
        'nom_commune': 'LILLE',
        'nom_rue': 'SOLFERINO'
    })
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "Résultats de la vérification de rue" in response.content.decode(), "Expected 'Résultats de la vérification de rue' in response"

def test_verifier_rue_view_with_typo():
    url = reverse('verifier_rue')
    response = client.get(url, {
        'code_postal': '59800',
        'nom_commune': 'LILLE',
        'nom_rue': 'COURT DEBOUT'
    })
    assert response.status_code == 200, f"Expected status code 200, got {response.status_code}"
    assert "Résultats de la vérification de rue" in response.content.decode(), "Expected 'Résultats de la vérification de rue' in response"
