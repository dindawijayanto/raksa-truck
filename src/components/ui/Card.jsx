export default function Card({ children, className = '' }) {
  return (
    <div className={`bg-white rounded-[24px] p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] border border-slate-100 ${className}`}>
      {children}
    </div>
  );
}