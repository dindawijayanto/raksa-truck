# Raksa Truck — Model A & Model B integration

Raksa Truck adalah UI React/Vite untuk dashboard kendaraan. Repository ini kini menyertakan API FastAPI, artefak Model A, dan weight native CatBoost Model B.

- **Model A**: output empat sesi sensor (999 segmen total) ditampilkan secara dinamis pada halaman **Dashboard** dan **Rute**. Skor kekasaran hanya dapat dibandingkan di dalam sesi yang sama.
- **Model B**: halaman **Kesehatan** mengirim skenario truk dan rute ke API, lalu menampilkan estimasi wear dari weight CatBoost.

## Batas penggunaan model

Endpoint menghasilkan estimasi `damage_increment_pct`, `rul_km`, dan probabilitas `service_due_1000km` dari skenario muatan, rute, dan kondisi kendaraan. Weight CatBoost dilatih pada benchmark physics-informed sintetis, sehingga seluruh respons selalu berstatus **`simulation_only`**. Jangan gunakan hasil sebagai keputusan maintenance otomatis atau klaim prediksi kerusakan armada nyata.

## Struktur

```text
src/components/health/ModelBScenario.jsx  Panel input dan hasil prediksi di UI
src/components/route/ModelARoughnessExplorer.jsx  Output segmen dan hotspot Model A di UI
src/components/dashboard/ModelOverview.jsx Ringkasan laporan Model A/Model B di UI
backend/app/main.py                        API FastAPI
backend/app/model_service.py               Pemuatan weight dan feature engineering
backend/app/report_service.py              Pembacaan laporan sensor Model A
backend/models/                            Artefak Model A + CatBoost native .cbm + kontrak model
backend/data/                              Laporan input yang dipublikasikan ke UI
```

## Menjalankan lokal

Terminal 1 — API:

```bash
cd backend
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements.txt
.venv\Scripts\uvicorn app.main:app --reload --port 8000
```

Terminal 2 — UI:

```bash
npm install
npm run dev
```

Buka `http://localhost:5173/dashboard`, `http://localhost:5173/rute`, atau `http://localhost:5173/kesehatan`. Pada halaman Kesehatan, masukkan parameter perjalanan lalu tekan **Hitung skenario**. Saat development, Vite meneruskan permintaan `/api` ke `http://localhost:8000`. Dokumentasi interaktif API tersedia pada `http://localhost:8000/docs`.

Untuk hosting frontend dan API pada origin berbeda, salin `.env.example` ke `.env.local` dan isi `VITE_MODEL_API_URL` dengan URL endpoint API publik.

## Endpoint

`POST /api/v1/model-b/predict`

`GET /api/v1/dashboard/overview`

`GET /api/v1/model-a/sessions`

`GET /api/v1/model-a/sessions/{session_id}/segments?limit=120`

Contoh payload:

```json
{
  "truck_tare_kg": 6000,
  "gross_weight_limit_kg": 16000,
  "payload_kg": 6850,
  "axle_count": 3,
  "road_iri_m_per_km": 3.2,
  "speed_kmh": 48,
  "suspension_type": "leaf",
  "tire_pressure_ratio": 1.0,
  "trip_distance_km": 85,
  "cumulative_wear_pct": 28
}
```

## Cakupan UI

Panel **Model A** dan **Model B** di atas memanggil data/model nyata yang disertakan pada branch ini. Beberapa kartu navigasi, cuaca, peta dasar, dan contoh operasi yang sudah ada di UI asal masih merupakan data presentasi; kartu tersebut tidak diberi label sebagai keluaran model dan tidak boleh diinterpretasikan sebagai telemetri langsung.
