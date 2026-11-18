from django.urls import path
from ingestion.views import (
    BulkReadingIngestionView,
    CSVReadingUploadView,
    RawReadingListView,
    BatchLogListView,
)

urlpatterns = [
    path('readings/bulk/', BulkReadingIngestionView.as_view(), name='ingestion-bulk'),
    path('readings/upload-csv/', CSVReadingUploadView.as_view(), name='ingestion-csv-upload'),
    path('readings/', RawReadingListView.as_view(), name='raw-readings-list'),
    path('batches/', BatchLogListView.as_view(), name='ingestion-batches-list'),
]
