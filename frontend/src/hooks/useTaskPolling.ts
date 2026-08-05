import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { fetchTask } from "@/api/task";

/** Approximate pipeline stages shown in the loading UI. */
export type PipelineStage =
  | "parsing"
  | "profiling"
  | "signals"
  | "questions"
  | "hypotheses"
  | "evidence"
  | "validation"
  | "report"
  | "narrative"
  | "interactive"
  | "secondary_profiling"
  | "cross_dataset"
  | "completed";

export const PIPELINE_STAGES: PipelineStage[] = [
  "parsing",
  "profiling",
  "signals",
  "questions",
  "hypotheses",
  "evidence",
  "validation",
  "report",
  "narrative",
  "interactive",
  "secondary_profiling",
  "cross_dataset",
  "completed",
];

const STAGES: { key: PipelineStage; afterMs: number }[] = [
  { key: "parsing", afterMs: 0 },
  { key: "profiling", afterMs: 800 },
  { key: "signals", afterMs: 2000 },
  { key: "questions", afterMs: 3000 },
  { key: "hypotheses", afterMs: 4000 },
  { key: "evidence", afterMs: 5000 },
  { key: "validation", afterMs: 6500 },
  { key: "report", afterMs: 8000 },
  { key: "narrative", afterMs: 9500 },
  { key: "interactive", afterMs: 11000 },
];

export function useTaskPolling(taskId: string | undefined) {
  const [startedAt] = useState(() => Date.now());
  const [elapsed, setElapsed] = useState(0);

  // Tick elapsed time every second while processing
  const query = useQuery({
    queryKey: ["task", taskId],
    queryFn: () => fetchTask(taskId!),
    enabled: !!taskId,
    refetchInterval: (q) => {
      const status = q.state.data?.status;
      if (status === "pending" || status === "processing") return 2_000;
      return false;
    },
    retry: 2,
    retryDelay: 1_000,
  });

  const { data: task } = query;
  const isRunning =
    task?.status === "pending" || task?.status === "processing";

  // Tick the elapsed clock while the task is running
  useEffect(() => {
    if (!isRunning) return;
    const id = setInterval(() => {
      setElapsed(Date.now() - startedAt);
    }, 500);
    return () => clearInterval(id);
  }, [isRunning, startedAt]);

  // Determine fallback stage from elapsed time for old tasks without progress.
  let estimatedStage: PipelineStage = "parsing";
  for (let i = STAGES.length - 1; i >= 0; i--) {
    if (elapsed >= STAGES[i].afterMs) {
      estimatedStage = STAGES[i].key;
      break;
    }
  }
  const backendStage = task?.progress?.current_stage as PipelineStage | undefined;
  const stage = backendStage ?? estimatedStage;

  return {
    task,
    isLoading: query.isLoading,
    isError: query.isError,
    isRunning,
    stage,
    elapsed,
    stages: STAGES,
    progressPercent: task?.progress?.percent ?? null,
    completedStages: task?.progress?.completed_stages ?? [],
    stageDetail: task?.progress?.stage_detail ?? null,
    failedStage: task?.progress?.failed_stage ?? null,
    stageTitle: task?.progress?.stage_title ?? null,
    stageGoal: task?.progress?.stage_goal ?? null,
    stageInput: task?.progress?.stage_input ?? null,
    stageOutput: task?.progress?.stage_output ?? null,
    stageReason: task?.progress?.stage_reason ?? null,
    error: query.error,
  };
}

/** Format elapsed ms into a human-readable string. */
export function formatElapsed(ms: number): string {
  const sec = Math.floor(ms / 1000);
  if (sec < 60) return `${sec}s`;
  const min = Math.floor(sec / 60);
  const remainSec = sec % 60;
  return `${min}m ${remainSec}s`;
}
