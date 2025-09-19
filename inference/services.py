import os
from functools import lru_cache
from typing import List, Dict, Any, Optional

import joblib

DEFAULT_MODEL_PATH = os.path.join(
    os.path.dirname(__file__), "model_assets", "hotel_cancel_model.joblib"
)
MODEL_PATH = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)

@lru_cache(maxsize=1)
def _load_raw():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"MODEL_PATH not found: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)

def _resolve_model_and_meta(raw) -> (Any, Dict[str, Any]):
    """
    يرجّع (model, meta)
    - لو raw قاموس: يلقط 'pipeline' كموديل و 'feature_columns' كأسماء أعمدة إن وُجدت
    - لو raw موديل مباشرة: يرجّعه كما هو
    """
    meta: Dict[str, Any] = {}
    model = raw
    if isinstance(raw, dict):
        # جرّب المفاتيح الشائعة
        for key in ("pipeline", "model", "estimator"):
            if key in raw:
                model = raw[key]
                break
        else:
            raise ValueError(f"Model dict found but no supported key. Available keys: {list(raw.keys())}")

        # خُد أسماء الأعمدة لو موجودة
        if "feature_columns" in raw and isinstance(raw["feature_columns"], (list, tuple)):
            meta["feature_names"] = list(map(str, raw["feature_columns"]))

    # لو الموديل فيه أسماء أعمدة من sklearn
    names = getattr(model, "feature_names_in_", None)
    if names is not None and not meta.get("feature_names"):
        try:
            meta["feature_names"] = [str(n) for n in list(names)]
        except Exception:
            pass

    # عدد الأعمدة المتوقع من sklearn
    n_features = getattr(model, "n_features_in_", None)
    if n_features is not None:
        meta["expected_n_features"] = int(n_features)

    return model, meta

@lru_cache(maxsize=1)
def load_model_and_meta():
    raw = _load_raw()
    return _resolve_model_and_meta(raw)

def model_signature() -> Dict[str, Any]:
    model, meta = load_model_and_meta()
    sig: Dict[str, Any] = {
        "path": MODEL_PATH,
        "class_name": type(model).__name__,
        "is_pipeline": hasattr(model, "steps"),
        "has_predict_proba": hasattr(model, "predict_proba"),
    }
    sig.update(meta)
    return sig

def _to_model_input(features: List[float]):
    """
    يبني المدخلات زي ما الموديل متوقع:
    - لو عندنا feature_names -> نبني DataFrame بنفس الترتيب
    - غير كده -> list[list]
    ويتحقق من عدد الخصائص لو معروف
    """
    model, meta = load_model_and_meta()
    expected = meta.get("expected_n_features")
    names = meta.get("feature_names")

    # تحقق من العدد
    if expected is not None and len(features) != expected:
        raise ValueError(f"Feature length mismatch. Expected {expected}, got {len(features)}.")

    if names is not None:
        # لازم يساوي الطول
        if len(features) != len(names):
            raise ValueError(
                f"Feature length mismatch. Expected {len(names)} features ({names}), got {len(features)}."
            )
        try:
            import pandas as pd
        except ImportError as e:
            raise ImportError("pandas is required to pass named features. Install pandas.") from e
        return pd.DataFrame([features], columns=names)

    # fallback
    return [features]

def predict(features: List[float]) -> Dict[str, Any]:
    model, _ = load_model_and_meta()
    X = _to_model_input(features)

    # التنبؤ
    y = model.predict(X)[0]

    # الثقة (لو متاحة)
    confidence = None
    if hasattr(model, "predict_proba"):
        try:
            proba_row = model.predict_proba(X)[0]
            confidence = float(max(proba_row))
        except Exception:
            confidence = None

    # رجّع نوع قابل للتسلسل JSON
    label_out = float(y) if isinstance(y, (int, float)) else str(y)
    return {"label": label_out, "confidence": confidence}
