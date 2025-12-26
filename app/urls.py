from django.http import HttpResponse
from django.urls import path
from .views import test_upload, restart_test

def home(request):
    return HttpResponse("TOTO.poc est en ligne 🚀")

urlpatterns = [
    path("", home),
    path("test", test_upload),
    path("restart", restart_test),  # 👈 OBLIGATOIRE
]
