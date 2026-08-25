# Pipeline analitik AIC

> **Penyesuaian struktur Raksa Truck:** narasi asal di bawah memakai path
> proyek AI Center. Di repository ini, paket dan skripnya berada di
> `backend/modeling/`; laporan berada di `reports/modeling/`; data dashboard
> berada di `backend/data/`; artefak riset berada di
> `backend/models/research/`; sedangkan artifact deployable tetap berada di
> `backend/models/`. Jalankan seluruh perintah `python scripts/...` setelah
> `cd backend/modeling`. Lihat [README modelling](README.md) untuk path dan
> urutan reproduksi yang sudah disesuaikan.

Struktur ini memisahkan logika yang akan dipakai dashboard dari notebook:

```text
src/aic/
  data.py        # validasi dan pembacaan arsip sensor
  model_a.py     # IMU + GPS -> kekasaran relatif per sesi
  model_b.py     # skor keausan transparan dari beban + kekasaran + jarak
  benchmark.py   # benchmark eksternal EVIoT, bukan inferensi lokal
  synthetic.py   # fixture muatan simulasi yang berlabel jelas
scripts/
  run_model_a.py
  run_model_b.py
  train_model_b_benchmark.py
  generate_model_b_synthetic_benchmark.py
  train_model_b_synthetic_ml.py
notebooks/
  01_model_a_all_sessions.ipynb
  02_model_b_contextual_wear.ipynb
models/
  model_a/      # artefak K-Means/scaler/regresi per sesi
  model_b/      # bobot rule-based dan benchmark eksternal
```

## Menjalankan seluruh arsip untuk Model A

Untuk dashboard atau proses yang memuat artifact `joblib`, pasang paket lokal sekali:

```bash
pip install -e .
```

```bash
python scripts/run_model_a.py
```

Tabel hasil berada di `reports/model_a/`:

- `archive_audit.csv`: seluruh arsip termasuk yang dilewati beserta alasannya;
- `session_summary.csv`: metrik kualitas dan cluster per sesi;
- `segments.csv`: hasil per segmen yang siap dibaca dashboard.

Artefak Model A berada di `models/model_a/`. Setiap file `joblib` menyimpan seluruh parameter terlatih untuk satu sesi; `manifest.json` menjelaskan isi dan batas komparabilitasnya.

Skor `relative_roughness_score` hanya dapat dibandingkan **di dalam sesi yang sama**. Perangkat, kendaraan, dan frekuensi sampling berbeda antararsip, sehingga menggabungkannya menjadi satu peringkat global tidak sah.

## Menjalankan Model B

```bash
python scripts/run_model_b.py --load-kg 4000 --load-limit-kg 8000 --vehicle tt
```

Nilai `--load-kg` harus berasal dari load cell pada implementasi nyata. Untuk debugging boleh memakai skenario eksplisit seperti contoh di atas; output akan menyimpan konfigurasinya di `reports/model_b/run_config.json`. Filter `--vehicle tt` mencegah sesi `sepeda` diperlakukan sebagai perjalanan truk.

Jika tersedia pembacaan muatan aktual, kirim `--load-profile data/load_profile.csv` dengan kolom `session_id,load_kg` (opsional `segment_id`).

Sampai load cell tersedia, buat fixture debug secara eksplisit (bukan data lapangan):

```bash
python scripts/create_synthetic_load_profile.py --load-limit-kg 8000
python scripts/run_model_b.py --load-kg 4000 --load-limit-kg 8000 --vehicle tt \
  --load-profile data/synthetic/load_profile_demo.csv
```

Setiap baris fixture membawa `data_origin=synthetic_debug_fixture`. Jangan gunakan hasilnya untuk klaim akurasi atau keputusan servis nyata.

Model B saat ini memakai rumus transparan karena belum ada riwayat servis berlabel dari armada sendiri. Ia tidak mengklaim probabilitas gagal. Skor menunjukkan estimasi persentase umur servis yang telah terpakai sejak servis terakhir, dan selalu di-reset per sesi pada data demo ini.

Bobot Model B yang digunakan dashboard tersimpan di `models/model_b/contextual_wear_rule_based_v1.json`. Ini adalah bobot model rule-based, bukan file neural-network.

## Benchmark eksternal

`data/external/eviot_predictive_maintenance.zip` adalah EVIoT-PredictiveMaint Dataset dari Kaggle, berlisensi CC BY-NC-SA 4.0. Dataset tersebut dipakai terpisah untuk menguji baseline RUL terhadap fitur yang analog (`Load_Weight`, `Route_Roughness`, `Distance_Traveled`, `Driving_Speed`):

```bash
python scripts/train_model_b_benchmark.py
```

Hasil benchmark saat ini tidak cukup untuk ditransfer ke data lokal (`R²` temporal sekitar nol), sehingga model itu tidak dipakai untuk inferensi dashboard. Jangan menggunakannya sebagai model produksi sebelum tersedia kalibrasi silang, load-cell aktual, jarak sejak servis, dan label perawatan armada sendiri.

## Benchmark ML sintetis berbasis skenario truk

Untuk menguji jalur ML tanpa mengklaim data lapangan, jalankan:

```bash
python scripts/generate_model_b_synthetic_benchmark.py
python scripts/train_model_b_synthetic_ml.py
```

Weight tersimpan pada `models/model_b/synthetic_ml_v1/`, sedangkan visual benchmark berada di `reports/model_b_synthetic_ml/`. Metode, asumsi, dan rujukan ada di `docs/SYNTHETIC_ML_BENCHMARK.md`.
