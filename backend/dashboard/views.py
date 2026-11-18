"""
GreenGrid Dashboard Views (<1s Sub-second Response Times).
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from drf_spectacular.utils import extend_schema, OpenApiParameter

from dashboard.selectors import (
    get_facility_kpi_summary,
    get_facility_trends,
    get_facility_energy_mix,
    get_facility_load_breakdown,
)
from dashboard.serializers import (
    KPISummaryResponseSerializer,
    TrendResponseSerializer,
    EnergyMixResponseSerializer,
    LoadBreakdownResponseSerializer,
)

class DashboardSummaryView(APIView):
    """
    Retrieves real-time executive KPI metrics for a facility in under 1 second.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter('facility_id', int, required=True, description="ID of the commercial facility")],
        responses={200: KPISummaryResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response(
                {'error': {'status': 400, 'code': 'MISSING_FACILITY_ID', 'message': 'Query parameter facility_id is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = get_facility_kpi_summary(int(facility_id), request.user)
        return Response(data, status=status.HTTP_200_OK)

class DashboardTrendsView(APIView):
    """
    Retrieves 24-hour hourly profile or 30-day daily profile.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter('facility_id', int, required=True),
            OpenApiParameter('range', str, required=False, default='24h', description="'24h' or '30d'")
        ],
        responses={200: TrendResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response(
                {'error': {'status': 400, 'code': 'MISSING_FACILITY_ID', 'message': 'Query parameter facility_id is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        range_type = request.query_params.get('range', '24h')
        data = get_facility_trends(int(facility_id), request.user, range_type=range_type)
        return Response(data, status=status.HTTP_200_OK)

class DashboardEnergyMixView(APIView):
    """
    Returns energy consumption breakdown by source (Grid, DG, Solar PV).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter('facility_id', int, required=True)],
        responses={200: EnergyMixResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response(
                {'error': {'status': 400, 'code': 'MISSING_FACILITY_ID', 'message': 'Query parameter facility_id is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = get_facility_energy_mix(int(facility_id), request.user)
        return Response(data, status=status.HTTP_200_OK)

class DashboardLoadBreakdownView(APIView):
    """
    Returns sub-metered load breakdown (HVAC, Lighting, IT, Auxiliary Pumps).
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[OpenApiParameter('facility_id', int, required=True)],
        responses={200: LoadBreakdownResponseSerializer}
    )
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        if not facility_id:
            return Response(
                {'error': {'status': 400, 'code': 'MISSING_FACILITY_ID', 'message': 'Query parameter facility_id is required.'}},
                status=status.HTTP_400_BAD_REQUEST
            )
        data = get_facility_load_breakdown(int(facility_id), request.user)
        return Response(data, status=status.HTTP_200_OK)
