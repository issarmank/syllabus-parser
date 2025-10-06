import React, { useState } from "react";
import formatFullDate from "./components/EventDate";
import { downloadICS, downloadCSV } from "./utils/exportCalendar";
import type { EventItem, EvaluationItem, ParseResult } from "./utils/types";
import { EvaluationsTable } from "./components/EvaluationsTable";

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
      const API_BASE = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/+$/, "");
      const response = await fetch(`${API_BASE}/parse-syllabus`, {
        method: "POST",
        body: formData,
      });

      const data: ParseResult = await response.json();
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

        {events.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-3">
            <button
              onClick={handleDownloadICS}
              className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700"
            >
              Download .ics
            </button>
            <button
              onClick={handleDownloadCSV}
              className="px-4 py-2 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700"
            >
              Export CSV (Notion)
            </button>
          </div>
        )}

        {summary && (
          <div className="mt-8 p-4 rounded-xl bg-gray-50 border">
            <h2 className="text-xl text-black font-semibold mb-2">📄 Summary</h2>
            <p className="text-black leading-relaxed">{summary}</p>
          </div>
        )}

        {events.length > 0 && (
          <div className="mt-6">
            <h2 className="text-xl text-black font-semibold mb-2">Detected Events</h2>
            <ul className="space-y-3">
              {events.map((ev, idx) => (
                <li
                  key={idx}
                  className="p-3 border rounded-lg bg-gray-100 text-black flex justify-between"
                >
                  <span>{ev.title}</span>
                  <span className="text-black font-medium">
                    {formatFullDate(ev.date)}
                  </span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {evaluations.length > 0 && <EvaluationsTable items={evaluations} />}
      </div>
    </div>
  );
}

export default App;
