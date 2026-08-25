import Header from '../components/layout/Header';
import HealthSidebar from '../components/health/HealthSidebar';
import HealthDetails from '../components/health/HealthDetails';
import HealthBottom from '../components/health/HealthBottom';

export default function Kesehatan() {
  return (
    <div className="min-h-screen bg-slate-50 font-sans pb-12">
      <div className="max-w-[1400px] mx-auto px-4 sm:px-6 lg:px-8">
        
        <Header />
        
        <main className="mt-8">
          <div className="mb-8">
            <h1 className="text-3xl font-extrabold text-slate-900 mb-2">Kesehatan Kendaraan</h1>
            <p className="text-slate-500 text-sm max-w-xl">
              AI menganalisis kondisi kendaraan berdasarkan beban, pola getaran, kualitas jalan, dan riwayat perjalanan.
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
            {/* Sidebar Kiri (Ambil 4 Kolom) */}
            <aside className="lg:col-span-4">
              <HealthSidebar />
            </aside>

            {/* Konten Kanan (Ambil 8 Kolom) */}
            <section className="lg:col-span-8">
              <HealthDetails />
            </section>
          </div>

          {/* Bagian Bawah */}
          <HealthBottom />

        </main>
      </div>
    </div>
  );
}