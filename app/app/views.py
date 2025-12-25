from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def test_upload(request):
    if request.method == "GET":
        return render(request, "test_upload.html")

    # POST : fichier uploadé
    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    # POC: on ne corrige pas encore, on confirme juste la réception
    return HttpResponse(f"Fichier reçu ✅ : {f.name} ({f.size} bytes)")
