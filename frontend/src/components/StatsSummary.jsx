export default function StatsSummary({ stats_summary }) {
  const numeric = stats_summary?.numeric ?? {};
  const categorical = stats_summary?.categorical ?? {};
  const datetime = stats_summary?.datetime ?? {};
  const hasAny = Object.keys(numeric).length > 0 || Object.keys(categorical).length > 0 || Object.keys(datetime).length > 0;

  if (!hasAny) {
    return (
      <div className="rounded-xl bg-surface-800 border border-surface-600 p-4">
        <h3 className="text-lg font-semibold text-slate-100">Basic Statistics</h3>
        <p className="text-slate-400 text-sm mt-1">No numeric or categorical stats available.</p>
      </div>
    );
  }

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-600 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-600">
        <h3 className="text-lg font-semibold text-slate-100">Basic Statistics Summary</h3>
        <p className="text-sm text-slate-400 mt-0.5">Numeric (min, max, mean, median, std) and categorical (top value)</p>
      </div>
      <div className="p-4 space-y-6">
        {Object.keys(numeric).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-400 mb-2">Numeric</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400">
                    <th className="text-left py-2 pr-4">Column</th>
                    <th className="text-left py-2 pr-4">Min</th>
                    <th className="text-left py-2 pr-4">Max</th>
                    <th className="text-left py-2 pr-4">Mean</th>
                    <th className="text-left py-2 pr-4">Median</th>
                    <th className="text-left py-2 pr-4">Std</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(numeric).map(([col, s]) => (
                    <tr key={col} className="border-t border-surface-600">
                      <td className="py-2 pr-4 font-mono text-accent-primary">{col}</td>
                      <td className="py-2 pr-4 text-slate-300">{formatNum(s.min)}</td>
                      <td className="py-2 pr-4 text-slate-300">{formatNum(s.max)}</td>
                      <td className="py-2 pr-4 text-slate-300">{formatNum(s.mean)}</td>
                      <td className="py-2 pr-4 text-slate-300">{formatNum(s.median)}</td>
                      <td className="py-2 pr-4 text-slate-300">{formatNum(s.std)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {Object.keys(categorical).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-400 mb-2">Categorical</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400">
                    <th className="text-left py-2 pr-4">Column</th>
                    <th className="text-left py-2 pr-4">Unique count</th>
                    <th className="text-left py-2 pr-4">Top value</th>
                    <th className="text-left py-2 pr-4">Top count</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(categorical).map(([col, s]) => (
                    <tr key={col} className="border-t border-surface-600">
                      <td className="py-2 pr-4 font-mono text-accent-primary">{col}</td>
                      <td className="py-2 pr-4 text-slate-300">{s.unique_count}</td>
                      <td className="py-2 pr-4 text-slate-300 max-w-[200px] truncate">{String(s.top_value ?? '—')}</td>
                      <td className="py-2 pr-4 text-slate-300">{s.top_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {Object.keys(datetime).length > 0 && (
          <div>
            <h4 className="text-sm font-medium text-slate-400 mb-2">Datetime</h4>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-slate-400">
                    <th className="text-left py-2 pr-4">Column</th>
                    <th className="text-left py-2 pr-4">Min</th>
                    <th className="text-left py-2 pr-4">Max</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(datetime).map(([col, s]) => (
                    <tr key={col} className="border-t border-surface-600">
                      <td className="py-2 pr-4 font-mono text-accent-primary">{col}</td>
                      <td className="py-2 pr-4 text-slate-300">{String(s.min ?? '—')}</td>
                      <td className="py-2 pr-4 text-slate-300">{String(s.max ?? '—')}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function formatNum(n) {
  if (n == null || (typeof n === 'number' && isNaN(n))) return '—';
  if (typeof n === 'number') return Number.isInteger(n) ? n : Number(n).toFixed(4);
  return String(n);
}
