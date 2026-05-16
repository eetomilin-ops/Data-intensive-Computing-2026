# Save grid search results: param configs and their F1 scores.
import json
from common import write_text_file

def save_metrics(spark, cv_model, output_path: str):
    results = []
    for params, f1 in zip(cv_model.getEstimatorParamMaps(), cv_model.avgMetrics):
        flat = {}
        for p, v in params.items():
            flat[p.name] = v
        flat["f1"] = float(f1)
        results.append(flat)
    write_text_file(spark, [json.dumps(results, indent=2)], output_path)
