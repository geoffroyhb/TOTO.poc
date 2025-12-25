from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

@csrf_exempt
def test_upload(request):
    if request.method == "GET":
        return render(request, "test_upload.html")

    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    return HttpResponse(f"Fichier reçu ✅ : {f.name} ({f.size} bytes)")


