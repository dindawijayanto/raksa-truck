import { CheckCircle2, ShieldCheck } from 'lucide-react';
import Card from '../ui/Card';

export default function HealthSidebar() {
  const checklists = [
    'Beban Stabil',
    'Getaran Normal',
    'Kondisi Jalan Baik'
  ];

  return (
    <Card className="flex flex-col h-full bg-white">
      <div className="text-center mb-6">
        <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-6">Skor Kesehatan</p>
        
        {/* Lingkaran Skor */}
        <div className="relative w-40 h-40 mx-auto flex items-center justify-center rounded-full border-[12px] border-slate-100 mb-6">
          <div className="absolute inset-0 rounded-full border-[12px] border-teal-700" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 82%, 0 82%)' }}></div>
          <div className="text-center z-10 flex flex-col items-center">
            <span className="text-5xl font-extrabold text-slate-800 leading-none">82</span>
            <span className="text-[10px] text-slate-400 font-bold mt-1">/ 100</span>
          </div>
        </div>

        <div className="flex items-center justify-center gap-2 mb-2">
          <ShieldCheck size={20} className="text-teal-700" />
          <h3 className="text-lg font-bold text-teal-700">Sangat Baik</h3>
        </div>
        <p className="text-xs text-slate-500 px-4 leading-relaxed">
          Kendaraan dalam kondisi baik dan aman digunakan untuk perjalanan hari ini.
        </p>
      </div>

      <div className="mt-auto pt-6 border-t border-slate-100 flex flex-col gap-3">
        {checklists.map((item, idx) => (
          <div key={idx} className="flex justify-between items-center text-sm font-medium text-slate-700">
            {item}
            <CheckCircle2 size={16} className="text-teal-600" />
          </div>
        ))}
      </div>
    </Card>
  );
}