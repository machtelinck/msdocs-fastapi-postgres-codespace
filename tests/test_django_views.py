# tests/test_django_views.py
import pytest
from django.urls import reverse
from django.test import Client

@pytest.mark.django_db
def test_home_view():
    client = Client()
    url = reverse('home')
    response = client.get(url)
    assert response.status_code == 200
    assert "Bienvenue sur notre site!" in response.content.decode('utf-8')

@pytest.mark.django_db
def test_verifier_rue_view():
    client = Client()
    url = reverse('verifier_rue')
    response = client.get(url, {
        'code_postal': '59000',
        'nom_commune': 'LILLE',
        'nom_rue': 'SOLFERINO'
    })
    assert response.status_code == 200
    assert "Résultats de la vérification de rue" in response.content.decode('utf-8')

@pytest.mark.django_db
def test_verifier_rue_view_with_typo():
    client = Client()
    url = reverse('verifier_rue')
    response = client.get(url, {
        'code_postal': '59000',
        'nom_commune': 'LILLE',
        'nom_rue': 'COURT DEBOUT'
    })
    assert response.status_code == 200
    assert "Suggestions de rues" in response.content.decode('utf-8')
