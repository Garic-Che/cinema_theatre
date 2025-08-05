from django.contrib import admin
from .models import TemplateDB, ContentDB, NotificationDB, ScheduleEventDB


class TemplateDBAdmin(admin.ModelAdmin):
    list_display = ("id", "template_type", "created")
    search_fields = ("template_type", "template")
    list_filter = ("created",)


admin.site.register(TemplateDB, TemplateDBAdmin)


class ContentDBAdmin(admin.ModelAdmin):
    list_display = ("key", "created")
    search_fields = ("key", "value")


admin.site.register(ContentDB, ContentDBAdmin)


class NotificationDBAdmin(admin.ModelAdmin):
    list_display = ("id", "template", "to_id", "get_send_by_display", "sent", "created")
    list_filter = ("sent", "created", "send_by")
    fieldsets = (
        (None, {"fields": ("template", "content_id", "send_by", "to_id")}),
        ("Статус", {"fields": ("sent",), "classes": ("collapse",)}),
    )
    actions = ["mark_as_sent"]

    def mark_as_sent(self, request, queryset):
        queryset.update(sent=True)

    mark_as_sent.short_description = "Пометить как отправленные"


admin.site.register(NotificationDB, NotificationDBAdmin)


class ScheduleEventDBAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "template",
        "receiver_group_name",
        "get_send_by_display",
        "next_send",
        "once",
    )
    list_filter = ("once", "receiver_group_name", "send_by")
    fieldsets = (
        (None, {"fields": ("template", "send_by", "receiver_group_name")}),
        ("Расписание", {"fields": ("period", "next_send", "once")}),
    )


admin.site.register(ScheduleEventDB, ScheduleEventDBAdmin)
