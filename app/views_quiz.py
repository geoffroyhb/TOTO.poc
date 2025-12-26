from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.http import HttpResponse
from .models import Test, Question, Attempt, Answer


def _remaining_seconds(attempt: Attempt) -> int:
    duration = attempt.test.duration_seconds
    elapsed = (timezone.now() - attempt.started_at).total_seconds()
    return max(0, int(duration - elapsed))


def start_test(request):
    test = Test.objects.first()
    if not test:
        # V1: on crée un test par défaut si absent
        test = Test.objects.create(title="Test - V1", duration_seconds=20 * 60)

    attempt = Attempt.objects.create(test=test)
    return redirect(f"/q/{attempt.id}/1")


def question_page(request, attempt_id, order: int):
    attempt = get_object_or_404(Attempt, id=attempt_id)
    remaining = _remaining_seconds(attempt)
    if remaining <= 0:
        return redirect(f"/result/{attempt.id}")

    q = get_object_or_404(Question, test=attempt.test, order=order)

    # réponse déjà donnée ?
    existing = Answer.objects.filter(attempt=attempt, question=q).first()

    if request.method == "POST":
        selected = request.POST.get("selected")
        if selected not in ("A", "B", "C", "D"):
            return HttpResponse("Réponse invalide", status=400)

        Answer.objects.update_or_create(
            attempt=attempt,
            question=q,
            defaults={"selected": selected},
        )

        # question suivante ou résultat
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
            "q": q,
            "order": order,
            "total": total,
            "selected": existing.selected if existing else None,
            "remaining_seconds": remaining,
        },
    )


def result_page(request, attempt_id):
    attempt = get_object_or_404(Attempt, id=attempt_id)
    qs = list(Question.objects.filter(test=attempt.test).order_by("order"))
    answers = {a.question_id: a.selected for a in Answer.objects.filter(attempt=attempt)}

    # Score /40 = 1 point par question correcte
    score = 0
    details = []
    for q in qs:
        sel = answers.get(q.id)
        ok = (sel == q.correct)
        if ok:
            score += 1
        details.append(
            {
                "order": q.order,
                "statement": q.statement,
                "selected": sel,
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
            "max_score": len(qs),
            "remaining_seconds": remaining,
            "details": details,
        },
    )
