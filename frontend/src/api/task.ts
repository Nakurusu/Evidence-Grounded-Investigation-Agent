import { request } from "./client";
import type { TaskResponse } from "./types";

/** Fetch a task by ID (used for polling). */
export function fetchTask(taskId: string): Promise<TaskResponse> {
  return request<TaskResponse>(`/task/${taskId}`);
}
