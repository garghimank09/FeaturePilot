export default function SchemaTable({ schema }) {
  const columns = schema?.columns ?? [];

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-600 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-600">
        <h3 className="text-lg font-semibold text-slate-100">Schema Summary</h3>
        <p className="text-sm text-slate-400 mt-0.5">Detected column types and sample values</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead>
            <tr className="bg-surface-700/80 text-slate-300 text-sm">
              <th className="px-4 py-3 font-medium">Column</th>
              <th className="px-4 py-3 font-medium">Type</th>
              <th className="px-4 py-3 font-medium">Unique count</th>
              <th className="px-4 py-3 font-medium">Sample values</th>
            </tr>
          </thead>
          <tbody>
            {columns.map((col) => (
              <tr
                key={col.column}
                className="border-t border-surface-600 hover:bg-surface-700/50 transition-colors"
              >
                <td className="px-4 py-3 font-mono text-accent-primary">{col.column}</td>
                <td className="px-4 py-3">
                  <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-sky-500/20 text-sky-300">
                    {col.dtype}
                  </span>
                </td>
                <td className="px-4 py-3 text-slate-300">{col.unique_count ?? '—'}</td>
                <td className="px-4 py-3 text-slate-400 text-sm max-w-xs truncate">
                  {col.sample_values?.length
                    ? col.sample_values.slice(0, 3).join(', ')
                    : '—'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
