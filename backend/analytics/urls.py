from django.urls import path
from analytics.views import (
    HourlyRollupListView,
    DailyRollupListView,
    AnomalyAlertListView,
    AnomalyAlertDetailView,
)

urlpatterns = [
    path('rollups/hourly/', HourlyRollupListView.as_view(), name='hourly-rollups'),
    path('rollups/daily/', DailyRollupListView.as_view(), name='daily-rollups'),
    path('alerts/', AnomalyAlertListView.as_view(), name='anomaly-alerts-list'),
    path('alerts/<int:pk>/', AnomalyAlertDetailView.as_view(), name='anomaly-alert-detail'),
]

