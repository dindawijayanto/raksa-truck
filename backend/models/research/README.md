# Research-only model artifacts

Artefak di bawah folder ini tidak dimuat oleh FastAPI. Mereka dipertahankan
untuk dokumentasi dan reproduksi benchmark AIC.

- `model_b/contextual_wear_rule_based_v1.json`: spesifikasi Model B
  rule-based yang menghasilkan laporan operasional.
- `model_b/eviot_rul_benchmark/`: baseline eksternal EVIoT; tidak transferable
  ke data lokal tanpa validasi silang.
- `model_b/synthetic_ml_v1/`: surrogate HistGradientBoosting untuk label
  simulasi.
- `model_b/synthetic_boosting_benchmark_v1/`: bundle CatBoost, LightGBM, dan
  XGBoost pada benchmark synthetic group-held-out.

Seluruh artefak ini berstatus `simulation_only` atau research-only. Weight
deployable CatBoost native ada satu level di atas, di `backend/models/`.

## Kompatibilitas artifact legacy

Bundle boosting dapat dimuat pada environment saat ini, meskipun scikit-learn
akan memberi peringatan versi karena artifact asal memakai scikit-learn 1.2.1.
Artifact `synthetic_ml_v1` dan `eviot_rul_benchmark` adalah pickle legacy dari
scikit-learn 1.2.1 dan tidak kompatibel dengan runtime Python 3.13 /
scikit-learn 1.6 yang dipakai pemeriksaan repository ini. Untuk membuka dua
artifact tersebut, gunakan environment Python 3.10 atau 3.11 dengan
`scikit-learn==1.2.1`, atau jalankan ulang skrip training bila dataset sumber
tersedia. Keterbatasan ini tidak memengaruhi API: FastAPI hanya memuat model
CatBoost native `.cbm`, bukan pickle legacy ini.
