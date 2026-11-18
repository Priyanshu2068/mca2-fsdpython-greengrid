from django.urls import path, include
from rest_framework.routers import DefaultRouter
from billing.views import (
    UtilityProviderListView,
    TariffStructureListView,
    UtilityBillViewSet,
    BillReconciliationListView,
)

router = DefaultRouter()
router.register('bills', UtilityBillViewSet, basename='utility-bill')

urlpatterns = [
    path('providers/', UtilityProviderListView.as_view(), name='billing-providers'),
    path('tariffs/', TariffStructureListView.as_view(), name='billing-tariffs'),
    path('reconciliations/', BillReconciliationListView.as_view(), name='billing-reconciliations'),
    path('', include(router.urls)),
]
