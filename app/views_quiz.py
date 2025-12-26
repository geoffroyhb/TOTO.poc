import os
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from .models import Test, Question, Attempt, Answer


# -------------------------------
# UTILITAIRE : temps restant
# -------------------------------
def _remaining_seconds(attempt: Attempt) -> int:
    duration = attempt.test.duration_seconds
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    return max(0, int(duration - elapsed))


# -------------------------------
# LANCER LE TEST
# -------------------------------
def start_test(request):
    test = Test.objects.first()
    if not test:
        return HttpResponse(
            "Aucun test n'existe encore. Lance d'abord /seed pour créer les questions.",
            status=500,
        )

    attempt = Attempt.objects.create(test=test)
    return redirect(f"/q/{attempt.id}/1")


# -------------------------------
# PAGE QUESTION (QCM)
# -------------------------------
def question_page(request, attempt_id, order: int):
    attempt = get_object_or_404(Attempt, id=attempt_id)

    remaining = _remaining_seconds(attempt)
    if remaining <= 0:
        return redirect(f"/result/{attempt.id}")

    question = get_object_or_404(
        Question,
        test=attempt.test,
        order=order,
    )

    existing = Answer.objects.filter(
        attempt=attempt,
        question=question,
    ).first()

    if request.method == "POST":
        selected = request.POST.get("selected")
        if selected not in ("A", "B", "C", "D"):
            return HttpResponse("Réponse invalide", status=400)

        Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={"selected": selected},
        )

        next_order = order + 1
        if Question.objects.filter(test=attempt.test, order=next_order).exists():
            return redirect(f"/q/{attempt.id}/{next_order}")

        return redirect(f"/result/{attempt.id}")

    total = Question.objects.filter(test=attempt.test).count()

    return render(
        request,
        "quiz_question.html",
        {
            "attempt_id": str(attempt.id),
            "q": question,
            "order": order,
            "total": total,
            "selected": existing.selected if existing else None,
            "remaining_seconds": remaining,
        },
    )


# -------------------------------
# RÉSULTAT FINAL (SCORE /40)
# -------------------------------
def result_page(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id)

    questions = list(
        Question.objects.filter(test=attempt.test).order_by("order")
    )

    answers = {
        a.question_id: a.selected
        for a in Answer.objects.filter(attempt=attempt)
    }

    score = 0
    details = []

    for q in questions:
        selected = answers.get(q.id)
        ok = selected == q.correct
        if ok:
            score += 1

        details.append(
            {
                "order": q.order,
                "statement": q.statement,
                "selected": selected,
                "correct": q.correct,
                "ok": ok,
            }
        )

    remaining = _remaining_seconds(attempt)

    return render(
        request,
        "quiz_result.html",
        {
            "attempt_id": str(attempt.id),
            "score": score,
            "max_score": len(questions),
            "remaining_seconds": remaining,
            "details": details,
        },
    )


# -------------------------------
# SEED DES QUESTIONS (1 CLIC)
# -------------------------------
def seed_questions(request):
    key = request.GET.get("key")
    if not key or key != os.environ.get("SEED_KEY"):
        return HttpResponse("Forbidden", status=403)

    test, _ = Test.objects.get_or_create(
        title="Test - V1",
        defaults={"duration_seconds": 20 * 60},
    )

    # 👉 EXEMPLE (3 questions) – remplace par tes 40
    questions = [
        {
            "order": 1,
            "statement": "Combien font 2 + 2 ?",
            "a": "3",
            "b": "4",
            "c": "5",
            "d": "22",
            "correct": "B",
        },
        {
            "order": 2,
            "statement": "Quelle fonction Excel calcule une somme ?",
            "a": "MOYENNE",
            "b": "SOMME",
            "c": "MAX",
            "d": "SI",
            "correct": "B",
        },
        {
            "order": 3,
            "statement": "En SQL, quelle clause filtre les lignes ?",
            "a": "GROUP BY",
            "b": "ORDER BY",
            "c": "WHERE",
            "d": "JOIN",
            "correct": "C",
        },
    ]

    created = 0
    updated = 0

    for q in questions:
        obj, was_created = Question.objects.update_or_create(
            test=test,
            order=q["order"],
            defaults={
                "statement": q["statement"],
                "a": q["a"],
                "b": q["b"],
                "c": q["c"],
                "d": q["d"],
                "correct": q["correct"],
            },
        )
        if was_created:
            created += 1
        else:
            updated += 1

    return HttpResponse(
        f"Seed OK — created={created}, updated={updated}",
        status=200,
    )
