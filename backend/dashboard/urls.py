from django.urls import path
from dashboard.views import (
    DashboardSummaryView,
    DashboardTrendsView,
    DashboardEnergyMixView,
    DashboardLoadBreakdownView,
)

urlpatterns = [
    path('summary/', DashboardSummaryView.as_view(), name='dashboard-summary'),
    path('trends/', DashboardTrendsView.as_view(), name='dashboard-trends'),
    path('energy-mix/', DashboardEnergyMixView.as_view(), name='dashboard-energy-mix'),
    path('load-breakdown/', DashboardLoadBreakdownView.as_view(), name='dashboard-load-breakdown'),
]
