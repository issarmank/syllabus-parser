import React from "react";

interface Props {
  date?: string | null;
  className?: string;
}

function formatDate(iso?: string | null): string {
  if (!iso) return "No date";
  const parts = iso.split("-");
  if (parts.length !== 3) return iso; // leave unknown format as-is
  const [y, m, d] = parts.map(Number);
  const dt = new Date(y, (m || 1) - 1, d || 1);
  if (isNaN(dt.getTime())) return iso;
  return dt.toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  });
}

export const EventDate: React.FC<Props> = ({ date, className = "" }) => {
  const formatted = formatDate(date);
  const missing = !date;
  return (
    <span
      className={
        "inline-block px-2 py-0.5 rounded text-xs font-medium " +
        (missing
          ? "bg-gray-200 text-gray-600"
          : "bg-indigo-50 text-indigo-700 border border-indigo-200") +
        " " +
        className
      }
      title={date || "No ISO date provided"}
    >
      {formatted}
    </span>
  );
};