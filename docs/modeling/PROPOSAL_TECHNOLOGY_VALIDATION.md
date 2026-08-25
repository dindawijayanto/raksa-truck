# 05 TECHNOLOGY & AI

> **Lokasi artefak pada repository Raksa Truck:** kode dan CLI offline ada di
> `backend/modeling/`, laporan eksperimen di `reports/modeling/`, artefak
> benchmark di `backend/models/research/`, dan weight deployable di
> `backend/models/`. Referensi navigasi lengkap ada di
> [README modelling](README.md).

> **Status dokumen:** proposal teknis MVP. Model A menghasilkan indikator kekasaran relatif, sedangkan Model B ML masih berstatus `simulation_only`. Angka benchmark pada dokumen ini tidak merepresentasikan akurasi terhadap armada nyata.

Bab ini memisahkan tiga tingkat pembuktian: validasi kualitas data, validasi internal terhadap model/simulator, dan validasi eksternal terhadap ground truth lapangan. Pemisahan tersebut memastikan hasil teknis yang sudah tersedia dapat dipresentasikan secara kuat tanpa mengklaim validasi yang belum dilakukan.

## 5.1 IoT Architecture

<!-- Diisi pada tahap berikutnya. -->

## 5.2 Road Roughness Model

Model A mengestimasi **kekasaran jalan relatif** dari data accelerometer dan GPS. Model ini dirancang sebagai alat pemetaan prioritas ruas jalan, bukan sebagai alat ukur International Roughness Index (IRI) absolut maupun diagnosis jenis kerusakan jalan. Pendekatan tersebut sesuai untuk tahap MVP karena data lapangan awal belum memiliki pengukuran IRI referensi.

Input Model A terdiri atas deret waktu accelerometer tiga sumbu, timestamp, koordinat GPS, kecepatan, dan akurasi GPS. Data diproses melalui tahapan berikut:

1. Validasi struktur arsip, kelengkapan sensor, timestamp, dan kualitas GPS.
2. Regularisasi sinyal ke frekuensi sampling sesi, low-pass filtering untuk mengestimasi gravitasi, lalu high-pass filtering untuk mengambil getaran dinamis.
3. Proyeksi getaran dinamis ke arah gravitasi lokal sehingga perubahan orientasi ponsel tidak langsung dianggap sebagai getaran vertikal.
4. Sinkronisasi GPS dan segmentasi spasial setiap 20 meter.
5. Ekstraksi fitur getaran, antara lain RMS vertikal, persentil amplitudo, vibration dose value per meter, dan band power spektral.
6. Koreksi sensitivitas kecepatan menggunakan Huber regression, kemudian perhitungan skor kekasaran relatif 0–100 berbasis peringkat fitur dalam satu sesi.
7. Pengelompokan K-Means menjadi tiga kelas: **Rendah**, **Sedang**, dan **Tinggi**. Segmen kelas tinggi pada persentil skor teratas ditandai sebagai kandidat hotspot.

Output utama Model A adalah skor, kelas kekasaran, koordinat, kecepatan rata-rata, quality flag, dan kandidat hotspot untuk setiap segmen. Semua output disimpan dalam tabel yang dapat langsung dikonsumsi dashboard. Model terlatih tiap sesi—K-Means, RobustScaler, dan speed-correction regressor—juga disimpan sebagai artifact `joblib` agar hasil dapat direproduksi.

Karena perangkat, mounting, kendaraan, dan frekuensi sampling dapat berbeda, skor Model A **hanya boleh dibandingkan di dalam sesi yang sama**. Kalibrasi menuju IRI absolut membutuhkan pengukuran profil jalan atau IRI referensi pada ruas yang sama.

## 5.3 Vehicle Wear Model

Model B mengubah konteks perjalanan menjadi estimasi beban keausan dan prioritas servis. Pada MVP, terdapat dua lapisan model yang sengaja dipisahkan.

### A. Model operasional transparan

