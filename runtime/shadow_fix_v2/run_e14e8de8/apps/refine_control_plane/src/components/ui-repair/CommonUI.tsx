import React from 'react';

export const Card = ({ children, className = "", onClick }: { children: React.ReactNode, className?: string, onClick?: () => void }) => (
  <div 
    onClick={onClick}
    className={`bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden backdrop-blur-md shadow-xl ${className} ${onClick ? 'cursor-pointer transition-transform active:scale-[0.98]' : ''}`}
  >
    {children}
  </div>
);

export const CardHeader = ({ children, className = "" }: any) => (
    <div className={`p-6 border-b border-slate-800 ${className}`}>{children}</div>
);

export const CardTitle = ({ children, className = "" }: any) => (
    <h3 className={`text-lg font-bold text-white ${className}`}>{children}</h3>
);

export const CardDescription = ({ children, className = "" }: any) => (
    <p className={`text-sm text-slate-400 ${className}`}>{children}</p>
);

export const CardContent = ({ children, className = "" }: any) => (
    <div className={`p-6 ${className}`}>{children}</div>
);

export const Badge = ({ children, variant = "info", className = "" }: { children: React.ReactNode, variant?: string, className?: string }) => {
  const styles: Record<string, string> = {
    info: "bg-blue-500/10 text-blue-400 border-blue-500/20",
    success: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
    warning: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    error: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    critical: "bg-purple-500/10 text-purple-400 border-purple-500/20",
    low: "bg-slate-500/10 text-slate-400 border-slate-500/20",
    medium: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    high: "bg-rose-500/10 text-rose-400 border-rose-500/20",
    outline: "border-slate-700 text-slate-400",
  };
  return (
    <span className={`px-2 py-0.5 rounded-full text-[10px] uppercase font-bold tracking-wider border ${styles[variant.toLowerCase()] || styles.info} ${className}`}>
      {children}
    </span>
  );
};

export const Button = ({ children, onClick, disabled, className = "", variant = "primary", size = "md" }: any) => {
  const variants: any = {
    primary: "bg-blue-600 hover:bg-blue-500 text-white shadow-lg shadow-blue-500/20",
    secondary: "bg-slate-800 hover:bg-slate-700 text-slate-200",
    outline: "border border-slate-700 hover:border-slate-600 text-slate-300",
    danger: "bg-rose-600/10 text-rose-400 border border-rose-500/20 hover:bg-rose-600/20",
    ghost: "bg-transparent hover:bg-white/5 text-slate-400 hover:text-white",
  };
  
  const sizes: any = {
    xs: "px-2 py-1 text-[10px]",
    sm: "px-3 py-1.5 text-xs",
    md: "px-4 py-2 text-sm",
    lg: "px-6 py-3 text-base",
  };
  
  return (
    <button 
      onClick={onClick}
      disabled={disabled}
      className={`rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed ${variants[variant]} ${sizes[size]} ${className}`}
    >
      {children}
    </button>
  );
};

export const Table = ({ children, className = "" }: any) => (
    <div className="w-full overflow-auto">
        <table className={`w-full text-left border-collapse ${className}`}>{children}</table>
    </div>
);

export const TableHeader = ({ children, className = "" }: any) => (
    <thead className={`border-b border-slate-800 ${className}`}>{children}</thead>
);

export const TableBody = ({ children, className = "" }: any) => (
    <tbody className={`${className}`}>{children}</tbody>
);

export const TableRow = ({ children, className = "" }: any) => (
    <tr className={`border-b border-slate-800/50 hover:bg-white/5 transition-colors ${className}`}>{children}</tr>
);

export const TableHead = ({ children, className = "" }: any) => (
    <th className={`p-4 text-xs font-black text-slate-500 uppercase tracking-widest ${className}`}>{children}</th>
);

export const TableCell = ({ children, className = "" }: any) => (
    <td className={`p-4 text-sm text-slate-300 ${className}`}>{children}</td>
);
