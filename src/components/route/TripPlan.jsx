import React, { useState } from 'react';
import { CircleDot, MapPin, ArrowRightLeft, Activity } from 'lucide-react';
import Card from '../ui/Card';

export default function TripPlan() {
  // State untuk menyimpan nilai input yang bisa diedit
  const [origin, setOrigin] = useState('Pabrik Utama Cikarang, Jawa Barat');
  const [destination, setDestination] = useState('Gudang Distribusi Semarang, Jawa Tengah');

  // Fungsi interaktif untuk menukar lokasi asal dan tujuan
  const handleSwap = () => {
    setOrigin(destination);
    setDestination(origin);
  };

  return (
    <div className="mb-6">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-xs font-bold text-slate-400 uppercase tracking-widest">Rencana Perjalanan Aktif</h2>
        <div className="flex items-center gap-2 bg-slate-100/80 text-slate-600 px-3 py-1.5 rounded-full text-xs font-semibold">
          <Activity size={14} className="text-teal-600" /> Data Real-time
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center gap-4">
        
        {/* Input Asal */}
        <Card className="flex-1 w-full bg-slate-50/50 flex items-start gap-4 p-5 focus-within:ring-2 focus-within:ring-blue-100 transition-all cursor-text">
          <div className="bg-white p-2 rounded-full shadow-sm border border-slate-100 mt-1 shrink-0">
            <CircleDot size={20} className="text-slate-800" strokeWidth={3} />
          </div>
          <div className="w-full">
            <label htmlFor="input-asal" className="text-sm text-slate-500 mb-1 block cursor-text">Asal</label>
            <input 
              id="input-asal"
              type="text" 
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              placeholder="Masukkan titik keberangkatan..."
              className="w-full font-semibold text-slate-800 bg-transparent border-none outline-none focus:ring-0 p-0 placeholder-slate-400 truncate"
            />
          </div>
        </Card>

        {/* Tombol Swap (Tukar Rute) */}
        <button 
          onClick={handleSwap}
          className="bg-slate-50 hover:bg-slate-100 p-3 rounded-full text-blue-600 shadow-sm border border-slate-100 z-10 -mx-8 md:mx-0 transition-colors cursor-pointer group"
          aria-label="Tukar rute asal dan tujuan"
        >
          <ArrowRightLeft size={20} className="group-hover:scale-110 transition-transform" />
        </button>

        {/* Input Tujuan */}
        <Card className="flex-1 w-full bg-slate-50/50 flex items-start gap-4 p-5 focus-within:ring-2 focus-within:ring-blue-100 transition-all cursor-text">
          <div className="bg-white p-2 rounded-full shadow-sm border border-slate-100 mt-1 shrink-0">
            <MapPin size={20} className="text-blue-600" fill="currentColor" strokeWidth={1} />
          </div>
          <div className="w-full">
            <label htmlFor="input-tujuan" className="text-sm text-slate-500 mb-1 block cursor-text">Tujuan</label>
            <input 
              id="input-tujuan"
              type="text" 
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              placeholder="Masukkan titik tujuan..."
              className="w-full font-semibold text-slate-800 bg-transparent border-none outline-none focus:ring-0 p-0 placeholder-slate-400 truncate"
            />
          </div>
        </Card>
        
      </div>
    </div>
  );
}