import { BrainCircuit, TrendingDown, ShieldCheck, Cog, Activity } from 'lucide-react';
import Card from '../ui/Card';

export default function MapVisualization() {
  return (
    <div className="relative w-full h-[450px] bg-slate-200 rounded-[32px] overflow-hidden mb-6 shadow-inner border border-slate-200">
      
      {/* 
        AREA UNTUK AI ENGINEER 
        Beritahu engineer Anda untuk me-render map/canvas di dalam div ber-id "map-container" ini.
      */}
      <div id="map-container" className="absolute inset-0 bg-slate-300 mix-blend-multiply opacity-50">
        {/* Bisa diisi background image sementara jika mau, atau dibiarkan kosong untuk diisi oleh map library */}
      </div>

      {/* Floating Legend (Top Right) */}
      <Card className="absolute top-6 right-6 p-4 shadow-lg min-w-[200px]">
        <h4 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-3">Indeks Kekasaran Jalan</h4>
        <div className="flex flex-col gap-2 text-sm font-semibold text-slate-700">
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-teal-700"></span> Smooth</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-amber-600"></span> Moderate</div>
          <div className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-600"></span> Critical</div>
        </div>
      </Card>

      {/* Floating AI Card (Bottom Left) */}
      <Card className="absolute bottom-6 left-6 p-5 shadow-xl w-[90%] md:w-auto md:min-w-[340px]">
        <div className="flex items-center gap-3 mb-4">
          <div className="bg-blue-600 text-white p-2 rounded-full">
            <BrainCircuit size={20} />
          </div>
          <h3 className="font-bold text-slate-900">Mengapa AI memilih rute ini?</h3>
        </div>

        <div className="grid grid-cols-2 gap-y-4 gap-x-6">
          <div>
            <div className="flex items-center gap-1 text-teal-600 mb-1">
              <TrendingDown size={14} strokeWidth={3} />
              <span className="text-xl font-bold">-38%</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">Proyeksi Keausan<br/>Ban & Suspensi</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-blue-600 mb-1">
              <Cog size={14} strokeWidth={3} />
              <span className="text-xl font-bold">82%</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">Rasio Jalan<br/>Kategori Mulus</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-amber-600 mb-1">
              <ShieldCheck size={14} strokeWidth={3} />
              <span className="text-xl font-bold text-amber-700">Rendah</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">Risiko Kerusakan<br/>Muatan</p>
          </div>
          <div>
            <div className="flex items-center gap-1 text-teal-600 mb-1">
              <Activity size={14} strokeWidth={3} />
              <span className="text-xl font-bold">Opt</span>
            </div>
            <p className="text-[10px] text-slate-500 leading-tight">Rasio Biaya Operasional<br/>vs Waktu</p>
          </div>
        </div>
      </Card>

    </div>
  );
}