Model rule-based digunakan sebagai model operasional awal karena belum tersedia label servis, kerusakan komponen, pembacaan load cell, dan odometer sejak servis dari armada target. Model menghitung:

```text
context_score = 100 × [0,60 × min(load_kg / load_limit_kg, 1)
                       + 0,40 × (relative_roughness_score / 100)]

wear_multiplier = 1
                  + 0,60 × load_ratio
                  + 0,40 × roughness_ratio
                  + 0,20 × load_ratio × roughness_ratio
```

Nilai tersebut dikalikan dengan jarak tempuh untuk menghasilkan `wear_increment`, `cumulative_wear_score`, estimasi jarak servis tersisa, flag overload, dan band risiko Rendah/Sedang/Tinggi. Bobot 0,60 untuk beban, 0,40 untuk kekasaran, dan 0,20 untuk interaksi disimpan sebagai weight model yang dapat ditinjau dan diubah melalui konfigurasi. Pendekatan transparan ini membuat rekomendasi mudah dijelaskan kepada pemilik armada: muatan yang lebih tinggi dan jalan yang lebih kasar meningkatkan laju konsumsi umur servis.

### B. Physics-informed synthetic ML benchmark

Untuk menyiapkan jalur ML tanpa mengklaim data servis yang belum dimiliki, dibuat benchmark sintetis berbasis skenario truk. Benchmark mencakup tiga template truk generik (ringan 8 t, medium 16 t, berat 30 t), rasio muatan 0–110%, tiga kelas jalan berbasis IRI, empat kecepatan, dua tipe suspensi, variasi tekanan ban, dan beberapa seed profil jalan.

Label simulasi dibentuk dari hubungan beban, kekasaran, kecepatan, dynamic load coefficient, dan akumulasi damage. Surrogate ML menggunakan `HistGradientBoostingRegressor` untuk memprediksi `damage_increment` dan Remaining Useful Life (RUL), serta `HistGradientBoostingClassifier` untuk memprediksi risiko servis dalam 1.000 km. Artifact ML, model card, dan visual evaluasi disimpan terpisah dari model operasional.

Benchmark ini berguna untuk menguji arsitektur ML, struktur feature, format weight, dan tampilan dashboard. Namun, performanya **hanya menunjukkan kecocokan terhadap label simulasi**, bukan akurasi terhadap armada di lapangan. Model ML baru dapat dipromosikan menjadi model produksi setelah dikalibrasi dengan data muatan, kondisi kendaraan, dan riwayat perawatan armada nyata.

#### Rancangan dataset dan pembentukan label

Benchmark membangkitkan **15.000 perjalanan sintetis** dari 60 identitas kendaraan: tiga template truk generik (ringan 8 t GVM/2 axle, medium 16 t/3 axle, berat 30 t/4 axle), masing-masing 20 unit dengan 250 perjalanan. Variasi eksposur mencakup rasio muatan 0%, 50%, 75%, 100%, dan 110% kapasitas payload; IRI sintetis smooth 1,0–2,3, medium 2,3–3,8, dan rough 3,8–5,5 m/km; kecepatan 24, 48, 72, dan 89 km/jam; suspensi leaf/air; tekanan ban 85%, 100%, dan 115%; serta tiga seed profil jalan.

Level 110% hanya digunakan sebagai *stress test* ODOL dan bukan rekomendasi operasi. Rentang faktor dinamis diturunkan dari rancangan eksperimen kendaraan berat yang memasukkan roughness, kecepatan, beban roda, dan tekanan ban [3]. Profil jalan sintetis mengacu pada prinsip pembentukan profil untuk evaluasi kekasaran [4]. Eksponen beban 3,5 digunakan sebagai titik tengah *sensitivity range* 3–4 dalam studi dampak beban kendaraan berat [5]; nilai ini merupakan asumsi simulator, bukan konstanta universal kerusakan komponen.

Untuk setiap perjalanan, *dynamic load coefficient* (DLC) dibentuk dari IRI, kecepatan, suspensi, tekanan ban, dan noise kecil. Label kemudian dibentuk melalui persamaan berikut:

