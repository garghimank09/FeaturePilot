export default function PreviewTable({ preview }) {
  const rows = Array.isArray(preview) ? preview : [];
  const columns = rows.length ? Object.keys(rows[0]) : [];

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-600 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-600">
        <h3 className="text-lg font-semibold text-slate-100">Data Preview</h3>
        <p className="text-sm text-slate-400 mt-0.5">First 20 rows of cleaned data</p>
      </div>
      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 bg-surface-700 z-10">
            <tr className="text-slate-300">
              {columns.map((col) => (
                <th key={col} className="px-4 py-2 font-medium whitespace-nowrap border-b border-surface-600">
                  {col}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row, i) => (
              <tr
                key={i}
                className="border-b border-surface-600/80 hover:bg-surface-700/50 transition-colors"
              >
                {columns.map((col) => (
                  <td key={col} className="px-4 py-2 text-slate-300 whitespace-nowrap max-w-[200px] truncate">
                    {row[col] == null ? (
                      <span className="text-slate-500">—</span>
                    ) : (
                      String(row[col])
                    )}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
