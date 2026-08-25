import { Calendar, Truck } from 'lucide-react';
import Card from '../ui/Card';

export default function Greeting() {
  return (
    <section className="flex flex-col lg:flex-row justify-between items-start lg:items-center py-8 gap-4">
      <div>
        <h1 className="text-4xl font-extrabold text-slate-900 mb-2">Halo, Andi</h1>
        <p className="text-slate-500 text-lg">Let's make this trip safe and efficient.</p>
      </div>
      
      <div className="flex flex-wrap gap-4 w-full lg:w-auto">
        <Card className="flex items-center gap-4 py-3 min-w-[200px]">
          <Truck className="text-blue-600" size={24} />
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Truck</p>
            <div className="flex items-center gap-2">
              <p className="font-bold text-slate-800">B 9021 TRK</p>
              <span className="w-1.5 h-1.5 rounded-full bg-green-500"></span>
            </div>
          </div>
        </Card>
        
        <Card className="flex items-center gap-4 py-3 min-w-[200px]">
          <Calendar className="text-slate-400" size={24} />
          <div>
            <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">Today</p>
            <p className="font-bold text-slate-800">1 Aug 2026</p>
          </div>
        </Card>
      </div>
    </section>
  );
}