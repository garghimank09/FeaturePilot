export default function SummaryCards({ data }) {
  const totalRows = data?.total_rows ?? 0;
  const totalColumns = data?.total_columns ?? 0;
  const duplicatesRemoved = data?.duplicates_removed ?? 0;
  const totalMissing = data?.missing_summary?.total_missing ?? 0;
  const numericCount = Object.keys(data?.stats_summary?.numeric ?? {}).length;
  const categoricalCount = Object.keys(data?.stats_summary?.categorical ?? {}).length;

  const cards = [
    { label: 'Total Rows', value: totalRows.toLocaleString(), sub: 'after cleaning' },
    { label: 'Columns', value: totalColumns, sub: `${numericCount} numeric, ${categoricalCount} categorical` },
    { label: 'Duplicates Removed', value: duplicatesRemoved.toLocaleString(), sub: 'rows' },
    { label: 'Missing Values Filled', value: totalMissing.toLocaleString(), sub: 'median / mode' },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {cards.map((card) => (
        <div
          key={card.label}
          className="rounded-xl bg-surface-800 border border-surface-600 p-4 hover:border-surface-500 transition-colors"
        >
          <p className="text-sm text-slate-400 font-medium">{card.label}</p>
          <p className="text-2xl font-bold text-slate-100 mt-1">{card.value}</p>
          <p className="text-xs text-slate-500 mt-0.5">{card.sub}</p>
        </div>
      ))}
    </div>
  );
}
