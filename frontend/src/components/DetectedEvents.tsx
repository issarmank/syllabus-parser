import formatFullDate from "./EventDate";
import type { EventItem } from "../utils/types";

interface DetectedEventsProps {
  events: EventItem[];
}

export function DetectedEvents({ events }: DetectedEventsProps) {
  if (events.length === 0) return null;

  return (
    <div className="mt-6">
      <h2 className="text-xl text-black font-semibold mb-4">📅 Detected Events</h2>
      <div className="space-y-2">
        {events.map((ev, idx) => (
          <div
            key={idx}
            className="p-4 border border-gray-200 rounded-lg bg-white hover:bg-gray-50 transition-colors shadow-sm"
          >
            <div className="flex justify-between items-center">
              <span className="text-gray-900 font-medium">{ev.title}</span>
              <span className="text-gray-600 text-sm font-semibold bg-gray-100 px-3 py-1 rounded-full">
                {formatFullDate(ev.date)}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}