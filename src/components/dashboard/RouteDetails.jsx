import { Clock, Map, ShieldAlert, CheckCircle2, Bot, ChevronRight } from 'lucide-react';
import Card from '../ui/Card';

export default function RouteDetails() {
  return (
    <Card className="flex flex-col h-full">
      <h3 className="text-xl font-bold text-slate-800 mb-6">Today's route</h3>
      
      <div className="flex flex-col lg:flex-row gap-8 mb-6">
        <div className="flex flex-col gap-6 lg:w-1/3">
          <div className="flex gap-3">
            <div className="bg-blue-50 p-2.5 rounded-full text-blue-600 h-fit"><Clock size={20} /></div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Est. Time</p>
              <p className="text-lg font-bold text-slate-800">11h 20m</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="bg-blue-50 p-2.5 rounded-full text-blue-600 h-fit"><Map size={20} /></div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Distance</p>
              <p className="text-lg font-bold text-slate-800">780 km</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="bg-blue-50 p-2.5 rounded-full text-blue-600 h-fit"><ShieldAlert size={20} /></div>
            <div>
              <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-1">Wear Score</p>
              <p className="text-lg font-bold text-slate-800">32 / 100 <span className="text-sm text-green-500 font-semibold ml-1">Low</span></p>
            </div>
          </div>
        </div>

        {/* Visualisasi Rute Map */}
        <div className="lg:w-2/3 bg-slate-50 rounded-2xl p-6 relative">
           {/* Simulasi Progress Bar Rute */}
           <div className="relative h-2 bg-gradient-to-r from-blue-500 via-green-400 to-orange-500 rounded-full mt-10">
              <div className="absolute -top-6 left-0 text-xs font-bold text-blue-600">Jakarta</div>
              <div className="absolute -top-3 left-0 w-4 h-4 bg-blue-600 rounded-full border-2 border-white transform -translate-y-1/2"></div>
              
              <div className="absolute -top-6 left-1/3 text-[10px] font-medium text-slate-400 transform -translate-x-1/2">Cirebon</div>
              
              <div className="absolute -top-6 left-2/3 text-[10px] font-medium text-slate-400 transform -translate-x-1/2">Semarang</div>
              
              <div className="absolute -bottom-6 right-0 text-xs font-bold text-orange-500">Surabaya</div>
              <div className="absolute top-1/2 right-0 w-4 h-4 bg-orange-500 rounded-full border-2 border-white transform -translate-y-1/2 translate-x-1/2 shadow-sm"></div>
           </div>
        </div>
      </div>

      <div className="border-l-4 border-blue-600 bg-slate-50/50 p-4 rounded-r-xl mb-4 flex items-center justify-between">
        <div className="flex gap-3 items-start">
          <CheckCircle2 className="text-blue-600 mt-0.5" size={20} />
          <p className="text-sm text-slate-700 font-medium leading-relaxed">
            Chosen because it reduces<br/>vehicle wear by <span className="text-blue-600 font-bold">38%</span>
          </p>
        </div>
        <div className="flex gap-3 text-xs font-medium text-slate-500">
           <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-green-500"></span> Smooth</span>
           <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-orange-400"></span> Moderate</span>
           <span className="flex items-center gap-1"><span className="w-2 h-2 rounded-full bg-red-500"></span> Critical</span>
        </div>
      </div>

      <button className="w-full mt-auto bg-slate-50 hover:bg-slate-100 border border-slate-100 rounded-xl p-4 flex items-center justify-between transition-colors group">
        <div className="flex items-center gap-4">
          <div className="p-2 bg-blue-100 rounded-full text-blue-600"><Bot size={18} /></div>
          <div className="text-left">
            <p className="text-sm font-bold text-blue-600">AI recommends this route</p>
            <p className="text-xs text-slate-400">32% lower wear score compared to alternative route.</p>
          </div>
        </div>
        <ChevronRight className="text-slate-400 group-hover:text-blue-600 transition-colors" size={20} />
      </button>
    </Card>
  );
}