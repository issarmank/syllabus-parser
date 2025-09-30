import React from "react";
import type { EvaluationItem } from "../utils/types";

export const EvaluationsTable: React.FC<{ items: EvaluationItem[] }> = ({ items }) => {
  if (!items || !items.length) return null;
  const total = items.reduce((s,i)=>s+i.weight,0).toFixed(2);
  return (
    <div className="mt-10">
      <h2 className="text-xl font-semibold mb-3 text-black">Evaluation Breakdown</h2>
      <div className="overflow-x-auto rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-2 text-left font-medium text-gray-700">Assessment</th>
              <th className="px-4 py-2 text-right font-medium text-gray-700">Weight (%)</th>
            </tr>
          </thead>
            <tbody>
              {items.map((ev,i)=>(
                <tr key={i} className="border-t last:border-b">
                  <td className="px-4 py-2 text-gray-800">{ev.name}</td>
                  <td className="px-4 py-2 text-right font-medium text-gray-900">{ev.weight}</td>
                </tr>
              ))}
              <tr className="border-t bg-gray-50">
                <td className="px-4 py-2 font-semibold text-gray-900">Total</td>
                <td className="px-4 py-2 text-right font-semibold text-gray-900">{total}</td>
              </tr>
            </tbody>
        </table>
      </div>
      {Math.abs(Number(total) - 100) > 0.5 && (
        <p className="mt-2 text-xs text-amber-600">
          Note: Weights normalized but sum != 100 exactly. Review manually.
        </p>
      )}
    </div>
  );
};