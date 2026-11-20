"""
GreenGrid Benchmarking Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from drf_spectacular.utils import extend_schema

from core.scoping import get_user_facility_ids

from benchmarking.serializers import (
    BuildingBenchmarkSerializer,
    FacilityBenchmarkScoreSerializer,
)
from benchmarking.selectors import (
    list_building_benchmarks,
    get_facility_benchmark_scores,
    get_facility_rankings,
)

class BuildingBenchmarkListView(APIView):
    """
    Lists national BEE building energy standards and EUI percentile thresholds.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: BuildingBenchmarkSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        standards = list_building_benchmarks()
        return Response(BuildingBenchmarkSerializer(standards, many=True).data)

class FacilityBenchmarkScoreListView(APIView):
    """
    Retrieves annual EUI scores and star ratings for authorized facilities.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FacilityBenchmarkScoreSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_id = request.query_params.get('facility_id')
        year = request.query_params.get('year')
        scores = get_facility_benchmark_scores(request.user, facility_id=facility_id, year=year)
        return Response(FacilityBenchmarkScoreSerializer(scores, many=True).data)

class FacilityRankingListView(APIView):
    """
    Ranks peer facilities within a building category by EUI efficiency.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(responses={200: FacilityBenchmarkScoreSerializer(many=True)})
    def get(self, request, *args, **kwargs):
        facility_type = request.query_params.get('facility_type')
        year = request.query_params.get('year')
        rankings = get_facility_rankings(request.user, facility_type=facility_type, year=year)
        rows = [dict(r) for r in FacilityBenchmarkScoreSerializer(rankings[:50], many=True).data]

        # Peers outside the caller's facilities are anonymised: users can compare their
        # efficiency (EUI, percentile, stars) but never see who the other facilities are.
        scope = get_user_facility_ids(request.user)  # None = admin / superuser (sees everything)
        if scope is not None:
            for rank, row in enumerate(rows, start=1):
                if row['facility'] not in scope:
                    row.update({
                        'id': None,
                        'facility': None,
                        'facility_name': f'Peer facility #{rank}',
                        'facility_code': '',
                        'gross_floor_area_sqm': None,
                        'annual_energy_kwh': None,
                    })
        return Response(rows)

