from django.urls import path

from api.views import AnalyzeTripView, health_check

urlpatterns = [
    path("health", health_check, name="health-check"),
    path("analyze", AnalyzeTripView.as_view(), name="analyze-trip"),
]