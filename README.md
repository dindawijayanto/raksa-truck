# Raksa Truck — Model B integration

Raksa Truck adalah UI React/Vite untuk dashboard kendaraan. Repository ini kini menyertakan API FastAPI dan weight native CatBoost untuk menjalankan **Model B scenario estimate** langsung dari halaman **Kesehatan**.

## Batas penggunaan model

Endpoint menghasilkan estimasi `damage_increment_pct`, `rul_km`, dan probabilitas `service_due_1000km` dari skenario muatan, rute, dan kondisi kendaraan. Weight CatBoost dilatih pada benchmark physics-informed sintetis, sehingga seluruh respons selalu berstatus **`simulation_only`**. Jangan gunakan hasil sebagai keputusan maintenance otomatis atau klaim prediksi kerusakan armada nyata.

## Struktur

```text
src/components/health/ModelBScenario.jsx  Panel input dan hasil prediksi di UI
backend/app/main.py                        API FastAPI
backend/app/model_service.py               Pemuatan weight dan feature engineering
backend/models/                            CatBoost native .cbm + kontrak model
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

Buka `http://localhost:5173/kesehatan`, masukkan parameter perjalanan, lalu tekan **Hitung skenario**. Saat development, Vite meneruskan permintaan `/api` ke `http://localhost:8000`. Dokumentasi interaktif API tersedia pada `http://localhost:8000/docs`.

Untuk hosting frontend dan API pada origin berbeda, salin `.env.example` ke `.env.local` dan isi `VITE_MODEL_API_URL` dengan URL endpoint API publik.

## Endpoint

`POST /api/v1/model-b/predict`

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
