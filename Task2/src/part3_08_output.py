# Save grid search results: param configs and their F1 scores.
import json
import os

def save_metrics(cv_model, output_path: str):
    # CrossValidatorModel exposes avgMetrics (one per param config)
    results = []
    for params, f1 in zip(cv_model.getEstimatorParamMaps(), cv_model.avgMetrics):
        flat = {}
        for p, v in params.items():
            flat[p.name] = v
        flat["f1"] = float(f1)
        results.append(flat)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
