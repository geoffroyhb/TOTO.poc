from django.http import HttpResponse
from django.urls import path
from .views import test_upload

def home(request):
    return HttpResponse("TOTO.poc est en ligne 🚀")

urlpatterns = [
    path("", home),
    path("test", test_upload),
]
