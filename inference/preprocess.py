from typing import List, Dict, Any

def run(x: list | Dict[str, Any], expected_columns=None, **kwargs) -> List[float]:
    if isinstance(x, dict):
        cols = expected_columns or list(x.keys())
        values = [x.get(c) for c in cols]
    else:
        values = list(x)

    processed = []
    for v in values:
        if v is None:
            processed.append(0.0)
        else:
            try:
                processed.append(float(v))
            except ValueError:
                
                processed.append(0.0)
    return processed
