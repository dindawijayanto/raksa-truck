# Arsip Modelling AIC

Folder ini mengumpulkan deliverable modelling yang dipindahkan dari AI Center
ke struktur Raksa Truck. Ia memisahkan artefak riset yang dapat direproduksi
dari artefak yang benar-benar dipakai API dashboard.

## Peta artefak

| Kebutuhan | Lokasi | Status |
| --- | --- | --- |
| Proposal Technology & Validation | `PROPOSAL_TECHNOLOGY_VALIDATION.md` | Dokumen proposal |
| Metode end-to-end | `PIPELINE.md` | Dokumentasi teknis |
| Asumsi ML sintetis | `SYNTHETIC_ML_BENCHMARK.md` | Dokumentasi benchmark |
| Notebook Model A | `../../notebooks/01_model_a_all_sessions.ipynb` | Reproduksi analisis sensor |
| Notebook Model B rule-based | `../../notebooks/02_model_b_contextual_wear.ipynb` | Reproduksi analisis konteks wear |
| Notebook ML Model B | `../../notebooks/03_model_b_synthetic_ml_benchmark.ipynb` | Reproduksi benchmark sintetis |
| Kode dan skrip offline | `../../backend/modeling/` | Reproduksi modelling |
| Laporan dan grafik | `../../reports/modeling/` | Hasil eksperimen |
| Bobot benchmark riset | `../../backend/models/research/` | `simulation_only` / research-only |
| Bobot yang dipakai API | `../../backend/models/` | API Model B dan laporan Model A |

`reference/Brainstorming - COMPFEST.docx` dipertahankan sebagai dokumen
referensi historis; ia bukan kontrak model atau sumber metrik benchmark.

## Ringkasan model

### Model A — session-relative road roughness

Model A mengubah IMU dan GPS menjadi skor kekasaran relatif per segmen 20 m.
Output auditnya tersedia di `backend/data/model_a/`; bobot K-Means,
RobustScaler, dan koreksi kecepatan per sesi tersedia di
`backend/models/model_a/`. Empat sesi sensor diproses, dengan 999 segmen
total dan 45 hotspot. `relative_roughness_score` hanya sah dibandingkan di
dalam sesi yang sama, bukan sebagai IRI absolut atau peringkat antarkendaraan.

### Model B — contextual wear dan benchmark ML

Laporan `reports/modeling/model_b/` mendokumentasikan Model B rule-based yang
transparan. Dashboard saat ini menggunakan CatBoost native di
`backend/models/` untuk prediksi skenario. CatBoost tersebut dipilih dari
benchmark CatBoost, LightGBM, dan XGBoost pada label synthetic
physics-informed; karena itu semua outputnya wajib berstatus
`simulation_only` sampai dikalibrasi terhadap rekam servis armada nyata.

| Keluarga model | R² RUL | MAE RUL (km) | PR-AUC service due |
| --- | ---: | ---: | ---: |
| CatBoost (champion) | 0.9997 | 148.8 | 0.9975 |
| LightGBM | 0.9987 | 291.8 | 0.9971 |
| XGBoost | 0.9983 | 306.5 | 0.9972 |

Metrik di atas mengukur kesetiaan terhadap label simulasi, **bukan** akurasi
maintenance armada di lapangan. Detail split dan seluruh angka tersedia di
`../../reports/modeling/model_b_boosting_benchmark/benchmark_metrics.json`.

## Reproduksi benchmark

Jalankan dari root repository:

```powershell
cd backend/modeling
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\python -m pip install -e .
.venv\Scripts\python scripts/generate_model_b_synthetic_benchmark.py
.venv\Scripts\python scripts/benchmark_model_b_boosting.py
.venv\Scripts\python scripts/export_model_b_catboost_native.py
```

Skrip menggunakan direktori bersama Raksa Truck:

- data sintetis: `backend/data/synthetic/`;
- bobot riset: `backend/models/research/`;
- bobot deployment CatBoost: `backend/models/`;
- laporan eksperimen: `reports/modeling/`.

Beberapa pickle scikit-learn legacy di folder riset dibuat dengan
scikit-learn 1.2.1. Detail environment untuk membukanya tersedia di
`backend/models/research/README.md`; batas ini tidak memengaruhi CatBoost
native yang dipakai API.

Arsip sensor mentah Model A dan arsip EVIoT eksternal tidak disertakan dalam
repository ini. Untuk menjalankan ulang Model A, berikan folder arsip sensor
secara eksplisit melalui `run_model_a.py --data-dir <folder>`. Untuk benchmark
EVIoT, sediakan file berlisensi tersebut dengan
`train_model_b_benchmark.py --archive <file.zip>`.
