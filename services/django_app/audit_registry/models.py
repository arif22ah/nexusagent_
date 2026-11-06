from django.db import models


class ManagedAgentTool(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    source_code = models.TextField()
    is_sandboxed = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} [Safe: {self.is_sandboxed}]"


class ExecutionAuditRecord(models.Model):
    session_id = models.CharField(max_length=128)
    query_text = models.TextField()
    response_text = models.TextField()
    neural_confidence = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.session_id} @ {self.timestamp:%Y-%m-%d %H:%M}"
