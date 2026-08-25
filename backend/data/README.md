# Dashboard report data

- `model_a/` contains Model A session summaries and segment-level road roughness output.
- `model_b/` contains the output of the operational, rule-based Model B run.

Model A data is report-backed: it is the audited output of the sensor pipeline and its `relative_roughness_score` is comparable only within the selected session. Model B CatBoost scenario predictions remain available through `POST /api/v1/model-b/predict` and are labelled `simulation_only`.
