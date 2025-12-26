from django.http import HttpResponse
from django.urls import path
from .views_quiz import join_page, question_page, result_page, seed_questions, create_session

def home(request):
    return HttpResponse("TOTO.poc est en ligne 🚀")

urlpatterns = [
    path("", home),
    path("join", join_page),
    path("q/<uuid:attempt_id>/<int:order>", question_page),
    path("result/<uuid:attempt_id>", result_page),

    # admin / seed
    path("seed", seed_questions),
    path("create-session", create_session),
]
