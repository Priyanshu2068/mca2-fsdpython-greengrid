"""
GreenGrid Recommendations Serializers.
"""

from rest_framework import serializers
from recommendations.models import ECMRule, Recommendation

class ECMRuleSerializer(serializers.ModelSerializer):
    category_display = serializers.CharField(source='get_category_display', read_only=True)

    class Meta:
        model = ECMRule
        fields = [
            'id', 'rule_code', 'name', 'category', 'category_display',
            'description', 'is_active'
        ]

class RecommendationSerializer(serializers.ModelSerializer):
    rule_code = serializers.CharField(source='rule.rule_code', read_only=True)
    rule_category = serializers.CharField(source='rule.category', read_only=True)
    facility_name = serializers.CharField(source='facility.name', read_only=True)
    facility_code = serializers.CharField(source='facility.code', read_only=True)
    meter_identifier = serializers.CharField(source='meter.meter_identifier', read_only=True, default=None)

    class Meta:
        model = Recommendation
        fields = [
            'id', 'rule', 'rule_code', 'rule_category',
            'facility', 'facility_name', 'facility_code',
            'meter', 'meter_identifier',
            'title', 'description', 'action_plan',
            'estimated_annual_kwh_savings', 'estimated_annual_savings_inr',
            'implementation_cost_inr', 'estimated_payback_months',
            'status', 'dismissal_reason',
            'generated_at', 'actioned_at'
        ]

class RecommendationStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=['accepted', 'dismissed', 'implemented'])
    dismissal_reason = serializers.CharField(required=False, allow_blank=True, default='')

    def validate(self, attrs):
        if attrs.get('status') == 'dismissed' and not attrs.get('dismissal_reason', '').strip():
            raise serializers.ValidationError({
                'dismissal_reason': 'A valid dismissal reason is mandatory when dismissing a recommendation.'
            })
        return attrs

class RecommendationsSummarySerializer(serializers.Serializer):
    total_recommendations = serializers.IntegerField()
    active_count = serializers.IntegerField()
    accepted_count = serializers.IntegerField()
    dismissed_count = serializers.IntegerField()
    total_potential_savings_inr = serializers.DecimalField(max_digits=14, decimal_places=2)
    accepted_annual_savings_inr = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_potential_kwh_savings = serializers.DecimalField(max_digits=14, decimal_places=4)
    accepted_annual_kwh_savings = serializers.DecimalField(max_digits=14, decimal_places=4)
