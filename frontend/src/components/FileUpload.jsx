import { useCallback, useState } from 'react';

const ACCEPT = '.csv,.xlsx,.xls,.json';
const LABEL = 'CSV, Excel, or JSON';

export default function FileUpload({ onFileSelect, disabled }) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState('');

  const validate = useCallback((file) => {
    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['csv', 'xlsx', 'xls', 'json'].includes(ext)) {
      setError(`Please upload a ${LABEL} file.`);
      return false;
    }
    const maxMb = 50;
    if (file.size > maxMb * 1024 * 1024) {
      setError(`File must be under ${maxMb} MB.`);
      return false;
    }
    setError('');
    return true;
  }, []);

  const handleFile = useCallback(
    (file) => {
      if (!file || disabled) return;
      if (validate(file)) onFileSelect(file);
    },
    [onFileSelect, disabled, validate]
  );

  const onDrop = useCallback(
    (e) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer?.files?.[0];
      handleFile(file);
    },
    [handleFile]
  );

  const onDragOver = useCallback((e) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragLeave = useCallback((e) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onInputChange = useCallback(
    (e) => {
      const file = e.target?.files?.[0];
      handleFile(file);
      e.target.value = '';
    },
    [handleFile]
  );

  return (
    <div className="w-full">
      <label
        onDrop={onDrop}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        className={`
          flex flex-col items-center justify-center rounded-xl border-2 border-dashed
          py-12 px-6 cursor-pointer transition-colors
          ${disabled ? 'opacity-60 cursor-not-allowed' : 'cursor-pointer'}
          ${
            isDragging
              ? 'border-accent-primary bg-sky-500/10'
              : 'border-surface-500 hover:border-surface-400 bg-surface-800/50'
          }
        `}
      >
        <input
          type="file"
          accept={ACCEPT}
          onChange={onInputChange}
          disabled={disabled}
          className="hidden"
        />
        <div className="text-center text-surface-500 mb-2">
          <svg
            className="w-12 h-12 mx-auto mb-2 text-accent-primary"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
          <p className="text-slate-300 font-medium">
            {isDragging ? 'Drop file here' : `Drag & drop ${LABEL} or click to browse`}
          </p>
        </div>
      </label>
      {error && (
        <p className="mt-2 text-sm text-red-400" role="alert">
          {error}
        </p>
      )}
    </div>
  );
}
