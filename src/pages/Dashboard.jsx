import Header from '../components/layout/Header';
import Greeting from '../components/dashboard/Greeting';
import TripReadiness from '../components/dashboard/TripReadiness';
import LoadStatus from '../components/dashboard/LoadStatus';
import RouteDetails from '../components/dashboard/RouteDetails';
import { Sun, Car, DollarSign, PhoneCall } from 'lucide-react';

export default function Dashboard() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans pb-24">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        <Header />
        
        <main>
          <Greeting />
          <TripReadiness />
          
          {/* Menggunakan Grid untuk split 2 kolom pada layar besar */}
          <section className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LoadStatus />
            <RouteDetails />
          </section>
        </main>

      </div>

      {/* Floating Bottom Bar Container */}
      <div className="fixed bottom-6 left-0 right-0 px-4 flex justify-center z-50">
        <div className="bg-white shadow-xl border border-slate-100 rounded-full py-2 px-6 flex items-center divide-x divide-slate-100">
          
          <div className="flex items-center gap-3 px-6">
            <Sun className="text-orange-400" size={20} />
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Weather</p>
              <p className="text-sm font-bold text-slate-800">Cerah, 28°C</p>
            </div>
          </div>
          
          <div className="flex items-center gap-3 px-6">
            <div className="bg-blue-50 p-1.5 rounded-md"><Car className="text-blue-600" size={16} /></div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Traffic</p>
              <p className="text-sm font-bold text-slate-800">Normal</p>
            </div>
          </div>

          <div className="flex items-center gap-3 px-6">
            <div className="bg-purple-50 p-1.5 rounded-full"><DollarSign className="text-purple-600" size={16} /></div>
            <div>
              <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Potensi Penghematan</p>
              <p className="text-sm font-bold text-slate-800">Rp 245.000</p>
            </div>
          </div>

          <div className="pl-6">
            <button className="flex items-center gap-3 bg-slate-50 hover:bg-slate-100 px-4 py-2 rounded-full transition-colors">
              <div className="bg-blue-600 text-white p-1.5 rounded-full"><PhoneCall size={14} /></div>
              <div className="text-left">
                <p className="text-[10px] font-bold text-blue-600 uppercase">Need Help?</p>
                <p className="text-xs font-semibold text-slate-500">24/7 support</p>
              </div>
            </button>
          </div>

        </div>
      </div>
    </div>
  );
}