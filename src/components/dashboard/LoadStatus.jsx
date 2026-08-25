import { Check } from 'lucide-react';
import Card from '../ui/Card';

export default function LoadStatus() {
  return (
    <Card className="flex flex-col h-full">
      <h3 className="text-xl font-bold text-slate-800 mb-6">Load status</h3>
      
      <div className="flex flex-col md:flex-row items-center gap-8 mb-8">
        {/* Circular Progress Representation */}
        <div className="relative w-40 h-40 flex items-center justify-center rounded-full border-[14px] border-slate-100">
          <div className="absolute inset-0 rounded-full border-[14px] border-green-500" style={{ clipPath: 'polygon(0 0, 100% 0, 100% 75%, 0 75%)' }}></div>
          <div className="text-center z-10">
            <span className="text-3xl font-extrabold text-slate-800 block">75%</span>
            <span className="text-[10px] text-slate-400 font-medium block">of legal limit</span>
            <span className="text-xs font-bold text-green-500">Safe load</span>
          </div>
        </div>

        {/* Truck Image Placeholder */}
        <div className="w-full md:w-1/2 h-32 bg-slate-200 rounded-xl overflow-hidden">
          {/* Ganti src dengan asset gambar truk Anda */}
          <img src="/api/placeholder/400/200" alt="Truck on highway" className="w-full h-full object-cover" />
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <div>
          <p className="text-sm text-slate-400 mb-1">Current load</p>
          <p className="text-2xl font-bold text-slate-800">6.8 ton</p>
        </div>
        <div>
          <p className="text-sm text-slate-400 mb-1">Legal limit</p>
          <p className="text-2xl font-bold text-slate-800">9.0 ton</p>
        </div>
      </div>

      <div className="mt-auto bg-green-50/80 rounded-xl p-4 flex items-start gap-4 border border-green-100">
        <div className="bg-white p-1 rounded-full shadow-sm mt-1">
          <Check size={16} className="text-green-500" />
        </div>
        <div>
          <p className="font-semibold text-green-700 text-sm">You're within the safe load range.</p>
          <p className="text-sm text-green-600/70">Keep it up!</p>
        </div>
      </div>
    </Card>
  );
}