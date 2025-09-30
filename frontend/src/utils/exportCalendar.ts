type EventItem = { title: string; date: string };

function pad(n: number) {
  return n.toString().padStart(2, "0");
}

function escapeICS(s: string) {
  return s
    .replace(/\\/g, "\\\\")
    .replace(/;/g, "\\;")
    .replace(/,/g, "\\,")
    .replace(/\r?\n/g, "\\n");
}

function isoToAllDay(iso: string) {
  // Expect YYYY-MM-DD
  const [y, m, d] = iso.split("-").map(Number);
  if (!y || !m || !d) return null;
  return `${y}${pad(m)}${pad(d)}`;
}

export function buildICS(events: EventItem[], calendarName = "Syllabus Events") {
  const now = new Date();
  const stamp = now.toISOString().replace(/[-:]/g, "").split(".")[0] + "Z";

  const lines: string[] = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//Syllabus Parser//EN",
    `X-WR-CALNAME:${escapeICS(calendarName)}`
  ];

  events.forEach((ev, i) => {
    if (!ev.date) return;
    const start = isoToAllDay(ev.date);
    if (!start) return;
    // All‑day event → DTEND is next day (exclusive)
    const dt = new Date(ev.date + "T00:00:00Z");
    dt.setUTCDate(dt.getUTCDate() + 1);
    const end = `${dt.getUTCFullYear()}${pad(dt.getUTCMonth() + 1)}${pad(dt.getUTCDate())}`;

    const uid = `${ev.title}-${ev.date}-${i}`.replace(/[^A-Za-z0-9]+/g, "") + "@syllabus-parser";
    lines.push("BEGIN:VEVENT");
    lines.push(`UID:${uid}`);
    lines.push(`DTSTAMP:${stamp}`);
    lines.push(`DTSTART;VALUE=DATE:${start}`);
    lines.push(`DTEND;VALUE=DATE:${end}`);
    lines.push(`SUMMARY:${escapeICS(ev.title)}`);
    lines.push("END:VEVENT");
  });

  lines.push("END:VCALENDAR");
  return lines.join("\r\n");
}

export function downloadICS(events: EventItem[]) {
  const ics = buildICS(events);
  const blob = new Blob([ics], { type: "text/calendar" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "syllabus-events.ics";
  a.click();
  URL.revokeObjectURL(url);
}

export function downloadCSV(events: EventItem[]) {
  // Basic CSV for Notion import (Title,Date)
  const rows = [["Title", "Date"]];
  events.forEach(e => rows.push([e.title, e.date || ""]));
  const csv = rows
    .map(r => r.map(f => `"${f.replace(/"/g, '""')}"`).join(","))
    .join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "syllabus-events.csv";
  a.click();
  URL.revokeObjectURL(url);
}