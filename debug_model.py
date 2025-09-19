import json, joblib
from pathlib import Path
from pprint import pprint

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / "inference" / "model_assets" / "hotel_cancel_model.joblib"
OUT = ROOT / "_debug"
OUT.mkdir(exist_ok=True)

m = joblib.load(str(MODEL))

feature_cols = m.get("feature_columns")
num_cols = m.get("num_cols", [])
cat_cols = m.get("cat_cols", [])

info = {
    "model_path": str(MODEL),
    "feature_columns": feature_cols,
    "num_cols": num_cols,
    "cat_cols": cat_cols,
}

# حاول نطلع قيم OneHotEncoder المسموح بها + handle_unknown
cat_values_map = {}
handle_unknown = None

pipe = m.get("pipeline")
try:
    from sklearn.compose import ColumnTransformer
    from sklearn.preprocessing import OneHotEncoder

    ct = None
    for name, step in getattr(pipe, "steps", []):
        if isinstance(step, ColumnTransformer):
            ct = step
            break

    if ct is not None:
        for name, transformer, cols in ct.transformers_:
            ohe = None
            if isinstance(transformer, OneHotEncoder):
                ohe = transformer
            elif hasattr(transformer, "named_steps") and isinstance(transformer.named_steps.get("onehot"), OneHotEncoder):
                ohe = transformer.named_steps["onehot"]
            if ohe is not None:
                handle_unknown = getattr(ohe, "handle_unknown", None)
                base_cols = cat_cols or cols
                for col, cats in zip(base_cols, ohe.categories_):
                    cat_values_map[str(col)] = [ (c if isinstance(c,(str,int,float)) else str(c)) for c in cats ]
except Exception as e:
    info["ohe_extract_error"] = str(e)

info["allowed_categories"] = cat_values_map
info["onehot_handle_unknown"] = handle_unknown

# ابن عينة Features صحيحة بالترتيب (أرقام=0.0 كاتيجوري=أول قيمة مسموحة)
sample = []
for col in feature_cols:
    if col in num_cols:
        sample.append(0.0)
    elif col in cat_cols:
        vals = cat_values_map.get(col) or []
        sample.append(vals[0] if vals else "")
    else:
        sample.append("")

payload = {"features": sample}

# اكتب الملفات
(OUT / "model_info.json").write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding="utf-8")
(OUT / "predict_template.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

print("==> كتبنا:")
print(OUT / "model_info.json")
print(OUT / "predict_template.json")
print("\n# Sample payload استخدمه مع /api/v1/predict/:")
pprint(payload)
