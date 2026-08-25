import { Info, ArrowRight, Star } from 'lucide-react';
import Card from '../ui/Card';

export default function RouteComparison() {
  return (
    <aside className="flex flex-col h-full">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-1 h-6 bg-blue-600 rounded-full"></div>
        <h2 className="text-lg font-semibold text-slate-800">Komparasi Rute</h2>
      </div>

      {/* Rute Utama (Aktif) */}
      <Card className="mb-4 border-2 border-blue-600 shadow-md relative overflow-hidden">
        <div className="absolute top-4 right-4 bg-blue-600 text-white text-[9px] font-bold px-2 py-1 rounded-md flex items-center gap-1">
          <Star size={10} fill="currentColor" /> REKOMENDASI
        </div>
        <h3 className="text-lg font-bold text-slate-800 mb-1">Rute Utama</h3>
        <p className="text-xs text-slate-500 mb-5">Via Tol Trans Jawa (Cipali - Kalikangkung)</p>

        <div className="grid grid-cols-2 gap-4 mb-5">
          <div>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Waktu Tempuh</p>
            <p className="text-2xl font-light text-slate-800">6<span className="text-sm font-semibold ml-0.5">j</span> 45<span className="text-sm font-semibold ml-0.5">m</span></p>
          </div>
          <div>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Jarak</p>
            <p className="text-2xl font-light text-slate-800">425<span className="text-sm font-semibold ml-0.5">km</span></p>
          </div>
        </div>

        <div>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-2 flex items-center gap-1">
            Skor Keausan <Info size={12} />
          </p>
          <div className="flex items-center gap-3 text-teal-700 font-semibold">
            <div className="w-8 h-8 rounded-full border-2 border-teal-700 flex items-center justify-center font-bold">A</div>
            Rendah
          </div>
        </div>
      </Card>

      {/* Rute Alternatif (Inaktif) */}
      <Card className="mb-6 bg-slate-50/50 border-transparent shadow-none">
        <h3 className="text-lg font-semibold text-slate-600 mb-1">Rute Alternatif</h3>
        <p className="text-xs text-slate-400 mb-5">Via Pantura (Arteri Nasional)</p>

        <div className="grid grid-cols-2 gap-4 mb-5">
          <div>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Waktu Tempuh</p>
            <p className="text-2xl font-light text-slate-500">10<span className="text-sm font-semibold ml-0.5">j</span> 15<span className="text-sm font-semibold ml-0.5">m</span></p>
          </div>
          <div>
            <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-1">Jarak</p>
            <p className="text-2xl font-light text-slate-500">418<span className="text-sm font-semibold ml-0.5">km</span></p>
          </div>
        </div>

        <div>
          <p className="text-[10px] text-slate-400 font-bold uppercase tracking-widest mb-2">Skor Keausan</p>
          <div className="flex items-center gap-3 text-red-500 font-semibold">
            <div className="w-8 h-8 rounded-full bg-red-100 flex items-center justify-center font-bold">C</div>
            Tinggi
          </div>
        </div>
      </Card>

      {/* Kesimpulan AI & CTA */}
      <Card className="mt-auto bg-white border border-slate-100">
        <p className="font-semibold text-slate-800 text-sm mb-2">Kesimpulan: Rute Tol lebih efisien secara holistik.</p>
        <p className="text-xs text-slate-500 leading-relaxed mb-6">
          Penghematan waktu 3.5 jam dan penurunan risiko keausan aset (nilai depresiasi ban & suspensi est. Rp 1.2M) menjadikan Rute Utama pilihan paling ekonomis.
        </p>
        <button className="w-full bg-blue-700 hover:bg-blue-800 text-white text-sm font-semibold py-3.5 rounded-xl flex items-center justify-center gap-2 transition-colors">
          Mulai Perjalanan <ArrowRight size={16} />
        </button>
      </Card>
    </aside>
  );
}