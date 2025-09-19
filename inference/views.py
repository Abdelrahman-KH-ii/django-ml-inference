from typing import Optional, List, Any, Dict, Union

from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from drf_spectacular.utils import extend_schema, OpenApiExample

from .serializers import PredictSerializer, PredictResponseSerializer
from . import preprocess, postprocess
from .services import predict as do_predict, model_signature


class HealthView(APIView):
   
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(
        description="Simple health check",
        responses={200: {"type": "object", "properties": {"status": {"type": "string"}, "service": {"type": "string"}}}},
    )
    def get(self, request):
        return Response({"status": "ok", "service": "ML API"}, status=200)


class ModelInfoView(APIView):
    
    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(description="Inspect loaded model signature (debug).")
    def get(self, request):
        try:
            info = model_signature()  # لازم يرجّع dict فيه feature_columns على الأقل
            return Response(info, status=200)
        except FileNotFoundError as e:
            return Response({"error": "model_not_found", "detail": str(e)}, status=500)
        except Exception as e:
            return Response({"error": "model_introspection_failed", "detail": str(e)}, status=500)


@method_decorator(csrf_exempt, name="dispatch")  # للتجربة محليًا من Swagger بدون CSRF
class PredictView(APIView):

    authentication_classes: list = []
    permission_classes: list = []

    @extend_schema(
        request=PredictSerializer,
        responses={200: PredictResponseSerializer},
        examples=[
            OpenApiExample(
                name="List (ordered raw features)",
                value={"features": [5.1, 3.5, 1.4, 0.2]},
                request_only=True,
            ),
            OpenApiExample(
                name="Dict (named raw features)",
                value={
                    "features": {
                        "arrival_date_year": 2016,
                        "arrival_date_month": "January",
                        "arrival_date_week_number": 1,
                        "arrival_date_day_of_month": 15,
                        "stays_in_weekend_nights": 2,
                        "stays_in_week_nights": 0,
                        "adults": 2,
                        "children": 0,
                        "meal": "BB",
                        "country": "PRT",
                        "market_segment": "Online TA",
                        "previous_cancellations": 0,
                        "previous_bookings_not_canceled": 0,
                        "reserved_room_type": "A",
                        "assigned_room_type": "A",
                        "booking_changes": 0,
                        "deposit_type": "No Deposit",
                        "days_in_waiting_list": 0,
                        "customer_type": "Transient",
                        "adr": 100.0,
                        "required_car_parking_spaces": 0,
                        "total_of_special_requests": 0
                    }
                },
                request_only=True,
            ),
            OpenApiExample(
                name="Sample response",
                value={"label": 1, "confidence": 0.92},
                response_only=True,
            ),
        ],
        description="Accepts raw features as a dict (preferred) or list (ordered). Server applies training preprocessing.",
    )
    def post(self, request):
    # 1) هات ترتيب الأعمدة الخام من توقيع الموديل
        try:
            sig: Dict[str, Any] = model_signature()
            expected_cols: Optional[List[str]] = sig.get("feature_columns")
        except FileNotFoundError as e:
            return Response({"error": "model_not_found", "detail": str(e)}, status=500)
        except Exception as e:
            return Response({"error": "model_introspection_failed", "detail": str(e)}, status=500)

       
        serializer = PredictSerializer(data=request.data, context={"expected_columns": expected_cols})
        if not serializer.is_valid():
            return Response({"error": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            payload: Union[Dict[str, Any], List[Any]] = serializer.validated_data["features"]

            
            X = preprocess.run(payload, expected_columns=expected_cols)

            
            y = do_predict(X)

           
            out = postprocess.run(y)
            return Response(out, status=200)

        except ValueError as e:
            return Response({"error": "bad_input", "detail": str(e)}, status=400)
        except FileNotFoundError as e:
            return Response({"error": "model_not_found", "detail": str(e)}, status=500)
        except Exception as e:
            return Response({"error": "inference_failed", "detail": str(e)}, status=500)
