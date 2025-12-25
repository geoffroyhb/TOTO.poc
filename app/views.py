from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import openpyxl

@csrf_exempt
def test_upload(request):
    if request.method == "GET":
        return render(request, "test_upload.html")

    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    wb = openpyxl.load_workbook(f, data_only=False)
    ws = wb.active

    cell = ws["B2"]
    value = cell.value

    if value is None:
        return HttpResponse("❌ B2 est vide")

    if not (isinstance(value, str) and value.startswith("=")):
        return HttpResponse("❌ B2 n'est pas une formule")

    return HttpResponse(f"✅ OK ! Formule détectée : {value}")
