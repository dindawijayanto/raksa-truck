import { ShoppingBag, Map, Settings2, Activity, Check, ArrowRight } from 'lucide-react';
import Card from '../ui/Card';

export default function TripReadiness() {
  const metrics = [
    { icon: ShoppingBag, color: 'text-green-500', bg: 'bg-green-50', title: 'Load', status: 'Safe', desc: '75% of limit' },
    { icon: Map, color: 'text-blue-500', bg: 'bg-blue-50', title: 'Route', status: 'Recommended', desc: 'Best for vehicle' },
    { icon: Settings2, color: 'text-orange-500', bg: 'bg-orange-50', title: 'Service', status: 'In 520 km', desc: 'Next inspection' },
    { icon: Activity, color: 'text-green-500', bg: 'bg-green-50', title: 'Health', status: 'Good', desc: 'Wear score 82' },
  ];

  return (
    <Card className="mb-6 relative overflow-hidden">
      <div className="mb-8">
        <p className="text-slate-500 mb-1">Can I start today's trip safely?</p>
        <h2 className="text-4xl font-bold text-green-500">Yes, you're good to go!</h2>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-6 mb-8 relative z-10">
        {metrics.map((item, idx) => (
          <div key={idx} className="flex items-start gap-4">
            <div className={`p-3 rounded-full ${item.bg} ${item.color}`}>
              <item.icon size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm text-slate-400 font-medium">{item.title}</span>
                {item.title === 'Load' || item.title === 'Health' ? (
                  <span className="text-[10px] bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-bold">{item.status}</span>
                ) : null}
              </div>
              <p className="font-bold text-slate-800">{item.status}</p>
              <p className="text-xs text-slate-400">{item.desc}</p>
            </div>
          </div>
        ))}
      </div>

      {/* Decorative Check Mark - Absolute Right */}
      <div className="hidden md:flex absolute right-12 top-1/2 -translate-y-1/2 w-20 h-20 bg-green-100 rounded-full items-center justify-center">
        <Check className="text-green-500" size={40} strokeWidth={3} />
      </div>

      <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-4 rounded-xl flex items-center justify-center gap-2 transition-colors">
        Start trip <ArrowRight size={20} />
      </button>
    </Card>
  );
}