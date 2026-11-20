"""
GreenGrid Analytics Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.http import Http404
from drf_spectacular.utils import extend_schema

from analytics.serializers import (
    HourlyRollupSerializer,
    DailyRollupSerializer,
    AnomalyAlertSerializer,
    AnomalyAlertUpdateSerializer,
)
from analytics.selectors import (
    get_hourly_rollups,
    get_daily_rollups,
    list_anomaly_alerts,
)
from analytics.models import AnomalyAlert
from core.scoping import get_user_facility_ids
from core.permissions import deny_unless_role

class HourlyRollupListView(APIView):
    """
    Queries pre-computed hourly rollups.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: HourlyRollupSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        meter_id = request.query_params.get('meter_id')
        start_time = request.query_params.get('start_time')
        end_time = request.query_params.get('end_time')

        qs = get_hourly_rollups(
            user=request.user,
            facility_id=facility_id,
            meter_id=meter_id,
            start_time=start_time,
            end_time=end_time
        )
        return Response(HourlyRollupSerializer(qs[:200], many=True).data)

class DailyRollupListView(APIView):
    """
    Queries pre-computed daily rollups with peak and off-peak energy breakdown.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: DailyRollupSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        meter_id = request.query_params.get('meter_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        qs = get_daily_rollups(
            user=request.user,
            facility_id=facility_id,
            meter_id=meter_id,
            start_date=start_date,
            end_date=end_date
        )
        return Response(DailyRollupSerializer(qs[:100], many=True).data)

class AnomalyAlertListView(APIView):
    """
    Lists anomaly alerts across scoped facilities.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: AnomalyAlertSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        alert_status = request.query_params.get('status')
        severity = request.query_params.get('severity')
        anomaly_type = request.query_params.get('anomaly_type')

        qs = list_anomaly_alerts(
            user=request.user,
            facility_id=facility_id,
            status=alert_status,
            severity=severity,
            anomaly_type=anomaly_type
        )
        return Response(AnomalyAlertSerializer(qs[:100], many=True).data)

class AnomalyAlertDetailView(APIView):
    """
    Retrieves or updates an Anomaly Alert (acknowledges / resolves).
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, user):
        try:
            alert = AnomalyAlert.objects.select_related('facility', 'meter').get(pk=pk)
        except AnomalyAlert.DoesNotExist:
            raise Http404("Anomaly Alert not found.")

        facility_ids = get_user_facility_ids(user)
        if facility_ids is not None and alert.facility_id not in facility_ids:
            raise Http404("Anomaly Alert not found.")
        return alert

    @extend_schema(responses={200: AnomalyAlertSerializer})
    def get(self, request, pk, *args, **kwargs):
        alert = self.get_object(pk, request.user)
        return Response(AnomalyAlertSerializer(alert).data)

    @extend_schema(request=AnomalyAlertUpdateSerializer, responses={200: AnomalyAlertSerializer})
    def patch(self, request, pk, *args, **kwargs):
        denied = deny_unless_role(
            request.user, ('admin', 'field_engineer'),
            'Only administrators and field engineers can update alerts.')
        if denied:
            return denied
        alert = self.get_object(pk, request.user)
        serializer = AnomalyAlertUpdateSerializer(alert, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data.get('status')
        if new_status in ('resolved', 'false_positive'):
            alert.resolved_at = timezone.now()

        serializer.save()
        return Response(AnomalyAlertSerializer(alert).data, status=status.HTTP_200_OK)

