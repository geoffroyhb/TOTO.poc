from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import openpyxl


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


@csrf_exempt
def test_upload(request):
    if request.method == "GET":
        return render(request, "test_upload.html")

    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    # Charger le classeur (on garde les formules)
    try:
        wb = openpyxl.load_workbook(f, data_only=False)
    except Exception as e:
        return HttpResponse(f"Fichier illisible (.xlsx attendu) : {e}", status=400)

    ws = wb.active

    # --- Règles du test POC ---
    # Objectif : B2 doit contenir une formule qui somme B3:B7
    target_cell = ws["B2"]
    formula = target_cell.value

    # Barème /20
    score = 0
    feedback = []

    # 10 pts : B2 contient une formule (et pas une valeur en dur)
    if isinstance(formula, str) and formula.startswith("="):
        score += 10
        feedback.append("✅ Formule détectée en B2 (+10).")
    else:
        feedback.append(f"❌ B2 n'est pas une formule (valeur trouvée : {formula}) (+0).")
        # Si pas de formule, inutile d'aller plus loin (mais on renvoie un score)
        return HttpResponse(
            f"Score : {score}/20\n" + "\n".join(feedback),
            content_type="text/plain; charset=utf-8",
        )

    # 5 pts : la formule référence bien B3:B7 (tolérant sur SUM/SOMME/espaces)
    normalized = formula.replace(" ", "").upper()
    if "B3:B7" in normalized:
        score += 5
        feedback.append("✅ Plage B3:B7 trouvée dans la formule (+5).")
    else:
        feedback.append(f"⚠️ Plage attendue B3:B7 non trouvée dans la formule : {formula} (+0).")

    # 5 pts : cohérence du résultat (on calcule la somme attendue à partir des valeurs B3..B7)
    values = []
    for r in range(3, 8):
        v = _safe_float(ws[f"B{r}"].value)
        if v is not None:
            values.append(v)

    expected_sum = sum(values) if values else 0.0
    feedback.append(f"ℹ️ Somme attendue (à partir de B3:B7) = {expected_sum:g}")

    # Ici on ne peut pas recalculer Excel côté serveur (openpyxl ne calcule pas les formules).
    # Donc on attribue les 5 points si :
    # - il y a au moins 1 valeur numérique dans B3:B7
    # - et la formule est une somme (contient SOMME ou SUM)
    if values and ("SOMME" in normalized or "SUM" in normalized):
        score += 5
        feedback.append("✅ Formule de somme cohérente avec les données (+5).")
    else:
        feedback.append("⚠️ Impossible de valider la cohérence (données manquantes ou formule non reconnue) (+0).")

    # Verdict
    if score == 20:
        verdict = "🎉 Parfait !"
    elif score >= 15:
        verdict = "✅ Très bien"
    elif score >= 10:
        verdict = "🟠 Correct, mais améliorable"
    else:
        verdict = "🔴 À revoir"

    return HttpResponse(
        f"{verdict}\nScore : {score}/20\n\n" + "\n".join(feedback),
        content_type="text/plain; charset=utf-8",
    )