```text
damage_rate = gross_weight_ratio^3.5 × roughness_factor × speed_factor
              × (1 + DLC) × tire_factor × suspension_factor
              / nominal_service_life_km

damage_increment_pct = 100 × damage_rate × trip_distance_km
RUL_km               = (1 − cumulative_damage) / damage_rate
service_due_1000km   = 1 apabila RUL_km ≤ 1.000 km
```

Fitur yang dipakai adalah `gross_weight_ratio`, `payload_ratio`, `axle_count`, `road_iri_m_per_km`, `speed_kmh`, `suspension_is_air`, `tire_pressure_ratio`, `trip_distance_km`, `dynamic_load_coefficient`, dan `cumulative_wear_pct`. Tidak ada observasi maintenance armada nyata di dalam data ini.

#### Protokol kandidat ML

Selain baseline HistGradientBoosting, benchmark membandingkan CatBoost, LightGBM, dan XGBoost—tiga keluarga *gradient-boosted decision tree* yang umum digunakan untuk data tabular [7]–[9]. Masing-masing keluarga melatih tiga estimator: regresi `damage_increment_pct`, regresi `rul_km`, dan klasifikasi `service_due_1000km`. Target regresi ditransformasi dengan `log1p` ketika pelatihan lalu dikembalikan ke satuan asli sebelum metrik dihitung.

Semua kandidat memakai satu split yang identik, yaitu `GroupShuffleSplit` berdasarkan `fleet_unit_id`: 45 unit/11.250 perjalanan untuk pelatihan dan 15 unit/3.750 perjalanan untuk pengujian. Dengan demikian, tidak ada sampel dari kendaraan uji yang terlihat oleh model ketika training. Kelas service-due dibobotkan agar kontribusi kelas positif dan negatif seimbang. Protokol menggunakan 450 boosting rounds, learning rate 0,06, regularisasi, dan empat worker CPU untuk menjaga perbandingan dapat direproduksi di lingkungan yang sama.

## 5.4 Data Pipeline

Pipeline data dibangun modular agar notebook, CLI, dan dashboard menggunakan logika yang sama.

```text
Arsip sesi sensor
    ↓
Validasi ZIP, skema CSV, timestamp, dan kualitas GPS
    ↓
Model A: preprocessing IMU + GPS → roughness per segmen
    ↓
Tabel Model A: segment score, hotspot, quality flag
    ↓
Model B: load profile + roughness + jarak → wear score / RUL
    ↓
Tabel dashboard, visual report, dan model artifacts
```

Setiap arsip yang dibaca dicatat pada `archive_audit.csv`. Arsip korup, kolom yang hilang, atau sesi yang tidak memenuhi syarat tidak diabaikan secara diam-diam, melainkan diberi alasan `skipped`. Hasil Model A disimpan pada `reports/model_a/`; hasil operasional Model B pada `reports/model_b/`; dan hasil benchmark ML sintetis pada `reports/model_b_synthetic_ml/`.

Struktur kode memisahkan pembacaan data, konfigurasi, Model A, Model B, simulasi, reporting, dan script eksekusi. Karena itu dashboard dapat memanggil fungsi yang sama tanpa menyalin logika dari notebook. Artifact model disimpan pada `models/` dan dapat dimuat kembali setelah paket analitik dipasang.

Untuk benchmark tiga model, keluaran disimpan terpisah agar tidak tertukar dengan model operasional: `models/model_b/synthetic_boosting_benchmark_v1/` memuat bundle `catboost_model_b_synthetic_bundle_v1.joblib`, `lightgbm_model_b_synthetic_bundle_v1.joblib`, `xgboost_model_b_synthetic_bundle_v1.joblib`, dan `model_card.json`. Laporan pendukung berada di `reports/model_b_boosting_benchmark/` dan memuat `benchmark_metrics.csv`, `test_predictions.csv`, `rul_feature_importance.csv`, serta `boosting_benchmark.png`. Setelah penulisan, setiap bundle dimuat kembali dan diberi satu inferensi uji; pola ini mencegah dashboard menerima bobot yang tidak lengkap atau tidak kompatibel.

