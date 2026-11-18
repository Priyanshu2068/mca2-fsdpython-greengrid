from django.urls import path, include
from rest_framework.routers import DefaultRouter
from facilities.views import FacilityViewSet, RotateDataSourceKeyView

router = DefaultRouter()
router.register('', FacilityViewSet, basename='facility')

urlpatterns = [
    path('datasources/<int:pk>/rotate-key/', RotateDataSourceKeyView.as_view(), name='datasource-rotate-key'),
    path('', include(router.urls)),
]
