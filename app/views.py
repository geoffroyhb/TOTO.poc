from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
import openpyxl
import time

DURATION_SECONDS = 10 * 60  # 10 minutes


def _safe_float(x):
    try:
        return float(x)
    except Exception:
        return None


@csrf_exempt
def test_upload(request):
    now = int(time.time())

    # Démarrer le timer à la 1ère visite
    start_ts = request.session.get("test_start_ts")
    if not start_ts:
        request.session["test_start_ts"] = now
        start_ts = now

    elapsed = now - int(start_ts)
    remaining = DURATION_SECONDS - elapsed
    if remaining < 0:
        remaining = 0

    # GET : afficher la page + le timer restant
    if request.method == "GET":
        return render(request, "test_upload.html", {"remaining_seconds": remaining})

    # POST : si le temps est écoulé, on bloque
    if remaining <= 0:
        return HttpResponse(
            "⏰ Temps écoulé. Upload refusé.\n(Recharge /test pour relancer une nouvelle session.)",
            content_type="text/plain; charset=utf-8",
            status=403,
        )

    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    # --- Correction (score /20) ---
    try:
        wb = openpyxl.load_workbook(f, data_only=False)
    except Exception as e:
        return HttpResponse(f"Fichier illisible (.xlsx attendu) : {e}", status=400)

    ws = wb.active
    target_cell = ws["B2"]
    formula = target_cell.value

    score = 0
    feedback = []

    if isinstance(formula, str) and formula.startswith("="):
        score += 10
        feedback.append("✅ Formule détectée en B2 (+10).")
    else:
        feedback.append(f"❌ B2 n'est pas une formule (valeur trouvée : {formula}) (+0).")
        return HttpResponse(
            f"Score : {score}/20\n" + "\n".join(feedback),
            content_type="text/plain; charset=utf-8",
        )

    normalized = formula.replace(" ", "").upper()
    if "B3:B7" in normalized:
        score += 5
        feedback.append("✅ Plage B3:B7 trouvée dans la formule (+5).")
    else:
        feedback.append(f"⚠️ Plage attendue B3:B7 non trouvée dans la formule : {formula} (+0).")

    values = []
    for r in range(3, 8):
        v = _safe_float(ws[f"B{r}"].value)
        if v is not None:
            values.append(v)

    expected_sum = sum(values) if values else 0.0
    feedback.append(f"ℹ️ Somme attendue (B3:B7) = {expected_sum:g}")

    if values and ("SOMME" in normalized or "SUM" in normalized):
        score += 5
        feedback.append("✅ Formule de somme cohérente avec les données (+5).")
    else:
        feedback.append("⚠️ Impossible de valider la cohérence (+0).")

    verdict = "🎉 Parfait !" if score == 20 else ("✅ Très bien" if score >= 15 else ("🟠 Correct" if score >= 10 else "🔴 À revoir"))

    return HttpResponse(
        f"{verdict}\nScore : {score}/20\nTemps restant : {remaining}s\n\n" + "\n".join(feedback),
        content_type="text/plain; charset=utf-8",
    )
