# Experiment reports

Folder ini memuat hasil eksperimen yang dipindahkan dari AI Center:

- `model_a/`: konfigurasi dan audit proses sensor;
- `model_b/`: tabel wear rule-based, profil muatan, dan visual operasional;
- `model_b_synthetic_ml/`: metrik, feature importance, prediksi uji, dan grafik
  surrogate ML;
- `model_b_boosting_benchmark/`: perbandingan CatBoost, LightGBM, dan XGBoost;
- `model_b_benchmark/`: baseline EVIoT research-only.

Tabel Model A yang dibaca aplikasi berada di `backend/data/model_a/` agar
terpisah dari laporan offline. Interpretasi dan batas seluruh hasil tercantum
di [`../../docs/modeling/README.md`](../../docs/modeling/README.md).
