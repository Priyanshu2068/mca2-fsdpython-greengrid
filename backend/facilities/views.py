"""
GreenGrid Facilities Views.
"""

from accounts.services import record_audit_log
from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import Http404

from facilities.models import Facility, Building, Meter, DataSource
from facilities.serializers import (
    FacilitySerializer,
    BuildingSerializer,
    MeterSerializer,
    DataSourceSerializer,
    DataSourceCreateResponseSerializer,
)
from facilities.selectors import (
    list_facilities_for_user,
    get_facility_for_user,
    list_buildings_for_facility,
    list_meters_for_facility,
    list_datasources_for_facility,
)
from facilities.services import (
    create_facility,
    create_building,
    register_meter,
    generate_datasource_api_key,
    rotate_datasource_api_key,
)
from core.permissions import RolePermission

class FacilityViewSet(viewsets.ModelViewSet):
    """
    Facility management and scoped lookup.
    """
    serializer_class = FacilitySerializer
    permission_classes = [IsAuthenticated, RolePermission]

    role_permissions = {
        'admin': ['list', 'retrieve', 'create', 'update', 'partial_update', 'destroy', 'buildings', 'meters', 'datasources'],
        'customer': ['list', 'retrieve', 'buildings', 'meters'],
        'field_engineer': ['list', 'retrieve', 'buildings', 'meters', 'datasources']
    }

    def get_queryset(self):
        facility_type = self.request.query_params.get('facility_type')
        city = self.request.query_params.get('city')
        return list_facilities_for_user(self.request.user, facility_type=facility_type, city=city)

    def get_object(self):
        return get_facility_for_user(self.kwargs['pk'], self.request.user)

    def perform_create(self, serializer):
        facility = create_facility(dict(serializer.validated_data))
        serializer.instance = facility
        record_audit_log(
            user=self.request.user, action='CREATE_FACILITY', resource_type='Facility', resource_id=facility.id,
            ip_address=self.request.META.get('REMOTE_ADDR'), details={'code': facility.code, 'name': facility.name},
        )

    @action(detail=True, methods=['get', 'post'], url_path='buildings')
    def buildings(self, request, pk=None):
        facility = self.get_object()
        if request.method == 'GET':
            buildings = list_buildings_for_facility(facility)
            return Response(BuildingSerializer(buildings, many=True).data)

        # POST: Admin only
        if getattr(request.user, 'role', '') != 'admin' and not request.user.is_superuser:
            return Response(
                {'error': {'status': 403, 'code': 'PERMISSION_DENIED', 'message': 'Only administrators can create buildings.'}},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = BuildingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        building = create_building(facility=facility, **serializer.validated_data)
        return Response(BuildingSerializer(building).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='meters')
    def meters(self, request, pk=None):
        facility = self.get_object()
        if request.method == 'GET':
            energy_source = request.query_params.get('energy_source')
            load_category = request.query_params.get('load_category')
            meters = list_meters_for_facility(facility, energy_source=energy_source, load_category=load_category)
            return Response(MeterSerializer(meters, many=True).data)

        # POST: Admin or Field Engineer
        if getattr(request.user, 'role', '') not in ('admin', 'field_engineer') and not request.user.is_superuser:
            return Response(
                {'error': {'status': 403, 'code': 'PERMISSION_DENIED', 'message': 'Only engineers or admins can register meters.'}},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = MeterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        meter = register_meter(facility=facility, data=serializer.validated_data)
        return Response(MeterSerializer(meter).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get', 'post'], url_path='datasources')
    def datasources(self, request, pk=None):
        facility = self.get_object()
        if request.method == 'GET':
            sources = list_datasources_for_facility(facility)
            return Response(DataSourceSerializer(sources, many=True).data)

        # POST: Admin or Field Engineer
        if getattr(request.user, 'role', '') not in ('admin', 'field_engineer') and not request.user.is_superuser:
            return Response(
                {'error': {'status': 403, 'code': 'PERMISSION_DENIED', 'message': 'Only engineers or admins can provision DataSources.'}},
                status=status.HTTP_403_FORBIDDEN
            )
        name = request.data.get('name', 'Default Ingestion Gateway')
        datasource, raw_key = generate_datasource_api_key(facility=facility, name=name)
        return Response({
            'datasource': DataSourceSerializer(datasource).data,
            'api_key': raw_key
        }, status=status.HTTP_201_CREATED)

class RotateDataSourceKeyView(APIView):
    """
    Rotates existing DataSource API key.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, pk=None, *args, **kwargs):
        if getattr(request.user, 'role', '') not in ('admin', 'field_engineer') and not request.user.is_superuser:
            return Response(
                {'error': {'status': 403, 'code': 'PERMISSION_DENIED', 'message': 'Only engineers or admins can rotate API keys.'}},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            ds = DataSource.objects.select_related('facility').get(pk=pk)
        except DataSource.DoesNotExist:
            raise Http404("DataSource not found.")

        # Ensure user has access to facility
        get_facility_for_user(ds.facility_id, request.user)

        new_key = rotate_datasource_api_key(ds)
        return Response({
            'datasource_id': ds.id,
            'name': ds.name,
            'new_api_key': new_key,
            'message': 'API key successfully rotated. Previous key is now invalidated.'
        }, status=status.HTTP_200_OK)
