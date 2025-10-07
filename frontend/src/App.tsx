import React, { useState } from "react";
import { downloadICS, downloadCSV } from "./utils/exportCalendar";
import type { EventItem, EvaluationItem, ParseResult } from "./utils/types";
import { EvaluationsTable } from "./components/EvaluationsTable";
import { DetectedEvents } from "./components/DetectedEvents";
import { ExportButtons } from "./components/ExportButtons";

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");
  const [evaluations, setEvaluations] = useState<EvaluationItem[]>([]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
  };

  const handleUpload = async () => {
    if (!file) return alert("Please upload a syllabus PDF!");

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      // Vite automatically uses .env.development in dev mode and .env.production in build
      const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";
      console.log("API_BASE:", API_BASE); // DEBUG - remove after testing
      
      const response = await fetch(`${API_BASE}/parse-syllabus`, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data: ParseResult = await response.json();
      console.log("Parsed data:", data); // DEBUG
      console.log("Events count:", data.events?.length); // DEBUG
      
      setSummary(data.summary || "");
      setEvents(data.events || []);
      setEvaluations(data.evaluations || []);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to parse syllabus.");
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadICS = () => {
    if (!events.length) return;
    downloadICS(events.map(event => ({ ...event, date: event.date || "" })));
  };

  const handleDownloadCSV = () => {
    if (!events.length) return;
    downloadCSV(events.map(event => ({ ...event, date: event.date || "" })));
  };

  return (
    <div className="w-screen h-[100dvh] bg-white overflow-x-hidden">
      <div className="mx-auto max-w-2xl p-8 mt-60 mb-20">
        <h1 className="text-6xl font-bold mb-4 text-center text-gray-800">
          📚 Syllabus Parser
        </h1>

        <div className="w-122 text-right mb-4">
          <input
            type="file"
            accept=".pdf"
            onChange={handleFileChange}
            className="inline-block text-sm text-gray-900
                       file:mr-4 file:rounded-lg file:border-0
                       file:bg-gray-600 file:text-white file:px-4 file:py-2
                       hover:file:bg-gray-900"
          />
        </div>

        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Parsing..." : "Upload & Parse"}
        </button>

        <ExportButtons
          onDownloadICS={handleDownloadICS}
          onDownloadCSV={handleDownloadCSV}
          hasEvents={events.length > 0}
        />

        {summary && (
          <div className="mt-8 p-4 rounded-xl bg-gray-50 border">
            <h2 className="text-xl text-black font-semibold mb-2">📄 Summary</h2>
            <p className="text-black leading-relaxed">{summary}</p>
          </div>
        )}

        <DetectedEvents events={events} />

        {evaluations.length > 0 && <EvaluationsTable items={evaluations} />}
      </div>
    </div>
  );
}

export default App;
