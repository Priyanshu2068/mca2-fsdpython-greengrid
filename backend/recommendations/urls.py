from django.urls import path
from recommendations.views import (
    ECMRuleListView,
    RecommendationListView,
    RecommendationDetailView,
    RecommendationsSummaryView,
)

urlpatterns = [
    path('rules/', ECMRuleListView.as_view(), name='recommendations-rules-list'),
    path('summary/', RecommendationsSummaryView.as_view(), name='recommendations-summary'),
    path('', RecommendationListView.as_view(), name='recommendations-list'),
    path('<int:pk>/', RecommendationDetailView.as_view(), name='recommendations-detail'),
]
