"""
GreenGrid Ingestion Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework import status
from drf_spectacular.utils import extend_schema

from ingestion.serializers import (
    BulkIngestionRequestSerializer,
    BulkIngestionResponseSerializer,
    RawReadingSerializer,
    BatchLogSerializer,
    CSVUploadSerializer,
)
from ingestion.services import ingest_bulk_readings, process_csv_reading_file
from ingestion.selectors import list_raw_readings, list_batches
from facilities.services import validate_api_key

class BulkReadingIngestionView(APIView):
    """
    High-throughput idempotent endpoint for ingesting up to 5000 15-minute readings.
    Supports X-API-Key header authentication for IoT devices, or Session auth for Admin/Engineer.
    """
    permission_classes = [AllowAny]
    parser_classes = [JSONParser]

    @extend_schema(
        request=BulkIngestionRequestSerializer,
        responses={201: BulkIngestionResponseSerializer}
    )
    def post(self, request, *args, **kwargs):
        # 1. Check for X-API-Key header
        api_key = request.headers.get('X-API-Key')
        datasource = None
        user = None

        if api_key:
            datasource = validate_api_key(api_key)
            if not datasource:
                return Response(
                    {
                        'error': {
                            'status': status.HTTP_401_UNAUTHORIZED,
                            'code': 'INVALID_API_KEY',
                            'message': 'The provided X-API-Key is invalid, revoked, or expired.',
                            'details': {'header': ['Invalid credentials.']}
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )
        else:
            # 2. Check session authentication
            if not request.user or not request.user.is_authenticated:
                return Response(
                    {
                        'error': {
                            'status': status.HTTP_401_UNAUTHORIZED,
                            'code': 'AUTHENTICATION_REQUIRED',
                            'message': 'Either a valid X-API-Key header or authenticated session is required.',
                            'details': {'auth': ['Missing authentication credentials.']}
                        }
                    },
                    status=status.HTTP_401_UNAUTHORIZED
                )

            # Role check: only admin or field_engineer
            user_role = getattr(request.user, 'role', '')
            if user_role not in ('admin', 'field_engineer') and not request.user.is_superuser:
                return Response(
                    {
                        'error': {
                            'status': status.HTTP_403_FORBIDDEN,
                            'code': 'PERMISSION_DENIED',
                            'message': 'Only field engineers or administrators can ingest telemetry data.',
                            'details': {'role': ['Insufficient permissions.']}
                        }
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            user = request.user

        # 3. Parse and validate readings payload
        serializer = BulkIngestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        readings_data = serializer.validated_data['readings']

        # 4. Ingest readings idempotently
        result = ingest_bulk_readings(readings_data, datasource=datasource, user=user, source_type='api_bulk')
        return Response(result, status=status.HTTP_201_CREATED)

class CSVReadingUploadView(APIView):
    """
    Processes historical or offline telemetry batches uploaded as CSV files.
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(request=CSVUploadSerializer)
    def post(self, request, *args, **kwargs):
        user_role = getattr(request.user, 'role', '')
        if user_role not in ('admin', 'field_engineer') and not request.user.is_superuser:
            return Response(
                {
                    'error': {
                        'status': status.HTTP_403_FORBIDDEN,
                        'code': 'PERMISSION_DENIED',
                        'message': 'Only field engineers or administrators can upload CSV telemetry.',
                        'details': {'role': ['Insufficient permissions.']}
                    }
                },
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CSVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        file_obj = serializer.validated_data['file']

        result = process_csv_reading_file(file_obj, user=request.user)
        return Response(result, status=status.HTTP_201_CREATED)

class RawReadingListView(APIView):
    """
    Queries raw readings with facility, meter, and time range filters.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: RawReadingSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        meter_id = request.query_params.get('meter_id')
        meter_identifier = request.query_params.get('meter_identifier')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        qs = list_raw_readings(
            user=request.user,
            facility_id=facility_id,
            meter_id=meter_id,
            meter_identifier=meter_identifier,
            start_time=start_time,
            end_time=end_time
        )
        # Apply DRF pagination
        page = self.paginate_queryset(qs)
        if page is not None:
            serializer = RawReadingSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = RawReadingSerializer(qs[:100], many=True)
        return Response(serializer.data)

    @property
    def paginator(self):
        if not hasattr(self, '_paginator'):
            from core.pagination import StandardResultsSetPagination
            self._paginator = StandardResultsSetPagination()
        return self._paginator

    def paginate_queryset(self, queryset):
        return self.paginator.paginate_queryset(queryset, self.request, view=self)

    def get_paginated_response(self, data):
        return self.paginator.get_paginated_response(data)

class BatchLogListView(APIView):
    """
    Lists ingestion audit logs and batch summaries.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: BatchLogSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        source_type = request.query_params.get('source_type')
        batches = list_batches(user=request.user, source_type=source_type)
        serializer = BatchLogSerializer(batches[:50], many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
