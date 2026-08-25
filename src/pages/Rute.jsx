import Header from '../components/layout/Header';
import TripPlan from '../components/route/TripPlan';
import MapVisualization from '../components/route/MapVisualization';
import SurfaceProjection from '../components/route/SurfaceProjection';
import RouteComparison from '../components/route/RouteComparison';

export default function Rute() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans pb-12">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Reuse Header (Sebaiknya modifikasi state active tab di komponen aslinya) */}
        <Header />
        
        <main className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            {/* Kolom Kiri: Peta dan Detail Perjalanan (Ambil 8 Kolom di Desktop) */}
            <section className="lg:col-span-8 flex flex-col">
              <TripPlan />
              <MapVisualization />
              <SurfaceProjection />
            </section>

            {/* Kolom Kanan: Sidebar Komparasi (Ambil 4 Kolom di Desktop) */}
            <section className="lg:col-span-4">
              <RouteComparison />
            </section>

          </div>
        </main>
      </div>
    </div>
  );
}