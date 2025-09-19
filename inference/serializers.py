# inference/serializers.py
from typing import List, Optional, Union, Dict, Any
from rest_framework import serializers


class PredictSerializer(serializers.Serializer):
    """
    يقبل شكلين للـ features:
      1) Dict بالمفاتيح الخام (مُفضّل):
         {"features": {"arrival_date_year": 2016, "arrival_date_month": "January", ...}}

      2) List بنفس ترتيب الأعمدة الخام:
         {"features": [2016, "January", ...]}

    مرّر expected_columns من الـ view للتحقق بدقة من الطول/المفاتيح:
        PredictSerializer(data=..., context={"expected_columns": FEATURE_COLUMNS})
    """
    features = serializers.JSONField()

    def validate_features(self, value: Union[List[Any], Dict[str, Any]]) -> Union[List[Any], Dict[str, Any]]:
        expected: Optional[List[str]] = self.context.get("expected_columns")

        # List: تحقق من الطول لو متاح expected_columns
        if isinstance(value, list):
            if expected is not None and len(value) != len(expected):
                raise serializers.ValidationError(
                    f"Expected {len(expected)} features in list, got {len(value)}."
                )
            return value

        # Dict: تحقق من المفاتيح المفقودة لو متاح expected_columns
        if isinstance(value, dict):
            if expected is not None:
                missing = [c for c in expected if c not in value]
                if missing:
                    raise serializers.ValidationError(
                        {"missing_keys": missing, "detail": "Some required feature keys are missing."}
                    )
            return value

        raise serializers.ValidationError("features must be either a JSON object (dict) or an array (list).")


class PredictResponseSerializer(serializers.Serializer):
    """
    مثال رد:
    {
      "label": 1,
      "confidence": 0.92
    }
    """
    label = serializers.IntegerField()
    confidence = serializers.FloatField(required=False, allow_null=True)
