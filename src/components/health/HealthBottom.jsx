import { CheckCircle2, AlertTriangle } from 'lucide-react';
import Card from '../ui/Card';

export default function HealthBottom() {
  const actions = [
    { type: 'success', text: 'Kendaraan aman digunakan.' },
    { type: 'success', text: 'Muatan berada dalam batas legal.' },
    { type: 'warning', text: 'Pemeriksaan suspensi disarankan dalam sekitar 520 km.' },
    { type: 'warning', text: 'Hindari rute dengan tingkat getaran tinggi untuk memperpanjang umur kendaraan.' },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-6">
      
      {/* Kolom Kiri: Tindakan yang Disarankan */}
      <Card>
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-4">Tindakan yang Disarankan</h3>
        <div className="flex flex-col gap-3">
          {actions.map((action, idx) => (
            <div 
              key={idx} 
              className={`flex items-start gap-3 p-4 rounded-xl ${
                action.type === 'success' ? 'bg-slate-50/80 text-slate-700' : 'bg-amber-50/50 text-amber-900'
              }`}
            >
              {action.type === 'success' ? (
                <CheckCircle2 size={18} className="text-teal-700 shrink-0 mt-0.5" />
              ) : (
                <AlertTriangle size={18} className="text-amber-500 shrink-0 mt-0.5" />
              )}
              <p className="text-sm font-medium">{action.text}</p>
            </div>
          ))}
        </div>
      </Card>

      {/* Kolom Kanan: Perubahan Kondisi (Chart) */}
      <Card className="flex flex-col">
        <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Perubahan Kondisi Kendaraan</h3>
        <p className="text-[10px] text-slate-500 mb-6">Semakin stabil grafik, semakin konsisten kondisi kendaraan. (30 Hari)</p>
        
        {/* Area ini idealnya diisi chart JS, kita mockup SVG sbg UI */}
        <div className="relative mt-auto h-32 w-full flex items-end">
          <svg className="w-full h-full drop-shadow-md" viewBox="0 0 400 100" preserveAspectRatio="none">
            {/* Gradient bawah grafik */}
            <defs>
              <linearGradient id="gradient" x1="0" x2="0" y1="0" y2="1">
                <stop offset="0%" stopColor="#2563eb" stopOpacity="0.2"/>
                <stop offset="100%" stopColor="#2563eb" stopOpacity="0"/>
              </linearGradient>
            </defs>
            <path d="M0,80 C50,80 80,90 120,90 C180,90 200,60 250,50 C300,40 330,30 400,30 L400,100 L0,100 Z" fill="url(#gradient)" />
            {/* Garis Chart */}
            <path d="M0,80 C50,80 80,90 120,90 C180,90 200,60 250,50 C300,40 330,30 400,30" fill="none" stroke="#2563eb" strokeWidth="4" strokeLinecap="round" />
          </svg>
          {/* Titik Akhir */}
          <div className="absolute right-0 top-[20%] w-5 h-5 bg-blue-100 rounded-full flex items-center justify-center translate-x-2 -translate-y-2">
             <div className="w-2.5 h-2.5 bg-blue-600 rounded-full"></div>
          </div>
        </div>
      </Card>

    </div>
  );
}