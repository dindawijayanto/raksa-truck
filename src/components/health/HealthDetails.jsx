import { Activity, BrainCircuit, Gauge, Map, Settings, Wrench } from 'lucide-react';
import Card from '../ui/Card';

const roadLabels = { smooth: 'Halus', medium: 'Sedang', rough: 'Kasar' };

function formatNumber(value, maximumFractionDigits = 0) {
  return new Intl.NumberFormat('id-ID', { maximumFractionDigits }).format(value);
}

export default function HealthDetails({ prediction }) {
  if (!prediction) {
    return <Card className="flex min-h-80 items-center justify-center text-center text-sm text-slate-500">Menunggu prediksi Model B dari API…</Card>;
  }

  const serviceProbability = prediction.service_due_probability * 100;
  return (
    <div className="flex flex-col gap-6">
      <Card className="border-l-[6px] border-l-blue-600 bg-white">
        <div className="flex items-start gap-4">
          <div className="shrink-0 rounded-full bg-blue-50 p-2 text-blue-600"><BrainCircuit size={20} /></div>
          <div>
            <h3 className="mb-2 text-lg font-bold text-slate-800">Analisis Model B untuk skenario aktif</h3>
            <p className="text-sm leading-relaxed text-slate-600">Risiko {prediction.risk_band}, estimasi RUL {formatNumber(prediction.predicted_rul_km)} km, dan probabilitas servis dalam 1.000 km sebesar {formatNumber(serviceProbability, 1)}%. Nilai dibentuk dari muatan, IRI, kecepatan, tekanan ban, jarak, dan wear kumulatif.</p>
          </div>
        </div>
      </Card>

      <div className="grid grid-cols-2 gap-4">
        <MetricCard label="Rasio muatan" value={`${formatNumber(prediction.derived_features.payload_ratio * 100, 1)}%`} detail="dari kapasitas payload" icon={Gauge} tone="text-blue-700" />
        <MetricCard label="Kondisi jalan" value={roadLabels[prediction.derived_features.road_condition]} detail="berdasarkan IRI skenario" icon={Map} tone="text-teal-700" />
        <MetricCard label="Damage perjalanan" value={`${formatNumber(prediction.predicted_damage_increment_pct, 3)}%`} detail="estimasi kenaikan damage" icon={Activity} tone="text-amber-600" />
        <MetricCard label="Wear kumulatif" value={`${formatNumber(100 - prediction.scenario_health_score, 1)}%`} detail="indikator skenario" icon={Settings} tone="text-violet-700" />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="p-5">
          <span className="mb-4 block text-[10px] font-bold uppercase tracking-widest text-slate-400">Respons model</span>
          <div className="flex flex-col gap-3 text-sm font-medium text-slate-700">
            <div className="flex items-center justify-between gap-2"><span>Gross weight ratio</span><strong>{formatNumber(prediction.derived_features.gross_weight_ratio * 100, 1)}%</strong></div>
            <div className="flex items-center justify-between gap-2"><span>Dynamic load coefficient</span><strong>{formatNumber(prediction.derived_features.dynamic_load_coefficient, 3)}</strong></div>
            <div className="flex items-center justify-between gap-2"><span>Flag overload</span><strong>{prediction.derived_features.overload ? 'Ya' : 'Tidak'}</strong></div>
          </div>
        </Card>
        <Card className="relative flex flex-col justify-between overflow-hidden p-5">
          <div>
            <span className="mb-2 block text-[10px] font-bold uppercase tracking-widest text-slate-400">Prediksi servis</span>
            <p className="mb-3 text-[10px] leading-tight text-slate-500">Remaining Useful Life dari CatBoost benchmark. Ini bukan jadwal servis yang tervalidasi di lapangan.</p>
            <p className="text-4xl font-bold text-slate-800">{formatNumber(prediction.predicted_rul_km)} <span className="text-sm font-normal text-slate-500">km</span></p>
            <p className="mt-1 text-xs font-bold text-blue-600">Probabilitas service due: {formatNumber(serviceProbability, 1)}%</p>
          </div>
          <Wrench className="absolute -bottom-5 -right-3 h-24 w-24 text-slate-50" />
        </Card>
      </div>
    </div>
  );
}

function MetricCard({ label, value, detail, icon: Icon, tone }) {
  return (
    <Card className="flex flex-col justify-between p-5">
      <div className="mb-4 flex items-center justify-between gap-2"><span className="text-[10px] font-bold uppercase tracking-widest text-slate-400">{label}</span><Icon size={14} className={tone} /></div>
      <p className="text-2xl font-bold text-slate-800">{value}</p>
      <p className="mt-2 text-[10px] text-slate-500">{detail}</p>
    </Card>
  );
}
