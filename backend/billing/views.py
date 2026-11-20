"""
GreenGrid Billing Views.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.http import Http404
from drf_spectacular.utils import extend_schema

from billing.serializers import (
    UtilityProviderSerializer,
    TariffStructureSerializer,
    UtilityBillSerializer,
    UtilityBillCreateSerializer,
    BillReconciliationSerializer,
)
from billing.selectors import (
    list_utility_providers,
    list_tariffs,
    list_utility_bills,
    list_reconciliations,
)
from billing.services import record_utility_bill, reconcile_utility_bill
from billing.models import UtilityBill
from facilities.selectors import get_facility_for_user

class UtilityProviderListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: UtilityProviderSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        providers = list_utility_providers()
        return Response(UtilityProviderSerializer(providers, many=True).data)

class TariffStructureListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: TariffStructureSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        provider_id = request.query_params.get('provider_id')
        tariffs = list_tariffs(provider_id=provider_id)
        return Response(TariffStructureSerializer(tariffs, many=True).data)

class UtilityBillViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = UtilityBillSerializer

    def get_queryset(self):
        facility_id = self.request.query_params.get('facility_id')
        year = self.request.query_params.get('year')
        return list_utility_bills(self.request.user, facility_id=facility_id, year=year)

    def get_object(self):
        try:
            bill = UtilityBill.objects.select_related('facility', 'tariff').get(pk=self.kwargs['pk'])
        except UtilityBill.DoesNotExist:
            raise Http404("Utility bill not found.")
        get_facility_for_user(bill.facility_id, self.request.user)
        return bill

    # Admins and field engineers may record bills manually (emergency / offline entry).
    BILL_ENTRY_ROLES = ('admin', 'field_engineer')

    def create(self, request, *args, **kwargs):
        user = request.user
        if getattr(user, 'role', '') not in self.BILL_ENTRY_ROLES and not user.is_superuser:
            return Response(
                {'error': {'status': 403, 'code': 'PERMISSION_DENIED', 'message': 'Only administrators and field engineers can record utility bills.'}},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = UtilityBillCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        facility = serializer.validated_data['facility']
        get_facility_for_user(facility.id, user)  # engineers: assigned facilities only (404 otherwise)
        tariff = serializer.validated_data['tariff']

        bill = record_utility_bill(
            facility=facility,
            tariff=tariff,
            bill_number=serializer.validated_data['bill_number'],
            billing_cycle_start=serializer.validated_data['billing_cycle_start'],
            billing_cycle_end=serializer.validated_data['billing_cycle_end'],
            due_date=serializer.validated_data['due_date'],
            billed_kwh=serializer.validated_data['billed_kwh'],
            billed_max_demand_kva=serializer.validated_data['billed_max_demand_kva'],
            billed_amount_inr=serializer.validated_data['billed_amount_inr'],
            payment_status=serializer.validated_data.get('payment_status', 'unpaid'),
            auto_reconcile=True
        )
        return Response(UtilityBillSerializer(bill).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='reconcile')
    def reconcile(self, request, pk=None):
        bill = self.get_object()
        rec = reconcile_utility_bill(bill)
        return Response(BillReconciliationSerializer(rec).data, status=status.HTTP_200_OK)

class BillReconciliationListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: BillReconciliationSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        bill_id = request.query_params.get('bill_id')
        facility_id = request.query_params.get('facility_id')
        recs = list_reconciliations(user=request.user, bill_id=bill_id, facility_id=facility_id)
        return Response(BillReconciliationSerializer(recs[:100], many=True).data)
