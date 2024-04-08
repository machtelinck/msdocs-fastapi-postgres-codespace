from django.contrib import admin
from django.urls import path
# Importez la vue depuis l'application
from appli_django.views import verifier_rue



urlpatterns = [
    path("admin/", admin.site.urls),
    path('', verifier_rue, name='home'),  # Page d'accueil
    path('verifier_rue/', verifier_rue, name='verifier_rue'),
]
