import { LayoutGrid, Route as RouteIcon, Activity, Settings } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import logo from '../../assets/logo.png'; 

export default function Header() {
  const getNavClass = ({ isActive }) => {
    const baseClass = "flex items-center gap-2 px-5 py-2.5 rounded-full text-sm transition-all";
    const activeClass = "bg-white text-blue-600 shadow-sm font-semibold";
    const inactiveClass = "text-slate-500 hover:text-slate-800 font-medium";
    
    return `${baseClass} ${isActive ? activeClass : inactiveClass}`;
  };

  return (
    <header className="flex flex-col md:flex-row items-center justify-between py-4 gap-4">
      
      {/* Bagian Logo yang diperbarui */}
      <div className="flex-shrink-0">
        <img 
          src={logo} 
          alt="Truk Logo" 
          className="h-10 w-auto object-contain drop-shadow-sm" 
        />
      </div>
      
      {/* Navigation Pills */}
      <nav className="flex items-center bg-slate-100/80 p-1.5 rounded-full" aria-label="Main Navigation">
        <NavLink to="/" className={getNavClass}>
          <LayoutGrid size={18} /> Dashboard
        </NavLink>
        
        <NavLink to="/rute" className={getNavClass}>
          <RouteIcon size={18} /> Rute
        </NavLink>
        
        <NavLink to="/kesehatan" className={getNavClass}>
          <Activity size={18} /> Kesehatan
        </NavLink>
        
        <NavLink to="/pengaturan" className={getNavClass}>
          <Settings size={18} /> Pengaturan
        </NavLink>
      </nav>

      {/* IoT Status */}
      <div className="flex items-center gap-2 bg-green-50/80 border border-green-100 px-4 py-2 rounded-full hidden sm:flex">
        <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></span>
        <span className="text-sm font-medium text-green-700">IoT Online</span>
      </div>
    </header>
  );
}