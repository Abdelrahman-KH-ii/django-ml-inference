
from typing import List, Optional, Union, Dict, Any
from rest_framework import serializers


class PredictSerializer(serializers.Serializer):
    
    features = serializers.JSONField()

    def validate_features(self, value: Union[List[Any], Dict[str, Any]]) -> Union[List[Any], Dict[str, Any]]:
        expected: Optional[List[str]] = self.context.get("expected_columns")

        
        if isinstance(value, list):
            if expected is not None and len(value) != len(expected):
                raise serializers.ValidationError(
                    f"Expected {len(expected)} features in list, got {len(value)}."
                )
            return value

        
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
 
    label = serializers.IntegerField()
    confidence = serializers.FloatField(required=False, allow_null=True)
