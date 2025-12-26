import uuid
from django.db import models


class Test(models.Model):
    title = models.CharField(max_length=200, default="Test - V1")
    duration_seconds = models.IntegerField(default=20 * 60)  # 20 min

    def __str__(self):
        return self.title


class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="questions")
    order = models.PositiveIntegerField()  # 1..40
    statement = models.TextField()

    a = models.CharField(max_length=300)
    b = models.CharField(max_length=300)
    c = models.CharField(max_length=300)
    d = models.CharField(max_length=300)

    correct = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
    )

    class Meta:
        unique_together = [("test", "order")]
        ordering = ["order"]

    def __str__(self):
        return f"Q{self.order} - {self.statement[:40]}"


class Attempt(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    test = models.ForeignKey(Test, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Attempt {self.id}"


class Answer(models.Model):
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected = models.CharField(
        max_length=1,
        choices=[("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")],
    )

    class Meta:
        unique_together = [("attempt", "question")]

    def __str__(self):
        return f"{self.attempt_id} Q{self.question.order}={self.selected}"
