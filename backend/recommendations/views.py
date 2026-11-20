"""
GreenGrid Recommendations Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from recommendations.serializers import (
    ECMRuleSerializer,
    RecommendationSerializer,
    RecommendationStatusUpdateSerializer,
    RecommendationsSummarySerializer,
)
from recommendations.selectors import (
    list_ecm_rules,
    get_recommendations_for_user,
    get_recommendation_by_id,
    get_recommendations_summary,
)
from recommendations.services import update_recommendation_status
from core.permissions import deny_unless_role

class ECMRuleListView(APIView):
    """
    Lists explainable Energy Conservation Measure (ECM) rule definitions.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: ECMRuleSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        rules = list_ecm_rules()
        return Response(ECMRuleSerializer(rules, many=True).data, status=status.HTTP_200_OK)

class RecommendationListView(APIView):
    """
    Retrieves prioritized ECM recommendations for authorized facilities with ₹ savings.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: RecommendationSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        recom_status = request.query_params.get('status')
        category = request.query_params.get('category')

        recoms = get_recommendations_for_user(
            user=request.user,
            facility_id=facility_id,
            status=recom_status,
            category=category
        )
        return Response(RecommendationSerializer(recoms, many=True).data, status=status.HTTP_200_OK)

class RecommendationDetailView(APIView):
    """
    Retrieves or updates the lifecycle state (accept/dismiss) of an individual ECM recommendation.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: RecommendationSerializer})
    def get(self, request, pk, *args, **kwargs):
        recom = get_recommendation_by_id(request.user, pk)
        return Response(RecommendationSerializer(recom).data, status=status.HTTP_200_OK)

    @extend_schema(
        request=RecommendationStatusUpdateSerializer,
        responses={200: RecommendationSerializer}
    )
    def patch(self, request, pk, *args, **kwargs):
        denied = deny_unless_role(
            request.user, ('admin', 'customer'),
            'Only administrators and customers can accept or dismiss recommendations.')
        if denied:
            return denied
        recom = get_recommendation_by_id(request.user, pk)
        serializer = RecommendationStatusUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_status = serializer.validated_data['status']
        dismissal_reason = serializer.validated_data.get('dismissal_reason', '')

        updated = update_recommendation_status(
            recommendation=recom,
            status=new_status,
            dismissal_reason=dismissal_reason,
            user=request.user
        )
        return Response(RecommendationSerializer(updated).data, status=status.HTTP_200_OK)

class RecommendationsSummaryView(APIView):
    """
    Returns executive summary of total and accepted ₹ energy savings opportunities.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: RecommendationsSummarySerializer})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        summary = get_recommendations_summary(user=request.user, facility_id=facility_id)
        return Response(RecommendationsSummarySerializer(summary).data, status=status.HTTP_200_OK)
