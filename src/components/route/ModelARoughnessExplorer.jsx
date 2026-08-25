import { useEffect, useState } from 'react';
import { AlertTriangle, Gauge, LocateFixed, MapPinned } from 'lucide-react';
import Card from '../ui/Card';
import { getModelASegments, getModelASessions } from '../../lib/modelReportsApi';

const classColors = { Rendah: 'bg-emerald-400', Sedang: 'bg-amber-400', Tinggi: 'bg-rose-500' };
const classText = { Rendah: 'text-emerald-700', Sedang: 'text-amber-700', Tinggi: 'text-rose-700' };

function formatNumber(value, maximumFractionDigits = 0) {
  return new Intl.NumberFormat('id-ID', { maximumFractionDigits }).format(value);
}

export default function ModelARoughnessExplorer() {
  const [sessions, setSessions] = useState([]);
  const [selectedSessionId, setSelectedSessionId] = useState('');
  const [segmentReport, setSegmentReport] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    let isActive = true;
    getModelASessions()
      .then((response) => {
        if (!isActive) return;
        setSessions(response.sessions);
        const preferred = response.sessions.find((session) => session.vehicle === 'tt' && session.model_reliability === 'standard');
        setSelectedSessionId((preferred || response.sessions[0])?.session_id || '');
      })
      .catch((requestError) => {
        if (isActive) setError(requestError instanceof Error ? requestError.message : 'Gagal memuat sesi Model A.');
      });
    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    if (!selectedSessionId) return undefined;
    let isActive = true;
    getModelASegments(selectedSessionId)
      .then((response) => {
        if (isActive) setSegmentReport(response);
      })
      .catch((requestError) => {
        if (isActive) setError(requestError instanceof Error ? requestError.message : 'Gagal memuat segmen Model A.');
      });
    return () => {
      isActive = false;
    };
  }, [selectedSessionId]);

  const selectedSession = sessions.find((session) => session.session_id === selectedSessionId);
  return (
    <Card className="mb-6 border border-teal-100 bg-gradient-to-br from-white to-teal-50/60">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <div className="flex items-center gap-2 text-teal-700"><MapPinned size={19} /><span className="text-xs font-bold uppercase tracking-widest">Model A · Road roughness</span></div>
          <h2 className="mt-1 text-2xl font-extrabold text-slate-900">Profil kekasaran sesi sensor</h2>
          <p className="mt-2 max-w-2xl text-sm text-slate-600">Data ini adalah output sensor yang telah diproses, bukan proyeksi rute statis. Pilih sesi untuk melihat segmen 20 m dan kandidat hotspot.</p>
        </div>
        <label className="rounded-xl border border-teal-200 bg-white px-3 py-2">
          <span className="block text-[10px] font-bold uppercase tracking-wider text-slate-400">Sesi</span>
          <select className="mt-1 max-w-full bg-transparent text-sm font-bold text-slate-800 outline-none" value={selectedSessionId} onChange={(event) => setSelectedSessionId(event.target.value)}>
            {sessions.map((session) => <option key={session.session_id} value={session.session_id}>{session.session_id} · {session.vehicle}</option>)}
          </select>
        </label>
      </div>

      {error ? <div className="mt-5 flex gap-2 rounded-xl bg-rose-50 p-3 text-sm text-rose-700"><AlertTriangle size={18} /> {error}</div> : null}
      {selectedSession ? (
        <div className="mt-5 grid grid-cols-2 gap-3 sm:grid-cols-4">
          <Metric label="Segmen valid" value={formatNumber(selectedSession.valid_segments)} />
          <Metric label="Hotspot" value={selectedSession.hotspots} />
          <Metric label="Kecepatan referensi" value={`${formatNumber(selectedSession.reference_speed_kmh, 1)} km/j`} />
          <Metric label="Reliabilitas" value={selectedSession.model_reliability === 'standard' ? 'Standar' : 'Terbatas'} />
        </div>
      ) : null}

      {segmentReport ? (
        <>
          <div className="mt-5 flex h-4 overflow-hidden rounded-full bg-slate-100">
            {segmentReport.segments.map((segment) => <div key={segment.segment_id} className={classColors[segment.roughness_class]} style={{ width: `${100 / segmentReport.segments.length}%` }} title={`Segmen ${segment.segment_id}: ${segment.roughness_class}`} />)}
          </div>
          <div className="mt-2 flex justify-between text-[10px] font-bold uppercase tracking-wider text-slate-400"><span>Awal sesi</span><span>{segmentReport.segments.length} segmen yang ditampilkan</span><span>Akhir sampel</span></div>
          <div className="mt-5 grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="rounded-xl bg-white p-4">
              <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400"><Gauge size={14} /> Distribusi kelas</p>
              <div className="mt-3 flex gap-4 text-sm font-bold">
                <span className="text-emerald-700">Rendah {segmentReport.roughness_counts.rendah}</span>
                <span className="text-amber-700">Sedang {segmentReport.roughness_counts.sedang}</span>
                <span className="text-rose-700">Tinggi {segmentReport.roughness_counts.tinggi}</span>
              </div>
            </div>
            <div className="rounded-xl bg-white p-4">
              <p className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400"><LocateFixed size={14} /> Batas interpretasi</p>
              <p className="mt-2 text-xs leading-relaxed text-slate-600">{segmentReport.comparability}</p>
            </div>
          </div>
          <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-2 lg:grid-cols-3">
            {segmentReport.segments.filter((segment) => segment.hotspot_flag || segment.roughness_class === 'Tinggi').slice(0, 6).map((segment) => (
              <div key={segment.segment_id} className="flex items-center justify-between rounded-xl border border-slate-100 bg-white px-3 py-2.5">
                <div><p className="text-xs font-bold text-slate-700">Segmen {segment.segment_start_m}–{segment.segment_end_m} m</p><p className="text-[10px] text-slate-400">Skor {formatNumber(segment.relative_roughness_score, 1)} · {formatNumber(segment.mean_speed_kmh, 1)} km/j</p></div>
                <span className={`text-xs font-bold ${classText[segment.roughness_class]}`}>{segment.roughness_class}</span>
              </div>
            ))}
          </div>
        </>
      ) : <div className="mt-5 h-24 animate-pulse rounded-xl bg-white/70" />}
    </Card>
  );
}

function Metric({ label, value }) {
  return <div className="rounded-xl bg-white/80 px-3 py-3"><p className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</p><p className="mt-1 text-lg font-extrabold text-slate-800">{value}</p></div>;
}
