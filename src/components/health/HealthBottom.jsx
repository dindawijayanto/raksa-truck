import { AlertTriangle, CheckCircle2, Info } from 'lucide-react';
import Card from '../ui/Card';

function formatNumber(value, maximumFractionDigits = 0) {
  return new Intl.NumberFormat('id-ID', { maximumFractionDigits }).format(value);
}

export default function HealthBottom({ prediction }) {
  if (!prediction) return null;
  const serviceProbability = prediction.service_due_probability * 100;
  const actions = [
    {
      type: prediction.derived_features.overload ? 'warning' : 'success',
      text: prediction.derived_features.overload ? 'Kurangi muatan: skenario melewati batas berat kotor.' : 'Tidak ada flag overload pada skenario ini.',
    },
    {
      type: prediction.risk_band === 'high' ? 'warning' : 'success',
      text: `Risiko Model B berada pada band ${prediction.risk_band}.`,
    },
    {
      type: serviceProbability >= 45 ? 'warning' : 'success',
      text: `Probabilitas servis dalam 1.000 km: ${formatNumber(serviceProbability, 1)}%.`,
    },
  ];
  return (
    <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card>
        <h3 className="mb-4 text-[10px] font-bold uppercase tracking-widest text-slate-400">Tindakan yang disarankan</h3>
        <div className="flex flex-col gap-3">
          {actions.map((action) => (
            <div key={action.text} className={`flex items-start gap-3 rounded-xl p-4 text-sm font-medium ${action.type === 'success' ? 'bg-slate-50 text-slate-700' : 'bg-amber-50 text-amber-900'}`}>
              {action.type === 'success' ? <CheckCircle2 size={18} className="mt-0.5 shrink-0 text-teal-700" /> : <AlertTriangle size={18} className="mt-0.5 shrink-0 text-amber-500" />}
              <p>{action.text}</p>
            </div>
          ))}
        </div>
      </Card>
      <Card className="border border-amber-100 bg-amber-50/40">
        <div className="flex gap-3">
          <Info className="mt-0.5 shrink-0 text-amber-600" size={19} />
          <div>
            <h3 className="text-sm font-bold text-amber-900">Batas interpretasi Model B</h3>
            <p className="mt-2 text-xs leading-relaxed text-amber-800">Output berasal dari CatBoost pada label physics-informed synthetic. Ia berguna untuk demonstrasi skenario, alur dashboard, dan pengujian integrasi, tetapi belum boleh menjadi keputusan maintenance otomatis sebelum dikalibrasi dengan riwayat servis armada nyata.</p>
          </div>
        </div>
      </Card>
    </div>
  );
}
