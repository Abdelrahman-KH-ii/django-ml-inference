from typing import Dict, Any

def run(pred: Dict, **kwargs) -> Dict:
    """
    Postprocessing للنتيجة: يقبل أي باراميتر زيادة زي expected_columns
    علشان ما يكسرش الكود اللي بيناديه.
    """
    if pred.get("confidence") is not None:
        pred["confidence"] = round(float(pred["confidence"]), 6)
    return pred
