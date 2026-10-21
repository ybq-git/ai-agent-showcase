from django.contrib import admin

from tickets.models import Attachment, Category, Comment, StatusLog, Ticket, UserProfile


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "status", "priority", "created_by", "assigned_to", "created_at")
    list_filter = ("status", "priority", "category")
    search_fields = ("title", "description")


admin.site.register(Category)
admin.site.register(Comment)
admin.site.register(Attachment)
admin.site.register(StatusLog)
admin.site.register(UserProfile)
