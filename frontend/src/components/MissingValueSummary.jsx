export default function MissingValueSummary({ missing_summary }) {
  const columns = missing_summary?.columns ?? {};
  const entries = Object.entries(columns).filter(([, v]) => v?.count > 0);

  if (entries.length === 0) {
    return (
      <div className="rounded-xl bg-surface-800 border border-surface-600 p-4">
        <h3 className="text-lg font-semibold text-slate-100">Missing Values</h3>
        <p className="text-slate-400 text-sm mt-1">No missing values found. No fill applied.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-600 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-600">
        <h3 className="text-lg font-semibold text-slate-100">Missing Value Summary</h3>
        <p className="text-sm text-slate-400 mt-0.5">Count, percentage, and fill strategy per column</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-surface-700/80 text-slate-300 text-sm">
              <th className="px-4 py-3 font-medium">Column</th>
              <th className="px-4 py-3 font-medium">Missing count</th>
              <th className="px-4 py-3 font-medium">%</th>
              <th className="px-4 py-3 font-medium">Filled with</th>
            </tr>
          </thead>
          <tbody>
            {entries.map(([col, v]) => (
              <tr key={col} className="border-t border-surface-600 hover:bg-surface-700/50">
                <td className="px-4 py-3 font-mono text-accent-primary">{col}</td>
                <td className="px-4 py-3 text-slate-300">{v.count}</td>
                <td className="px-4 py-3 text-slate-300">{v.pct}%</td>
                <td className="px-4 py-3">
                  <span className="text-sky-300 text-sm">{v.filled_with}</span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
