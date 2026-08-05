import { request } from "./client";
import type { DrillDownResult, TaskResponse } from "./types";

/** Fetch a task by ID (used for polling). */
export function fetchTask(taskId: string): Promise<TaskResponse> {
  return request<TaskResponse>(`/task/${taskId}`);
}

/** Run a runnable follow-up question as a drill-down investigation step. */
export function runFollowUpDrilldown(
  taskId: string,
  questionIndex: number,
): Promise<DrillDownResult> {
  return request<DrillDownResult>(
    `/task/${taskId}/follow-ups/${questionIndex}/drilldown`,
    { method: "POST" },
  );
}
