import { CheckCircle2, ShieldAlert, ShieldCheck } from 'lucide-react';
import Card from '../ui/Card';

const riskStyle = {
  low: { label: 'Risiko Rendah', color: 'text-teal-700', border: 'border-teal-700', icon: ShieldCheck },
  medium: { label: 'Risiko Sedang', color: 'text-amber-700', border: 'border-amber-500', icon: ShieldAlert },
  high: { label: 'Risiko Tinggi', color: 'text-rose-700', border: 'border-rose-500', icon: ShieldAlert },
};

export default function HealthSidebar({ prediction }) {
  if (!prediction) {
    return <Card className="flex min-h-80 items-center justify-center text-center text-sm text-slate-500">Memuat output Model B…</Card>;
  }

  const state = riskStyle[prediction.risk_band];
  const Icon = state.icon;
  const checklists = [
    `Muatan ${Math.round(prediction.derived_features.payload_ratio * 100)}% dari kapasitas payload`,
    `Jalan ${prediction.derived_features.road_condition}`,
    prediction.derived_features.overload ? 'Muatan melewati batas berat kotor' : 'Tidak ada flag overload',
  ];
  return (
    <Card className="flex h-full flex-col bg-white">
      <div className="mb-6 text-center">
        <p className="mb-6 text-[10px] font-bold uppercase tracking-widest text-slate-400">Skor kesehatan skenario</p>
        <div className={`relative mx-auto mb-6 flex h-40 w-40 items-center justify-center rounded-full border-[12px] border-slate-100 ${state.border}`}>
          <div className="z-10 flex flex-col items-center text-center">
            <span className="text-5xl font-extrabold leading-none text-slate-800">{Math.round(prediction.scenario_health_score)}</span>
            <span className="mt-1 text-[10px] font-bold text-slate-400">/ 100</span>
          </div>
        </div>
        <div className={`mb-2 flex items-center justify-center gap-2 ${state.color}`}>
          <Icon size={20} />
          <h3 className="text-lg font-bold">{state.label}</h3>
        </div>
        <p className="px-4 text-xs leading-relaxed text-slate-500">Skor turunan untuk satu skenario; output ML berstatus simulation-only.</p>
      </div>
      <div className="mt-auto flex flex-col gap-3 border-t border-slate-100 pt-6">
        {checklists.map((item) => (
          <div key={item} className="flex items-start justify-between gap-2 text-sm font-medium text-slate-700">
            <span>{item}</span>
            <CheckCircle2 size={16} className={state.color} />
          </div>
        ))}
      </div>
    </Card>
  );
}
