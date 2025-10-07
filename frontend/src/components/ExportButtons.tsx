interface ExportButtonsProps {
  onDownloadICS: () => void;
  onDownloadCSV: () => void;
  hasEvents: boolean;
}

export function ExportButtons({ onDownloadICS, onDownloadCSV, hasEvents }: ExportButtonsProps) {
  if (!hasEvents) return null;

  return (
    <div className="mt-6 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 rounded-xl border border-blue-100">
      <h3 className="text-sm font-semibold text-gray-700 mb-3">📥 Export Options</h3>
      <div className="flex flex-wrap gap-3">
        <button
          onClick={onDownloadICS}
          className="flex-1 min-w-[140px] px-4 py-2.5 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors shadow-sm hover:shadow-md"
        >
          📆 Download .ics
        </button>
        <button
          onClick={onDownloadCSV}
          className="flex-1 min-w-[140px] px-4 py-2.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm hover:shadow-md"
        >
          📊 Export CSV (Notion)
        </button>
      </div>
    </div>
  );
}