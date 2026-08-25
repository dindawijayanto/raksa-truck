import { Sparkles, Map, Activity, Settings, Circle, CheckCircle2, TrendingUp } from 'lucide-react';
import Card from '../ui/Card';

export default function HealthDetails() {
  return (
    <div className="flex flex-col gap-6">
      
      {/* 1. AI Analysis Summary */}
      <Card className="border-l-[6px] border-l-amber-400 bg-white">
        <div className="flex gap-4 items-start">
          <div className="bg-amber-50 p-2 rounded-full text-amber-500 shrink-0">
            <Sparkles size={20} />
          </div>
          <div>
            <h3 className="text-lg font-bold text-slate-800 mb-2">Analisis</h3>
            <p className="text-sm text-slate-600 leading-relaxed">
              Selama tiga perjalanan terakhir, kendaraan mengalami tingkat getaran yang masih berada dalam batas normal. Tidak ditemukan indikasi keausan yang meningkat secara signifikan. Kendaraan diperkirakan masih aman digunakan sebelum pemeriksaan berikutnya.
            </p>
          </div>
        </div>
      </Card>

      {/* 2. 4 Mini Metrics Grid */}
      <div className="grid grid-cols-2 gap-4">
        {/* Muatan */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Muatan</span>
            <span className="text-[9px] bg-green-50 text-teal-700 px-2 py-0.5 rounded-full font-bold">Normal</span>
          </div>
          <p className="text-2xl font-bold text-slate-800 mb-3">6.850 kg</p>
          <div className="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
            <div className="h-full bg-blue-700 w-[75%] rounded-full"></div>
          </div>
        </Card>

        {/* Kondisi Jalan */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Kondisi Jalan</span>
            <Map size={14} className="text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mb-3">Baik</p>
          <div className="flex gap-1 items-end h-3">
            {[20, 30, 20, 40, 100, 80, 40, 20].map((h, i) => (
              <div key={i} className={`flex-1 rounded-sm ${h > 70 ? 'bg-teal-800' : h > 30 ? 'bg-teal-500/50' : 'bg-teal-200/50'}`} style={{ height: `${h}%` }}></div>
            ))}
          </div>
        </Card>

        {/* Tingkat Getaran */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Tingkat Getaran</span>
            <Activity size={14} className="text-slate-400" />
          </div>
          <p className="text-2xl font-bold text-slate-800 mb-3">Normal</p>
          <svg className="w-full h-4 text-blue-600" viewBox="0 0 100 20" preserveAspectRatio="none">
            <path d="M0,10 Q10,0 20,10 T40,10 T60,10 T80,10 T100,10" fill="none" stroke="currentColor" strokeWidth="2" />
          </svg>
        </Card>

        {/* Estimasi Keausan */}
        <Card className="p-5 flex flex-col justify-between">
          <div className="flex justify-between items-center mb-4">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Estimasi Tingkat Keausan</span>
            <Settings size={14} className="text-slate-400" />
          </div>
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full border-2 border-teal-700 text-teal-700 flex items-center justify-center font-bold text-lg">A</div>
            <p className="text-3xl font-bold text-slate-800">28<span className="text-sm font-normal text-slate-500 ml-1">%</span></p>
          </div>
        </Card>
      </div>

      {/* 3. Bottom 2 Cards (Impact & Service) */}
      <div className="grid grid-cols-2 gap-4">
        <Card className="p-5">
          <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4 block">Dampak Perjalanan Terakhir</span>
          <div className="flex flex-col gap-4 text-sm font-medium text-slate-700">
            <div className="flex items-center gap-3"><Circle size={16} className="text-blue-600" /> Perjalanan Terakhir</div>
            <div className="flex items-center gap-3"><div className="bg-blue-50 p-1 rounded text-blue-600"><CheckCircle2 size={12}/></div> Muatan (82%)</div>
            <div className="flex items-center gap-3"><div className="bg-amber-50 p-1 rounded text-amber-500"><Map size={12}/></div> Jalan Sedang</div>
            <div className="flex items-center gap-3"><div className="bg-teal-50 p-1 rounded text-teal-600"><TrendingUp size={12}/></div> Wear +2</div>
          </div>
        </Card>

        <Card className="p-5 flex flex-col justify-between relative overflow-hidden">
          <div>
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-2 block">Prediksi Servis</span>
            <p className="text-[10px] text-slate-500 leading-tight mb-4">Estimasi dibuat berdasarkan pola penggunaan kendaraan, kualitas jalan, dan beban selama perjalanan.</p>
            <p className="text-4xl font-bold text-slate-800">520 <span className="text-sm font-normal text-slate-500">km</span></p>
            <p className="text-xs font-bold text-blue-600 mt-1">Estimasi: 12 Agustus 2026</p>
          </div>
          
          {/* Visual Timeline */}
          <div className="flex justify-between items-center mt-6 relative z-10">
             <div className="h-0.5 bg-slate-200 absolute left-2 right-2 top-2 -z-10"></div>
             <div className="flex flex-col items-center gap-1"><span className="w-4 h-4 rounded-full bg-slate-300 border-2 border-white"></span><span className="text-[9px] font-bold text-slate-400">Today</span></div>
             <div className="flex flex-col items-center gap-1"><span className="w-4 h-4 rounded-full bg-teal-700 border-2 border-white shadow-sm"></span><span className="text-[9px] font-bold text-teal-700">Current</span></div>
             <div className="flex flex-col items-center gap-1"><span className="w-4 h-4 rounded-full bg-amber-400 border-2 border-white shadow-sm"></span><span className="text-[9px] font-bold text-amber-500">Inspect</span></div>
             <div className="flex flex-col items-center gap-1"><span className="w-4 h-4 rounded-full bg-white border-2 border-slate-300"></span><span className="text-[9px] font-bold text-slate-400">Service</span></div>
          </div>
          
          {/* Decorative faint circle at bottom right */}
          <div className="absolute -bottom-4 -right-4 w-24 h-24 border-[8px] border-slate-50 rounded-full z-0 pointer-events-none"></div>
        </Card>
      </div>

    </div>
  );
}