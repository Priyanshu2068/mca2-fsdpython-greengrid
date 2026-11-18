from django.urls import path
from benchmarking.views import (
    BuildingBenchmarkListView,
    FacilityBenchmarkScoreListView,
    FacilityRankingListView,
)

urlpatterns = [
    path('standards/', BuildingBenchmarkListView.as_view(), name='benchmarking-standards'),
    path('scores/', FacilityBenchmarkScoreListView.as_view(), name='benchmarking-scores'),
    path('ranking/', FacilityRankingListView.as_view(), name='benchmarking-ranking'),
]

