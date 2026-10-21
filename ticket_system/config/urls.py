from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import render
from django.urls import include, path

from tickets import views


def handler403(request, exception):
    return render(request, "tickets/403.html", status=403)


def handler404(request, exception):
    return render(request, "tickets/404.html", status=404)


urlpatterns = [
    path("admin/", admin.site.urls),
    path("login/", views.TicketLoginView.as_view(), name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("", include("tickets.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
