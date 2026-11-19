from django.urls import path
from renewables.views import (
    SolarAssetListView,
    SolarGenerationListView,
    SolarSelfConsumptionView,
    GridEventListView,
    CarbonEmissionsView,
    CarbonFactorListView,
)

urlpatterns = [
    path('solar-assets/', SolarAssetListView.as_view(), name='renewables-solar-assets'),
    path('generation/', SolarGenerationListView.as_view(), name='renewables-generation'),
    path('self-consumption/', SolarSelfConsumptionView.as_view(), name='renewables-self-consumption'),
    path('grid-events/', GridEventListView.as_view(), name='renewables-grid-events'),
    path('emissions/', CarbonEmissionsView.as_view(), name='renewables-emissions'),
    path('carbon-factors/', CarbonFactorListView.as_view(), name='renewables-carbon-factors'),
]

