"""
GreenGrid Renewables Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils.dateparse import parse_date

from core.scoping import get_user_facility_ids
from facilities.selectors import get_facility_for_user
from rest_framework.exceptions import ValidationError

from renewables.serializers import (
    SolarAssetSerializer,
    SolarGenerationReadingSerializer,
    GridEventSerializer,
    CarbonEmissionFactorSerializer,
    SelfConsumptionResponseSerializer,
    CarbonEmissionsResponseSerializer,
)
from renewables.selectors import (
    list_solar_assets,
    get_solar_generation_readings,
    get_grid_events,
    get_carbon_emission_factors,
)
from renewables.services import (
    calculate_solar_self_consumption,
    calculate_carbon_emissions,
    record_grid_event,
    ensure_default_emission_factors,
)

class SolarAssetListView(APIView):
    """
    Lists on-site solar photovoltaic arrays, rated capacity, and inverter specifications.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name='facility_id', type=int, required=False)],
        responses={200: SolarAssetSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        assets = list_solar_assets(user=request.user, facility_id=facility_id)
        return Response(SolarAssetSerializer(assets, many=True).data, status=status.HTTP_200_OK)

class SolarGenerationListView(APIView):
    """
    Retrieves 15-minute solar power generation telemetry, irradiance, and performance ratios.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: SolarGenerationReadingSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        asset_id = request.query_params.get('asset_id')
        facility_id = request.query_params.get('facility_id')
        start_date = parse_date(request.query_params.get('start_date', ''))
        end_date = parse_date(request.query_params.get('end_date', ''))

        readings = get_solar_generation_readings(
            user=request.user,
            asset_id=asset_id,
            facility_id=facility_id,
            start_date=start_date,
            end_date=end_date
        )
        return Response(SolarGenerationReadingSerializer(readings[:100], many=True).data, status=status.HTTP_200_OK)

class SolarSelfConsumptionView(APIView):
    """
    Calculates on-site solar generation self-consumption %, solar fraction %, and avoided grid expenditure.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name='facility_id', type=int, required=True)],
        responses={200: SelfConsumptionResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            raise ValidationError({'facility_id': 'Query parameter facility_id is required.'})

        fac = get_facility_for_user(facility_id=facility_id, user=request.user)
        start_date = parse_date(request.query_params.get('start_date', ''))
        end_date = parse_date(request.query_params.get('end_date', ''))

        data = calculate_solar_self_consumption(facility=fac, start_date=start_date, end_date=end_date)
        return Response(SelfConsumptionResponseSerializer(data).data, status=status.HTTP_200_OK)

class GridEventListView(APIView):
    """
    Retrieves and logs utility grid outages, voltage sags, and diesel generator runtimes.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: GridEventSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        event_type = request.query_params.get('event_type')
        events = get_grid_events(user=request.user, facility_id=facility_id, event_type=event_type)
        return Response(GridEventSerializer(events[:100], many=True).data, status=status.HTTP_200_OK)

    @extend_schema(request=GridEventSerializer, responses={201: GridEventSerializer})
    def post(self, request, *args, **kwargs):
        serializer = GridEventSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        facility = get_facility_for_user(
            facility_id=serializer.validated_data['facility'].id,
            user=request.user
        )
        event = record_grid_event(
            facility=facility,
            event_type=serializer.validated_data['event_type'],
            start_time=serializer.validated_data['start_time'],
            end_time=serializer.validated_data.get('end_time'),
            fuel_consumed_litres=serializer.validated_data.get('fuel_consumed_litres', 0),
            notes=serializer.validated_data.get('notes', '')
        )
        return Response(GridEventSerializer(event).data, status=status.HTTP_201_CREATED)

class CarbonEmissionsView(APIView):
    """
    Calculates facility Scope 2 carbon emissions (kg CO2 & tCO2e) and avoided emissions based on CEA India factors.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter(name='facility_id', type=int, required=True)],
        responses={200: CarbonEmissionsResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            raise ValidationError({'facility_id': 'Query parameter facility_id is required.'})

        fac = get_facility_for_user(facility_id=facility_id, user=request.user)
        start_date = parse_date(request.query_params.get('start_date', ''))
        end_date = parse_date(request.query_params.get('end_date', ''))

        data = calculate_carbon_emissions(facility=fac, start_date=start_date, end_date=end_date)
        return Response(CarbonEmissionsResponseSerializer(data).data, status=status.HTTP_200_OK)

class CarbonFactorListView(APIView):
    """
    Lists Central Electricity Authority (CEA) verified CO2 emission factors per fuel/energy source.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: CarbonEmissionFactorSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        ensure_default_emission_factors()
        factors = get_carbon_emission_factors()
        return Response(CarbonEmissionFactorSerializer(factors, many=True).data, status=status.HTTP_200_OK)
