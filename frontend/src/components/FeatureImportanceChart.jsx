import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

const chartOptions = {
  indexAxis: 'y',
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { display: false },
    title: { display: false },
  },
  scales: {
    x: {
      grid: { color: 'rgba(148, 163, 184, 0.15)' },
      ticks: { color: '#94a3b8' },
    },
    y: {
      grid: { display: false },
      ticks: { color: '#94a3b8', font: { size: 11 } },
    },
  },
};

export default function FeatureImportanceChart({ featureImportance }) {
  const entries = Object.entries(featureImportance || {}).sort((a, b) => b[1] - a[1]).slice(0, 25);
  if (entries.length === 0) {
    return (
      <div className="rounded-xl bg-surface-800 border border-surface-600 p-6 text-center text-slate-400">
        No feature importance (run with feature selection enabled).
      </div>
    );
  }

  const labels = entries.map(([name]) => name.length > 30 ? name.slice(0, 27) + '...' : name);
  const values = entries.map(([, v]) => v);

  const data = {
    labels,
    datasets: [
      {
        label: 'Importance',
        data: values,
        backgroundColor: 'rgba(14, 165, 233, 0.7)',
        borderColor: 'rgb(14, 165, 233)',
        borderWidth: 1,
      },
    ],
  };

  return (
    <div className="rounded-xl bg-surface-800 border border-surface-600 overflow-hidden">
      <div className="px-4 py-3 border-b border-surface-600">
        <h3 className="text-lg font-semibold text-slate-100">Feature importance</h3>
        <p className="text-sm text-slate-400 mt-0.5">Random Forest importance (top 25)</p>
      </div>
      <div className="p-4 h-[400px]">
        <Bar data={data} options={chartOptions} />
      </div>
    </div>
  );
}
