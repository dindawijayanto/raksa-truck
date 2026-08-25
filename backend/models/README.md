# Model B CatBoost artifact

This directory contains the native CatBoost weights exported from the AIC Model B synthetic benchmark:

- `damage_regressor.cbm`
- `rul_regressor.cbm`
- `service_classifier.cbm`
- `model_contract.json`

The model is **simulation-only**. It estimates synthetic scenarios and is not a field-validated maintenance decision model.

## Model A artifacts

`model_a/` contains K-Means, RobustScaler, and speed-correction artifacts for the four processed sensor sessions. Model A scores are relative **within a session**; the dashboard uses the paired precomputed reports in `backend/data/model_a/` rather than attempting raw-sensor inference in an HTTP request.
