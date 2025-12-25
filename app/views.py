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

    if request.method == "GET":
        resp = render(request, "test_upload.html", {"remaining_seconds": remaining})
        # on pose le cookie au 1er GET
        if "test_start_ts" not in request.COOKIES:
            resp.set_cookie("test_start_ts", start_ts, max_age=DURATION_SECONDS, samesite="Lax")
        return resp

    if remaining <= 0:
        return HttpResponse(
            "⏰ Temps écoulé. Upload refusé.\n(Recharge /test pour relancer une nouvelle session.)",
            content_type="text/plain; charset=utf-8",
            status=403,
        )

    f = request.FILES.get("file")
    if not f:
        return HttpResponse("Aucun fichier reçu", status=400)

    try:
        wb = openpyxl.load_workbook(f, data_only=False)
    except Exception as e:
        return HttpResponse(f"Fichier illisible (.xlsx attendu) : {e}", status=400)

    ws = wb.active
    formula = ws["B2"].value

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
        feedback.append(f"⚠️ Plage attendue B3:B7 non trouvée : {formula} (+0).")

    values = []
    for r in range(3, 8):
        v = _safe_float(ws[f"B{r}"].value)
        if v is not None:
            values.append(v)

    expected_sum = sum(values) if values else 0.0
    feedback.append(f"ℹ️ Somme attendue (B3:B7) = {expected_sum:g}")

    if values and ("SOMME" in normalized or "SUM" in normalized):
        score += 5
        feedback.append("✅ Formule de somme cohérente (+5).")
    else:
        feedback.append("⚠️ Cohérence non validée (+0).")

    verdict = "🎉 Parfait !" if score == 20 else ("✅ Très bien" if score >= 15 else ("🟠 Correct" if score >= 10 else "🔴 À revoir"))

    return HttpResponse(
        f"{verdict}\nScore : {score}/20\nTemps restant : {remaining}s\n\n" + "\n".join(feedback),
        content_type="text/plain; charset=utf-8",
    )
