from django.shortcuts import render

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from api.serializers import AnalyzeRequestSerializer
from api.services.trip_analysis import analyze_trip


@api_view(["GET"])
def health_check(request):
    return Response({
        "status": "ok",
        "service": "WeAware API",
        "message": "Backend is running successfully."
    })


class AnalyzeTripView(APIView):
    def post(self, request):
        serializer = AnalyzeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        result = analyze_trip(
            origin=data["origin"],
            destination=data["destination"],
            departure_utc=data["departure_utc"],
            load_lb=data["load_lb"],
            interval_miles=data["interval_miles"],
        )

        return Response(result, status=status.HTTP_200_OK)
