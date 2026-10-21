from django.urls import path

from tickets import views

urlpatterns = [
    path("", views.ticket_list, name="ticket_list"),
    path("tickets/new/", views.ticket_create, name="ticket_create"),
    path("tickets/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("tickets/<int:pk>/edit/", views.ticket_edit, name="ticket_edit"),
    path("tickets/<int:pk>/assign/", views.ticket_assign, name="ticket_assign"),
    path("tickets/<int:pk>/status/", views.ticket_update_status, name="ticket_update_status"),
    path("tickets/<int:pk>/comment/", views.add_comment, name="add_comment"),
    path("tickets/<int:pk>/attachment/", views.add_attachment, name="add_attachment"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("users/", views.user_management, name="user_management"),
    path("users/<int:user_id>/role/", views.change_role, name="change_role"),
    path("users/<int:user_id>/toggle/", views.toggle_user, name="toggle_user"),
    path("health/", views.health, name="health"),
]
