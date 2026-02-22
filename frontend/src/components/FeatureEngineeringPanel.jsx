import { useCallback, useState } from 'react';
import FeatureImportanceChart from './FeatureImportanceChart';
import PreviewTable from './PreviewTable';
import { runFeatureEngineering, downloadEngineeredCsv } from '../services/api';

export default function FeatureEngineeringPanel({ uploadResult, onError }) {
  const [options, setOptions] = useState({
    apply_scaling: true,
    apply_outlier_handling: true,
    apply_feature_selection: false,
    target_column: '',
    top_n_features: 20,
  });
  const [feResult, setFeResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [downloading, setDownloading] = useState(false);

  const columns = uploadResult?.schema_summary?.columns ?? [];
  const columnNames = columns.map((c) => c.column).filter(Boolean);

  const handleRun = useCallback(async () => {
    if (!uploadResult?.download_id) {
      onError?.('Upload a file first.');
      return;
    }
    setLoading(true);
    setFeResult(null);
    onError?.('');
    try {
      const payload = {
        download_id: uploadResult.download_id,
        target_column: options.target_column || null,
        apply_scaling: options.apply_scaling,
        apply_outlier_handling: options.apply_outlier_handling,
        apply_feature_selection: options.apply_feature_selection,
        top_n_features: options.top_n_features,
      };
      const data = await runFeatureEngineering(payload);
      setFeResult(data);
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message ?? 'Feature engineering failed';
      onError?.(Array.isArray(msg) ? msg.join(', ') : msg);
    } finally {
      setLoading(false);
    }
  }, [uploadResult, options, onError]);

  const handleDownload = useCallback(async () => {
    if (!feResult?.download_id) return;
    setDownloading(true);
    onError?.('');
    try {
      const { blob, filename } = await downloadEngineeredCsv(feResult.download_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      onError?.(err.response?.data?.detail ?? err.message ?? 'Download failed');
    } finally {
      setDownloading(false);
    }
  }, [feResult, onError]);

  return (
    <section className="rounded-xl border border-surface-600 bg-surface-800/50 p-6">
      <h2 className="text-lg font-semibold text-slate-200 mb-4">Feature Engineering</h2>
      <p className="text-sm text-slate-400 mb-6">
        Run encoding, outlier handling, scaling, interactions, multicollinearity removal, and optional feature selection.
      </p>

      {/* Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <div className="space-y-4">
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.apply_scaling}
              onChange={(e) => setOptions((o) => ({ ...o, apply_scaling: e.target.checked }))}
              className="rounded border-surface-500 text-accent-primary focus:ring-accent-primary"
            />
            <span className="text-slate-300">Apply scaling</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.apply_outlier_handling}
              onChange={(e) => setOptions((o) => ({ ...o, apply_outlier_handling: e.target.checked }))}
              className="rounded border-surface-500 text-accent-primary focus:ring-accent-primary"
            />
            <span className="text-slate-300">Apply outlier handling</span>
          </label>
          <label className="flex items-center gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={options.apply_feature_selection}
              onChange={(e) => setOptions((o) => ({ ...o, apply_feature_selection: e.target.checked }))}
              className="rounded border-surface-500 text-accent-primary focus:ring-accent-primary"
            />
            <span className="text-slate-300">Apply feature selection</span>
          </label>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm text-slate-400 mb-1">Target column (optional)</label>
            <select
              value={options.target_column}
              onChange={(e) => setOptions((o) => ({ ...o, target_column: e.target.value }))}
              className="w-full rounded-lg bg-surface-700 border border-surface-600 text-slate-200 px-3 py-2 text-sm focus:ring-2 focus:ring-accent-primary"
            >
              <option value="">— None —</option>
              {columnNames.map((col) => (
                <option key={col} value={col}>{col}</option>
              ))}
            </select>
          </div>
          {options.apply_feature_selection && (
            <div>
              <label className="block text-sm text-slate-400 mb-1">Top N features</label>
              <input
                type="number"
                min={5}
                max={100}
                value={options.top_n_features}
                onChange={(e) => setOptions((o) => ({ ...o, top_n_features: Number(e.target.value) || 20 }))}
                className="w-full rounded-lg bg-surface-700 border border-surface-600 text-slate-200 px-3 py-2 text-sm"
              />
            </div>
          )}
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-4 mb-6">
        <button
          onClick={handleRun}
          disabled={loading || !uploadResult?.download_id}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-primary hover:bg-accent-hover text-white font-medium disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? (
            <>
              <span className="inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Running…
            </>
          ) : (
            'Run Feature Engineering'
          )}
        </button>
        {feResult?.download_id && (
          <button
            onClick={handleDownload}
            disabled={downloading}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-surface-600 hover:bg-surface-500 text-slate-200 font-medium disabled:opacity-60 transition-colors"
          >
            {downloading ? 'Downloading…' : 'Download engineered CSV'}
          </button>
        )}
      </div>

      {/* Results */}
      {feResult && (
        <div className="space-y-6 mt-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="rounded-lg bg-surface-800 border border-surface-600 p-4">
              <p className="text-sm text-slate-400">Features created</p>
              <p className="text-xl font-bold text-slate-100">{feResult.features_created?.length ?? 0}</p>
            </div>
            <div className="rounded-lg bg-surface-800 border border-surface-600 p-4">
              <p className="text-sm text-slate-400">Features removed</p>
              <p className="text-xl font-bold text-slate-100">{feResult.features_removed?.length ?? 0}</p>
            </div>
            <div className="rounded-lg bg-surface-800 border border-surface-600 p-4">
              <p className="text-sm text-slate-400">Selected features</p>
              <p className="text-xl font-bold text-slate-100">{feResult.selected_features?.length ?? 0}</p>
            </div>
            <div className="rounded-lg bg-surface-800 border border-surface-600 p-4">
              <p className="text-sm text-slate-400">Rows × Cols</p>
              <p className="text-xl font-bold text-slate-100">{feResult.total_rows} × {feResult.total_columns}</p>
            </div>
          </div>

          {feResult.features_created?.length > 0 && (
            <div className="rounded-xl bg-surface-800 border border-surface-600 p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">Features created</h3>
              <p className="text-slate-400 text-sm break-all">{feResult.features_created.join(', ')}</p>
            </div>
          )}
          {feResult.features_removed?.length > 0 && (
            <div className="rounded-xl bg-surface-800 border border-surface-600 p-4">
              <h3 className="text-sm font-semibold text-slate-200 mb-2">Features removed</h3>
              <p className="text-slate-400 text-sm break-all">{feResult.features_removed.join(', ')}</p>
            </div>
          )}

          <FeatureImportanceChart featureImportance={feResult.feature_importance} />
          <div>
            <h3 className="text-lg font-semibold text-slate-200 mb-2">Engineered dataset preview</h3>
            <PreviewTable preview={feResult.engineered_preview} />
          </div>
        </div>
      )}
    </section>
  );
}
