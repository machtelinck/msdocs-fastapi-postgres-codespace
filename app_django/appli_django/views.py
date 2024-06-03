from django.shortcuts import render
import requests

def verifier_rue(request):
    code_postal = request.GET.get('code_postal', '59000')
    nom_commune = request.GET.get('nom_commune', 'LILLE')
    nom_rue = request.GET.get('nom_rue', 'SOLFERINO')

    params = {
        'code_postal': code_postal,
        'nom_commune': nom_commune,
        'nom_rue': nom_rue,
    }
    
    url_api = "http://localhost:8000/verify_cp_ville_rue/"
    reponse = requests.get(url_api, params=params)

    if reponse.status_code == 200 and reponse.content:
        donnees = reponse.json()
        top_suggestions = donnees.get('top_suggestions', [])
    else:
        donnees = {'erreur': 'Impossible de récupérer les données ou réponse vide'}
        top_suggestions = []

    return render(request, 'verifier_rue.html', {'donnees': donnees, 'top_suggestions': top_suggestions})

def verify_address_view(request):
    return render(request, 'verify_address.html')
