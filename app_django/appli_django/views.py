from django.shortcuts import render
import requests

def verifier_rue(request):
    code_postal = '59000'
    nom_commune = 'Lille'
    nom_rue = 'Soleferino'
    
    # Remplacez cette URL par l'URL de votre API FastAPI, en vous assurant d'utiliser le bon port
    url_api = f"http://localhost:8001/verify_cp_ville_rue/?code_postal={code_postal}&nom_commune={nom_commune}&nom_rue={nom_rue}"
    
    # Appeler l'API et récupérer les données
    reponse = requests.get(url_api)
    if reponse.status_code == 200 and reponse.content:
        donnees = reponse.json()
    else:
        donnees = {'erreur': 'Impossible de récupérer les données ou réponse vide'}

    # Passer les données au template
    return render(request, 'verifier_rue.html', {'donnees': donnees})
