# Model B — physics-informed synthetic ML benchmark

> **Penyesuaian struktur Raksa Truck:** jalankan perintah di dokumen ini dari
> `backend/modeling/`. Path asal `data/`, `models/`, dan `reports/` masing-masing
> dipetakan ke `backend/data/`, `backend/models/research/`, dan
> `reports/modeling/`. CatBoost native yang diekspor untuk API berada di
> `backend/models/`. Ringkasan path tersedia di [README modelling](README.md).

## Tujuan

Dataset sensor lokal belum memiliki `load_kg` dari load cell, jarak sejak servis, maupun label kerusakan/servis. Karena itu benchmark ini **tidak menggantikan** Model B rule-based. Ia membuat data simulasi berlabel untuk menguji alur ML, visualisasi, dan struktur artifact sampai data armada tersedia.

## Grid skenario

- Template truk generik: ringan (8 t GVM), medium (16 t), berat (30 t). Angka ini adalah parameter simulasi, bukan batas legal universal.
- Rasio muatan: 0%, 50%, 75%, 100%, dan 110% kapasitas payload. Level 110% digunakan untuk stress-test ODOL, bukan rekomendasi operasi.
- Jalan: smooth (IRI 1,0–2,3), medium (2,3–3,8), rough (3,8–5,5 m/km).
- Kecepatan: 24, 48, 72, dan 89 km/jam.
- Suspensi: leaf dan air; tekanan ban 85%, 100%, dan 115% nominal; tiga seed profil jalan.

Rentang IRI dan grid kecepatan/muatan mengikuti desain uji kendaraan berat. Simulasi memakai hubungan beban pangkat 3,5 sebagai titik tengah sensitivity range 3–4. Ini adalah simplifikasi yang sengaja eksplisit.

## Pembuatan label

```text
DLC = f(IRI, speed, suspension, tire state)
damage_rate = load_ratio^3.5 × roughness × speed × (1 + DLC) / service_life
RUL = (1 - cumulative_damage) / damage_rate
```

ML belajar dari fitur operasional tersebut untuk memprediksi `damage_increment_pct`, `rul_km`, dan kelas `service_due_1000km`. Split dilakukan berdasarkan `fleet_unit_id`, sehingga unit truk uji tidak muncul saat training.

Metric seperti R², MAE, atau PR-AUC hanya menyatakan fidelity terhadap **label simulasi**. Jangan menyebutnya akurasi terhadap armada nyata.

## Perintah

```bash
python scripts/generate_model_b_synthetic_benchmark.py
python scripts/train_model_b_synthetic_ml.py
python scripts/benchmark_model_b_boosting.py
```

Output:

- `data/synthetic/model_b_physics_benchmark.csv` dan manifest;
- `models/model_b/synthetic_ml_v1/physics_informed_synthetic_ml_v1.joblib`;
- `models/model_b/synthetic_ml_v1/model_card.json`;
- `reports/model_b_synthetic_ml/synthetic_ml_overview.png`.

## Benchmark CatBoost, LightGBM, dan XGBoost

`benchmark_model_b_boosting.py` menggunakan persis satu split group-held-out yang sama untuk ketiga keluarga model. Setiap keluarga melatih tiga estimator: regresi `damage_increment_pct`, regresi `rul_km`, dan klasifikasi `service_due_1000km`. Target regresi ditransformasi `log1p` ketika pelatihan dan dikembalikan ke satuan asli sebelum evaluasi.

Outputnya adalah tiga bundle bobot terpisah di `models/model_b/synthetic_boosting_benchmark_v1/`, tabel metrik komparatif, prediksi test, feature importance, serta `reports/model_b_boosting_benchmark/boosting_benchmark.png`. Pemilihan *champion* bersifat otomatis untuk **benchmark sintetis** (R² RUL tertinggi, dilanjutkan PR-AUC tertinggi dan MAE terendah); hasil ini tidak mengubah status Model B yang deployable.

## Rujukan teknis

1. [Kulakowski et al., dynamic wheel-load factorial experiment](https://hvttforum.org/wp-content/uploads/2019/11/A-Study-Of-Dynamic-Wheel-Loads-Conducted-Using-A-Four-Post-Road-Simulator-Kulakowski-.pdf) — roughness, speed, axle static load, dan tekanan ban sebagai faktor eksperimen.
2. [Loprencipe & Zoccali (2017)](https://link.springer.com/article/10.1007/s40534-017-0122-1) — pembuatan profil jalan sintetis berdasarkan kelas ISO 8608.
3. [FHWA truck size and weight study](https://www.fhwa.dot.gov/reports/tswstudy/vol3-chapter5.pdf) — sensitivity hubungan kerusakan pavement terhadap beban axle berada sekitar pangkat 3–4, dengan batas penggunaan yang perlu diperhatikan.
4. [Boéssio et al. (2006)](https://www.sciencedirect.com/science/article/abs/pii/S0022460X05003664) — rainflow dan Palmgren–Miner untuk akumulasi fatigue kendaraan komersial.
