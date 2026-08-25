import { useState } from 'react';
import { AlertTriangle, BrainCircuit, LoaderCircle, RefreshCw, ShieldAlert, Sparkles } from 'lucide-react';
import Card from '../ui/Card';
import { predictModelBScenario } from '../../lib/modelBApi';

const initialScenario = {
  truck_tare_kg: 6000,
  gross_weight_limit_kg: 16000,
  payload_kg: 6850,
  axle_count: 3,
  road_iri_m_per_km: 3.2,
  speed_kmh: 48,
  suspension_type: 'leaf',
  tire_pressure_ratio: 1,
  trip_distance_km: 85,
  cumulative_wear_pct: 28,
};

const numberFields = [
  ['truck_tare_kg', 'Berat kosong', 'kg', 100],
  ['gross_weight_limit_kg', 'Batas berat kotor', 'kg', 100],
  ['payload_kg', 'Muatan', 'kg', 100],
  ['axle_count', 'Jumlah sumbu', '', 1],
  ['road_iri_m_per_km', 'IRI jalan', 'm/km', 0.1],
  ['speed_kmh', 'Kecepatan', 'km/jam', 1],
  ['tire_pressure_ratio', 'Rasio tekanan ban', '× nominal', 0.05],
  ['trip_distance_km', 'Jarak perjalanan', 'km', 1],
  ['cumulative_wear_pct', 'Wear kumulatif', '%', 1],
];
const numericFieldNames = numberFields.map(([name]) => name);

const roadLabels = { smooth: 'Halus', medium: 'Sedang', rough: 'Kasar' };
const riskStyles = {
  low: 'bg-emerald-50 text-emerald-700 border-emerald-100',
  medium: 'bg-amber-50 text-amber-700 border-amber-100',
  high: 'bg-rose-50 text-rose-700 border-rose-100',
};

function formatNumber(value, maximumFractionDigits = 0) {
  return new Intl.NumberFormat('id-ID', { maximumFractionDigits }).format(value);
}

export default function ModelBScenario({ onPrediction }) {
  const [scenario, setScenario] = useState(initialScenario);
  const [prediction, setPrediction] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const updateNumber = (name, value) => {
    // Keep the text the user is actively editing. Coercing an empty input to
    // Number('') creates a visible zero and makes values such as 7000 become 07000.
    setScenario((current) => ({ ...current, [name]: value }));
  };

  const normalizeNumber = (name) => {
    setScenario((current) => {
      const value = current[name];
      if (value === '') return current;
      const numericValue = Number(value);
      return Number.isFinite(numericValue) ? { ...current, [name]: String(numericValue) } : current;
    });
  };

  const requestPrediction = async (payload) => {
    setError('');
    setIsLoading(true);
    try {
      const result = await predictModelBScenario(payload);
      setPrediction(result);
      onPrediction?.(result);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : 'Terjadi kesalahan saat memanggil model.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    const payload = {
      ...scenario,
      ...Object.fromEntries(numericFieldNames.map((name) => [name, Number(scenario[name])])),
    };
    await requestPrediction(payload);
  };

  return (
    <Card className="mb-6 border border-blue-100 bg-gradient-to-br from-white via-white to-blue-50/60">
      <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
        <div>
          <div className="mb-2 flex items-center gap-2 text-blue-700">
            <BrainCircuit size={20} />
            <span className="text-xs font-bold uppercase tracking-[0.16em]">Model B Scenario Lab</span>
          </div>
          <h2 className="text-2xl font-extrabold text-slate-900">Estimasi wear perjalanan</h2>
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-slate-600">
            Masukkan konteks truk dan rute. Panel ini memanggil weight CatBoost yang di-deploy dari benchmark Model B.
          </p>
        </div>
        <span className="inline-flex items-center gap-1.5 self-start rounded-full border border-amber-200 bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-700">
          <ShieldAlert size={14} /> Simulation only
        </span>
      </div>

      <form className="mt-6 grid grid-cols-1 gap-3 sm:grid-cols-2 xl:grid-cols-5" onSubmit={handleSubmit}>
        {numberFields.map(([name, label, unit, step]) => (
          <label key={name} className="rounded-xl border border-slate-200 bg-white px-3 py-2.5">
            <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</span>
            <div className="mt-1 flex items-center gap-1">
              <input
                className="min-w-0 w-full bg-transparent text-sm font-bold text-slate-800 outline-none"
                name={name}
                type="number"
                min="0"
                step={step}
                value={scenario[name]}
                onChange={(event) => updateNumber(name, event.target.value)}
                onBlur={() => normalizeNumber(name)}
                required
              />
              <span className="whitespace-nowrap text-[10px] font-medium text-slate-400">{unit}</span>
            </div>
          </label>
        ))}
        <label className="rounded-xl border border-slate-200 bg-white px-3 py-2.5">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Suspensi</span>
          <select
            className="mt-1 w-full bg-transparent text-sm font-bold text-slate-800 outline-none"
            value={scenario.suspension_type}
            onChange={(event) => setScenario((current) => ({ ...current, suspension_type: event.target.value }))}
          >
            <option value="leaf">Leaf</option>
            <option value="air">Air</option>
          </select>
        </label>
        <div className="flex items-center sm:col-span-2 xl:col-span-1">
          <button
            className="flex w-full items-center justify-center gap-2 rounded-xl bg-blue-700 px-4 py-3 text-sm font-bold text-white transition hover:bg-blue-800 disabled:cursor-wait disabled:bg-blue-400"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? <LoaderCircle className="animate-spin" size={18} /> : <Sparkles size={18} />}
            {isLoading ? 'Menghitung…' : 'Hitung skenario'}
          </button>
        </div>
      </form>

      {error ? (
        <div className="mt-5 flex items-start gap-2 rounded-xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-800" role="alert">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <div>
            <p className="font-bold">Model API belum dapat dihubungi</p>
            <p className="mt-1 text-rose-700">{error}</p>
            <p className="mt-1 text-xs text-rose-600">Jalankan backend pada port 8000 atau atur `VITE_MODEL_API_URL`.</p>
          </div>
        </div>
      ) : null}

      {prediction ? (
        <div className="mt-5 rounded-2xl border border-slate-200 bg-white p-4" aria-live="polite">
          <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
            <div className="flex items-center gap-2">
              <RefreshCw size={16} className="text-blue-600" />
              <p className="text-sm font-bold text-slate-800">Output CatBoost untuk skenario ini</p>
            </div>
            <span className={`rounded-full border px-2.5 py-1 text-xs font-bold capitalize ${riskStyles[prediction.risk_band]}`}>
              Risiko {prediction.risk_band}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
            <Metric label="RUL skenario" value={`${formatNumber(prediction.predicted_rul_km)} km`} />
            <Metric label="Probabilitas servis ≤1.000 km" value={`${formatNumber(prediction.service_due_probability * 100, 1)}%`} />
            <Metric label="Damage perjalanan" value={`${formatNumber(prediction.predicted_damage_increment_pct, 3)}%`} />
            <Metric label="Kondisi rute" value={roadLabels[prediction.derived_features.road_condition]} />
          </div>
          <p className="mt-4 text-xs leading-relaxed text-amber-700">{prediction.notice}</p>
        </div>
      ) : null}
    </Card>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl bg-slate-50 px-3 py-3">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-1 text-lg font-extrabold text-slate-800">{value}</p>
    </div>
  );
}
