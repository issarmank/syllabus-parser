import React, { useState } from "react";

type EventItem = { title: string; date: string };

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [summary, setSummary] = useState("");

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
      const response = await fetch("http://127.0.0.1:8000/parse-syllabus", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setSummary(data.summary || "");
      setEvents(data.events || []);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to parse syllabus.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-screen h-[100dvh] bg-white overflow-x-hidden">
      <div className="mx-auto max-w-2xl p-8 mt-60">
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

        {summary && (
          <div className="mt-8 p-4 rounded-xl bg-gray-50 border">
            <h2 className="text-xl font-semibold mb-2">📄 Summary</h2>
            <p className="text-gray-700 leading-relaxed">{summary}</p>
          </div>
        )}

        {events.length > 0 && (
          <div className="mt-6">
            <h2 className="text-xl font-semibold mb-2">📅 Detected Events</h2>
            <ul className="space-y-3">
              {events.map((ev, idx) => (
                <li
                  key={idx}
                  className="p-3 border rounded-lg bg-gray-100 flex justify-between"
                >
                  <span>{ev.title}</span>
                  <span className="text-blue-600 font-medium">{ev.date}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
