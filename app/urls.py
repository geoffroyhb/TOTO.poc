from django.http import HttpResponse
from django.urls import path
from .views_quiz import start_test, question_page, result_page

def home(request):
    return HttpResponse("TOTO.poc est en ligne 🚀")

urlpatterns = [
    path("", home),
    path("test", start_test),  # lance une tentative
    path("q/<uuid:attempt_id>/<int:order>", question_page),
    path("result/<uuid:attempt_id>", result_page),
]
