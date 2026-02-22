/**
 * API client for FeaturePilot backend.
 * Uses VITE_API_URL from env or defaults to http://localhost:8000.
 */
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 min for large uploads
});

/**
 * Upload file (CSV, Excel, JSON). Returns schema, missing summary, stats, preview.
 * @param {File} file
 * @param {function(progress: number)} onProgress - optional progress callback 0-100
 * @returns {Promise<UploadResponse>}
 */
export async function uploadFile(file, onProgress) {
  const formData = new FormData();
  formData.append('file', file);

  const config = onProgress
    ? {
        onUploadProgress: (e) => {
          const pct = e.total ? Math.round((e.loaded / e.total) * 100) : 0;
          onProgress(pct);
        },
      }
    : {};

  const { data } = await api.post('/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    ...config,
  });
  return data;
}

/**
 * Download cleaned CSV. Pass download_id from upload response (optional; uses latest if omitted).
 * @param {string} [downloadId]
 * @returns {Promise<{ blob: Blob, filename: string }>}
 */
export async function downloadCleanedCsv(downloadId) {
  const params = downloadId ? { download_id: downloadId } : {};
  const { data, headers } = await api.get('/download', {
    params,
    responseType: 'blob',
  });
  let filename = 'cleaned_export.csv';
  const disposition = headers?.['content-disposition'];
  if (disposition) {
    const match = /filename="?([^";]+)"?/i.exec(disposition);
    if (match) filename = match[1].trim();
  }
  return { blob: data, filename };
}

/**
 * Run feature engineering on the cleaned dataset.
 * @param {object} params - { downloadId?, target_column?, apply_scaling, apply_outlier_handling, apply_feature_selection, top_n_features? }
 * @returns {Promise<FeatureEngineeringResponse>}
 */
export async function runFeatureEngineering(params) {
  const { data } = await api.post('/feature-engineering', params);
  return data;
}

/**
 * Download engineered CSV.
 * @param {string} [downloadId] - from feature-engineering response
 * @returns {Promise<{ blob: Blob, filename: string }>}
 */
export async function downloadEngineeredCsv(downloadId) {
  const params = downloadId ? { download_id: downloadId } : {};
  const { data, headers } = await api.get('/download/engineered', {
    params,
    responseType: 'blob',
  });
  let filename = 'engineered_export.csv';
  const disposition = headers?.['content-disposition'];
  if (disposition) {
    const match = /filename="?([^";]+)"?/i.exec(disposition);
    if (match) filename = match[1].trim();
  }
  return { blob: data, filename };
}

/**
 * Health check.
 */
export async function health() {
  const { data } = await api.get('/health');
  return data;
}

export default api;