# 06 VALIDATION

## 6.1 Data Collection

Data awal dikumpulkan dalam format arsip sesi yang memuat `imu.csv`, `gps.csv`, `orientation.csv`, `markers.csv`, metadata, serta quality report. Accelerometer direkam pada sekitar 50–100 Hz dan GPS sekitar 1 Hz. Pipeline telah diuji pada empat arsip yang dapat dibaca, menghasilkan 999 segmen Model A; satu arsip korup tercatat dan tidak diproses.

Untuk validasi MVP berikutnya, pengumpulan data harus memakai protokol yang lebih terkontrol:

- kendaraan, posisi mounting, orientasi perangkat, tekanan ban, dan kondisi cuaca dicatat pada setiap sesi;
- beberapa lintasan di ruas yang sama direkam pada kecepatan dan muatan berbeda;
- muatan dicatat melalui load cell atau timbangan yang dapat ditelusuri;
- jarak kumulatif sejak servis terakhir dan event servis dicatat per kendaraan;
- pengambilan data mencakup jalan halus, sedang, kasar, polisi tidur, sambungan jalan, dan pothole;
- data dibagi berdasarkan kendaraan, rute, dan sesi, bukan secara acak per segmen yang berdekatan.

## 6.2 Ground Truth

Ground truth untuk Model A dan Model B harus dibangun secara terpisah.

Untuk Model A, ground truth minimum berupa pengukuran IRI/profil jalan referensi pada ruas yang sama, atau setidaknya anotasi lapangan dan video untuk menandai pothole, speed bump, sambungan jalan, dan segmen normal. Pengukuran diulang pada beberapa lintasan agar kestabilan skor dapat diuji.

Untuk Model B, ground truth mencakup berat muatan aktual, berat sumbu bila tersedia, odometer sejak servis, jenis servis, tanggal servis, komponen yang diganti, dan indikasi kerusakan. Riwayat tersebut memungkinkan label seperti waktu menuju servis, biaya maintenance, atau failure within horizon dibentuk tanpa membuat asumsi sintetis.

Sebelum ground truth tersedia, data sintetis hanya dipakai sebagai benchmark engineering. Ia tidak boleh digabungkan dengan data lapangan lalu dilaporkan sebagai satu dataset nyata.

## 6.3 Model Evaluation

Evaluasi Model A dilakukan sesuai ketersediaan ground truth.

- **Tanpa IRI/label eksternal:** cek kelengkapan data, gap sensor, akurasi GPS, kestabilan cluster bootstrap, silhouette score, ukuran kelas cluster, dan konsistensi repeated pass. Metrik ini mengevaluasi struktur internal, bukan akurasi kondisi jalan.
- **Dengan IRI referensi:** laporkan MAE, RMSE, R², dan korelasi Spearman antara roughness prediction dan IRI per segmen/rute.
- **Dengan anotasi event:** laporkan precision, recall, F1, dan PR-AUC untuk deteksi hotspot/pothole, dengan split berbasis rute atau sesi.

Evaluasi Model B dibagi menjadi dua jalur.

- **Rule-based model:** dievaluasi melalui monotonicity test, yaitu skor harus meningkat ketika muatan atau kekasaran meningkat pada kondisi lain yang sama; lalu divalidasi terhadap frekuensi servis dan biaya maintenance aktual setelah data tersedia.
- **Synthetic ML benchmark:** menggunakan group hold-out berdasarkan `fleet_unit_id`. Metrik RUL adalah R², MAE, dan RMSE; metrik service horizon adalah PR-AUC, precision, dan recall. Metrik benchmark hanya membuktikan fidelity terhadap simulator.
- **Field ML model:** setelah data cukup, training/validation/test harus dipisahkan berdasarkan kendaraan dan periode waktu. Hindari random split per segmen karena dapat menyebabkan data leakage antar perjalanan yang berdekatan.

