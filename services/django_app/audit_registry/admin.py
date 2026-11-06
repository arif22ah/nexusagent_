from django.contrib import admin

from .models import ExecutionAuditRecord, ManagedAgentTool


@admin.register(ManagedAgentTool)
class ManagedAgentToolAdmin(admin.ModelAdmin):
    list_display = ("name", "is_sandboxed", "created_at")
    search_fields = ("name", "description")


@admin.register(ExecutionAuditRecord)
class ExecutionAuditRecordAdmin(admin.ModelAdmin):
    list_display = ("session_id", "neural_confidence", "timestamp")
    list_filter = ("timestamp",)
