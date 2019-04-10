from django.conf import settings
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.IndexView.as_view(), name="index"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
    path("logout/", views.LogoutUserView.as_view(), name="logout"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("openhumans/", include("openhumans.urls")),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
