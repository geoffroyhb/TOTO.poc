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

    # Timer via cookie (pas de session)
    start_ts = request.COOKIES.get("test_start_ts")
    if start_ts is None:
        start_ts = str(now)

    elapsed = now - int(start_ts)
    remaining = max(0, DURATION_SECONDS - elapsed)

    # GET : page test + timer
    if request.method == "GET":
        resp = render(request, "test_upload.html", {"remaining_seconds": remaining})
        if "test_start_ts" not in request.COOKIES:
            resp.set_cookie("test_start_ts", start_ts, max_age=DURATION_SECONDS, samesite="Lax")
        return resp

    # POST : si temps écoulé -> page résultat "temps écoulé"
    if remaining <= 0:
        return render(
            request,
            "result.html",
            {
                "verdict": "⏰ Temps écoulé",
                "score": 0,
                "remaining_seconds": 0,
                "feedback": ["Upload refusé : le temps est écoulé."],
            },
            status=403,
        )

    f = request.FILES.get("file")
    if not f:
        return render(
            request,
            "result.html",
            {
                "verdict": "❌ Fichier manquant",
                "score": 0,
                "remaining_seconds": remaining,
                "feedback": ["Aucun fichier n’a été reçu."],
            },
            status=400,
        )

    # Charger Excel
    try:
        wb = openpyxl.load_workbook(f, data_only=False)
    except Exception as e:
        return render(
            request,
            "result.html",
            {
                "verdict": "❌ Fichier invalide",
                "score": 0,
                "remaining_seconds": remaining,
                "feedback": [f"Le fichier n’est pas lisible (.xlsx attendu). Détail : {e}"],
            },
            status=400,
        )

    ws = wb.active
    formula = ws["B2"].value

    score = 0
    feedback = []

    # +10 si formule
    if isinstance(formula, str) and formula.startswith("="):
        score += 10
        feedback.append("✅ Formule détectée en B2 (+10).")
    else:
        feedback.append(f"❌ B2 n'est pas une formule (valeur trouvée : {formula}) (+0).")
        return render(
            request,
            "result.html",
            {
                "verdict": "🔴 À revoir",
                "score": score,
                "remaining_seconds": remaining,
                "feedback": feedback,
            },
            status=200,
        )

    # +5 si plage B3:B7
    normalized = formula.replace(" ", "").upper()
    if "B3:B7" in normalized:
        score += 5
        feedback.append("✅ Plage B3:B7 trouvée dans la formule (+5).")
    else:
        feedback.append(f"⚠️ Plage attendue B3:B7 non trouvée : {formula} (+0).")

    # +5 cohérence “formule de somme” + données présentes
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

    if score == 20:
        verdict = "🎉 Parfait !"
    elif score >= 15:
        verdict = "✅ Très bien"
    elif score >= 10:
        verdict = "🟠 Correct"
    else:
        verdict = "🔴 À revoir"

    return render(
        request,
        "result.html",
        {
            "verdict": verdict,
            "score": score,
            "remaining_seconds": remaining,
            "feedback": feedback,
        },
        status=200,
    )
