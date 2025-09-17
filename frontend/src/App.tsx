import React, { useState } from "react";

type EventItem = { title: string; date: string };

function App() {
  const [file, setFile] = useState<File | null>(null);
  const [events, setEvents] = useState<EventItem[]>([]);
  const [loading, setLoading] = useState(false);

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
      const response = await fetch("http://127.0.0.1:8000/upload", {
        method: "POST",
        body: formData,
      });

      const data = await response.json();
      setEvents(data.events || []);
    } catch (error) {
      console.error("Upload error:", error);
      alert("Failed to parse syllabus.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col items-center justify-center p-6">
      <div className="bg-white shadow-xl rounded-2xl p-8 w-full max-w-lg">
        <h1 className="text-2xl font-bold mb-4 text-center text-gray-800">
          📚 Syllabus Parser
        </h1>

        <input
          type="file"
          accept=".pdf"
          onChange={handleFileChange}
          className="block w-full text-sm text-gray-700 mb-4"
        />

        <button
          onClick={handleUpload}
          disabled={loading}
          className="w-full py-2 px-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-700 transition disabled:opacity-50"
        >
          {loading ? "Parsing..." : "Upload & Parse"}
        </button>

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
