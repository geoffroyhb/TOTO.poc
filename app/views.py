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

    # Charger le classeur
    try:
        wb = openpyxl.load_workbook(f, data_only=False)  # data_only=False pour lire la formule
    except Exception as e:
        return HttpResponse(f"Fichier illisible (pas un .xlsx ?) : {e}", status=400)

    ws = wb.active  # feuille 1

    # Règles POC : B2 doit contenir une FORMULE et pas une valeur en dur
    cell = ws["B2"]
    value = cell.value

    if value is None:
        return HttpResponse("❌ B2 est vide. Attendu : une formule de somme.", status=200)

    if not (isinstance(value, str) and value.startswith("=")):
        return HttpResponse(f"❌ B2 n'est pas une formule (valeur trouvée : {value}).", status=200)

    # Vérif simple : la formule doit référencer B3:B7 (tolérant)
    normalized = value.replace(" ", "").upper()

    if "B3:B7" not in normalized:
        return HttpResponse(f"⚠️ Formule détectée mais plage inattendue : {value}", status=200)

    return HttpResponse(f"✅ OK ! Formule trouvée en B2 : {value}", status=200)