### Hasil benchmark CatBoost, LightGBM, dan XGBoost

Tabel berikut dihasilkan dari *group-held-out test set* berisi 3.750 perjalanan dari 15 kendaraan sintetis yang sepenuhnya tidak digunakan ketika pelatihan. Metrik ditulis pada satuan asli target. `MAE damage increment` adalah galat dalam poin persentase per perjalanan; precision dan recall memakai ambang probabilitas 0,50 untuk event servis dalam ≤1.000 km.

| Model | Waktu latih (detik) | R² damage increment | MAE damage increment | R² RUL | MAE RUL (km) | RMSE RUL (km) | PR-AUC service due | Precision | Recall |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| CatBoost | 17,66 | 0,9997 | 0,0084 | **0,9997** | **148,80** | **468,04** | **0,9975** | 0,9367 | **0,9867** |
| LightGBM | **4,80** | 0,9992 | 0,0146 | 0,9987 | 291,83 | 1.013,20 | 0,9971 | **0,9578** | 0,9833 |
| XGBoost | 6,10 | 0,9990 | 0,0154 | 0,9983 | 306,55 | 1.187,64 | 0,9972 | 0,9482 | 0,9767 |

Aturan pemilihan kandidat adalah R² RUL tertinggi, dilanjutkan PR-AUC service due tertinggi, lalu MAE RUL terendah. Berdasarkan aturan ini **CatBoost adalah champion pada benchmark sintetis**, sedangkan LightGBM merupakan kandidat tercepat. CatBoost juga memperoleh R² damage increment 0,9997 dan PR-AUC 0,9975. Hasil tersebut menunjukkan bahwa pipeline dapat membandingkan tiga keluarga model pada target, fitur, dan split yang adil.

Interpretasi hasil harus dibatasi secara ketat. Nilai R² yang mendekati satu terjadi karena RUL dan damage adalah label yang diturunkan secara deterministik dari hubungan simulator yang menerima fitur-fitur yang sama. Hasil tersebut membuktikan *fidelity* terhadap generator data, bukan “akurasi prediksi kerusakan truk 99,97%”. Klaim yang sah adalah bahwa struktur ML, pembagian data per kendaraan, format artifact, dan alur inferensi telah berfungsi secara konsisten.

Sebagai pemeriksaan interpretabilitas internal, tiga fitur RUL dengan *native feature importance* terbesar pada CatBoost adalah `cumulative_wear_pct` (47,53%), `payload_ratio` (24,21%), dan `gross_weight_ratio` (24,03%). Urutan ini konsisten dengan label simulator, namun belum boleh diperlakukan sebagai bukti kausal pada armada. Feature importance lengkap untuk tiga model tersedia pada `reports/model_b_boosting_benchmark/rul_feature_importance.csv`.

### Kriteria promosi dan reproduksibilitas

CatBoost tetap berstatus `simulation_only` dan baru boleh menjadi kandidat pilot apabila: (1) diuji pada kendaraan serta periode waktu yang tidak muncul saat training; (2) dibandingkan terhadap servis/inspeksi aktual dengan MAE/RMSE untuk *time-to-service* dan PR-AUC, recall, serta calibration untuk *failure horizon*; (3) dievaluasi menurut kelas kendaraan, muatan, rute, umur kendaraan, dan kondisi operasi; serta (4) diuji manfaat operasionalnya dengan *human review*, bukan keputusan servis otomatis.

Benchmark dapat direproduksi melalui:

```bash
python scripts/generate_model_b_synthetic_benchmark.py
python scripts/benchmark_model_b_boosting.py
```

Model card menyimpan konfigurasi simulasi, protokol split, aturan pemilihan champion, dan metrik seluruh kandidat. Script benchmark juga memverifikasi pemuatan kembali setiap bobot serta satu inferensi uji setelah proses penyimpanan selesai.

## 6.4 MVP Limitations

MVP ini memiliki batasan yang perlu dinyatakan secara eksplisit.

