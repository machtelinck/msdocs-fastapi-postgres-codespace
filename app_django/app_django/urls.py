from django.contrib import admin
from django.urls import path
from appli_django.views import verifier_rue, verify_address_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', verifier_rue, name='home'),  # Page d'accueil
    path('verifier_rue/', verifier_rue, name='verifier_rue'),
    path('verify_address/', verify_address_view, name='verify_address')
]
