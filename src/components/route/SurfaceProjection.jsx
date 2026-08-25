export default function SurfaceProjection() {
  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h3 className="font-semibold text-slate-800">Proyeksi Kondisi Permukaan Sepanjang Rute</h3>
        <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">Total 425 KM</span>
      </div>
      
      {/* Segmented Progress Bar */}
      <div className="h-4 w-full rounded-full flex overflow-hidden mb-2">
        <div className="bg-teal-400" style={{ width: '40%' }}></div>
        <div className="bg-amber-300" style={{ width: '15%' }}></div>
        <div className="bg-teal-400" style={{ width: '30%' }}></div>
        <div className="bg-red-200" style={{ width: '5%' }}></div>
        <div className="bg-teal-400" style={{ width: '10%' }}></div>
      </div>

      <div className="flex justify-between text-[10px] font-medium text-slate-400">
        <span>Titik Awal (0h)</span>
        <span>Rest Area KM 207 (3h 15m)</span>
        <span>Tujuan (6h 45m)</span>
      </div>
    </div>
  );
}