1. Model A menghasilkan kekasaran relatif per sesi, bukan IRI absolut.
2. Data awal belum cukup untuk membuktikan generalisasi dari perangkat/sepeda atau sesi uji ke truk operasional.
3. Pembacaan load cell, berat sumbu, jarak sejak servis, dan riwayat maintenance armada belum tersedia sebagai ground truth.
4. Model B rule-based bersifat explainable tetapi belum merupakan prediktor failure terkalibrasi.
5. Model B ML memiliki hasil tinggi pada benchmark sintetis, tetapi belum tervalidasi terhadap data kendaraan nyata dan tidak boleh digunakan untuk keputusan servis aktual.
6. GPS dengan akurasi buruk, gap sensor, perubahan mounting, perilaku pengemudi, dan kondisi ban dapat memengaruhi sinyal getaran.
7. Pemakaian level muatan di atas kapasitas pada simulasi bertujuan untuk stress-test dan analisis ODOL, bukan sebagai rekomendasi operasi.
8. Simulator menyederhanakan mekanika kendaraan: eksponen damage, service life nominal, respons suspensi, serta dynamic load coefficient harus dikalibrasi menurut komponen dan jenis kendaraan target.
9. Benchmark menggunakan CPU agar dapat direproduksi lintas lingkungan. Akselerator dapat digunakan untuk eksperimen berskala lebih besar, tetapi tidak menggantikan ground truth maupun validasi eksternal.

Dengan menyatakan batasan tersebut, MVP tetap dapat menunjukkan nilai praktis: pemetaan kandidat ruas kasar, transparansi dampak muatan terhadap wear score, dan fondasi data/model yang siap dikalibrasi ketika telemetri armada dan ground truth tersedia.

## Referensi Teknis

1. Zhang, K. et al. (2018). *Assessing and Mapping of Road Surface Roughness Based on GPS and Accelerometer Sensors on Bicycle-Mounted Smartphones*. Sensors, 18(3), 914. https://doi.org/10.3390/s18030914
2. Alessandroni, G. et al. (2017). *A Study on the Influence of Speed on Road Roughness Sensing*. Sensors, 17(2), 1017. https://doi.org/10.3390/s17051017
3. Kulakowski, B. T. et al. *A Study of Dynamic Wheel Loads Conducted Using a Four-Post Road Simulator*. https://hvttforum.org/wp-content/uploads/2019/11/A-Study-Of-Dynamic-Wheel-Loads-Conducted-Using-A-Four-Post-Road-Simulator-Kulakowski-.pdf
4. Loprencipe, G. & Zoccali, P. (2017). *Use of Generated Artificial Road Profiles in Road Roughness Evaluation*. Journal of Modern Transportation, 25, 24–33. https://doi.org/10.1007/s40534-017-0122-1
5. Federal Highway Administration. *Comprehensive Truck Size and Weight Study, Volume 3, Chapter 5*. https://www.fhwa.dot.gov/reports/tswstudy/vol3-chapter5.pdf
6. Boéssio, M. L., Morsch, I. B., & Awruch, A. M. (2006). *Fatigue Lifetime Estimation of Commercial Vehicles*. Journal of Sound and Vibration, 291, 169–191. https://doi.org/10.1016/j.jsv.2005.06.002
7. Prokhorenkova, L. et al. (2018). *CatBoost: Unbiased Boosting with Categorical Features*. NeurIPS 31. https://proceedings.neurips.cc/paper/2018/hash/14491b756b3a51daac41c24863285549-Abstract.html
8. Ke, G. et al. (2017). *LightGBM: A Highly Efficient Gradient Boosting Decision Tree*. NeurIPS 30. https://proceedings.neurips.cc/paper/2017/hash/6449f44a102fde848669bdd9eb6b76fa-Abstract.html
9. Chen, T. & Guestrin, C. (2016). *XGBoost: A Scalable Tree Boosting System*. KDD ’16, 785–794. https://doi.org/10.1145/2939672.2939785
