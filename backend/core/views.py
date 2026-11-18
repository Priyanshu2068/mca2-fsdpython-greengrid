"""
GreenGrid Core API Views.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework import status
from django.db import connection
from django.utils import timezone
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

class HealthCheckView(APIView):
    """
    Public health check endpoint validating application and database operational readiness.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Service Health Check",
        description="Returns system and database connectivity status.",
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={
                    "status": serializers.CharField(),
                    "version": serializers.CharField(),
                    "database": serializers.CharField(),
                    "timestamp": serializers.DateTimeField(),
                }
            )
        }
    )
    def get(self, request, *args, **kwargs):
        db_status = "connected"
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except Exception as e:
            db_status = f"unreachable: {str(e)}"
            return Response(
                {
                    "error": {
                        "status": status.HTTP_503_SERVICE_UNAVAILABLE,
                        "code": "DATABASE_UNAVAILABLE",
                        "message": "Database connectivity check failed.",
                        "details": str(e)
                    }
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )

        return Response(
            {
                "status": "healthy",
                "version": "1.0.0",
                "database": db_status,
                "timestamp": timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )
