from typing import Dict, Any

def run(pred: Dict, **kwargs) -> Dict:
   
    if pred.get("confidence") is not None:
        pred["confidence"] = round(float(pred["confidence"]), 6)
    return pred
