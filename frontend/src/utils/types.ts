export type EventItem = { title: string; date?: string };
export type EvaluationItem = { name: string; weight: number };
export interface ParseResult {
  summary: string;
  events: EventItem[];
  evaluations?: EvaluationItem[];
}