from django.http import HttpResponse
from django.urls import path

def home(request):
    return HttpResponse("TOTO.poc est en ligne 🚀")

urlpatterns = [
    path("", home),
]
