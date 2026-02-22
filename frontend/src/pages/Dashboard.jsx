import { useCallback, useState } from 'react';
import FileUpload from '../components/FileUpload';
import SchemaTable from '../components/SchemaTable';
import PreviewTable from '../components/PreviewTable';
import SummaryCards from '../components/SummaryCards';
import MissingValueSummary from '../components/MissingValueSummary';
import StatsSummary from '../components/StatsSummary';
import FeatureEngineeringPanel from '../components/FeatureEngineeringPanel';
import { uploadFile, downloadCleanedCsv } from '../services/api';

export default function Dashboard() {
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState('');
  const [downloading, setDownloading] = useState(false);

  const handleFileSelect = useCallback(async (file) => {
    setError('');
    setResult(null);
    setProgress(0);
    setLoading(true);
    try {
      const data = await uploadFile(file, setProgress);
      setResult(data);
    } catch (err) {
      const msg = err.response?.data?.detail ?? err.message ?? 'Upload failed';
      setError(Array.isArray(msg) ? msg.join(', ') : msg);
    } finally {
      setLoading(false);
      setProgress(100);
    }
  }, []);

  const handleDownload = useCallback(async () => {
    if (!result?.download_id) return;
    setDownloading(true);
    setError('');
    try {
      const { blob, filename } = await downloadCleanedCsv(result.download_id);
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError(err.response?.data?.detail ?? err.message ?? 'Download failed');
    } finally {
      setDownloading(false);
    }
  }, [result]);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="border-b border-surface-600 bg-surface-800/80 backdrop-blur">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold tracking-tight text-white">
              FeaturePilot
            </h1>
            <span className="text-sm text-slate-400">Auto Data Structuring</span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Upload section */}
        <section className="mb-8">
          <h2 className="text-lg font-semibold text-slate-200 mb-4">Upload data</h2>
          <FileUpload onFileSelect={handleFileSelect} disabled={loading} />
          {loading && (
            <div className="mt-4">
              <div className="h-2 rounded-full bg-surface-700 overflow-hidden">
                <div
                  className="h-full bg-accent-primary transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
              <p className="text-sm text-slate-400 mt-2">Uploading & processing…</p>
            </div>
          )}
          {error && (
            <div className="mt-4 p-4 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm">
              {error}
            </div>
          )}
        </section>

        {/* Results */}
        {result && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <h2 className="text-lg font-semibold text-slate-200">Results</h2>
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-accent-primary hover:bg-accent-hover text-white font-medium disabled:opacity-60 transition-colors"
              >
                {downloading ? (
                  'Downloading…'
                ) : (
                  <>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                    </svg>
                    Download cleaned CSV
                  </>
                )}
              </button>
            </div>

            <div className="space-y-6">
              <SummaryCards data={result} />
              <SchemaTable schema={result.schema_summary} />
              <MissingValueSummary missing_summary={result.missing_summary} />
              <StatsSummary stats_summary={result.stats_summary} />
              <PreviewTable preview={result.preview} />
            </div>

            {/* Phase 2: Feature Engineering */}
            <div className="mt-10">
              <FeatureEngineeringPanel uploadResult={result} onError={setError} />
            </div>
          </>
        )}
      </main>
    </div>
  );
}
