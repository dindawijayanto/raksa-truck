import { useEffect, useState } from 'react';
import { Activity, AlertTriangle, MapPinned, Route } from 'lucide-react';
import Card from '../ui/Card';
import { getDashboardOverview } from '../../lib/modelReportsApi';

function formatNumber(value, maximumFractionDigits = 0) {
  return new Intl.NumberFormat('id-ID', { maximumFractionDigits }).format(value);
}

export default function ModelOverview() {
  const [overview, setOverview] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;
    getDashboardOverview()
      .then((response) => {
        if (isActive) setOverview(response);
      })
      .catch((requestError) => {
        if (isActive) setError(requestError instanceof Error ? requestError.message : 'Gagal memuat data model.');
      });
    return () => {
      isActive = false;
    };
  }, []);

  if (error) {
    return (
      <Card className="mb-6 border border-rose-200 bg-rose-50">
        <div className="flex items-start gap-3 text-rose-800">
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <p className="text-sm">Data Model A/Model B belum tersedia: {error}</p>
        </div>
      </Card>
    );
  }

  if (!overview) {
    return <Card className="mb-6 h-36 animate-pulse bg-slate-100" />;
  }

  const modelA = overview.model_a;
  const latestWear = overview.model_b_rule_based.sessions.at(-1);
  return (
    <section className="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
      <Card className="border border-teal-100 bg-gradient-to-br from-white to-teal-50/70">
        <div className="mb-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-teal-100 p-2 text-teal-700"><MapPinned size={20} /></div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-teal-700">Model A · Jalan</p>
              <h3 className="font-bold text-slate-800">Kekasaran relatif per sesi</h3>
            </div>
          </div>
          <span className="rounded-full bg-white px-2.5 py-1 text-xs font-bold text-teal-700 shadow-sm">Report-backed</span>
        </div>
        <div className="grid grid-cols-3 gap-3">
          <Metric label="Sesi" value={modelA.total_sessions} />
          <Metric label="Segmen valid" value={formatNumber(modelA.total_valid_segments)} />
          <Metric label="Hotspot" value={modelA.total_hotspots} />
        </div>
        <p className="mt-4 text-xs leading-relaxed text-teal-800">{modelA.comparability}</p>
      </Card>

      <Card className="border border-blue-100 bg-gradient-to-br from-white to-blue-50/70">
        <div className="mb-5 flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="rounded-xl bg-blue-100 p-2 text-blue-700"><Activity size={20} /></div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-blue-700">Model B · Wear</p>
              <h3 className="font-bold text-slate-800">Konteks perjalanan terakhir</h3>
            </div>
          </div>
          <span className="rounded-full bg-white px-2.5 py-1 text-xs font-bold text-blue-700 shadow-sm">Rule-based</span>
        </div>
        {latestWear ? (
          <>
            <div className="grid grid-cols-3 gap-3">
              <Metric label="Context score" value={formatNumber(latestWear.mean_context_score, 1)} />
              <Metric label="Roughness" value={formatNumber(latestWear.mean_roughness_score, 1)} />
              <Metric label="Servis tersisa" value={`${formatNumber(latestWear.estimated_remaining_km)} km`} />
            </div>
            <p className="mt-4 flex items-center gap-2 text-xs text-blue-800"><Route size={14} /> Sesi {latestWear.session_id} · {latestWear.segments} segmen dianalisis</p>
          </>
        ) : (
          <p className="text-sm text-slate-500">Belum ada output Model B rule-based.</p>
        )}
      </Card>
    </section>
  );
}

function Metric({ label, value }) {
  return (
    <div className="rounded-xl bg-white/80 px-3 py-3">
      <p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p>
      <p className="mt-1 text-lg font-extrabold text-slate-800">{value}</p>
    </div>
  );
}
