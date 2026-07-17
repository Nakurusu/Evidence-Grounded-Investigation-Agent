import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { fetchTask } from "@/api/task";

/** Approximate pipeline stages shown in the loading UI. */
export type PipelineStage =
  | "parsing"
  | "profiling"
  | "signals"
  | "evidence"
  | "validation"
  | "report"
  | "narrative";

const STAGES: { key: PipelineStage; labelKey: string; afterMs: number }[] = [
  { key: "parsing", labelKey: "loading.stages.parsing", afterMs: 0 },
  { key: "profiling", labelKey: "loading.stages.profiling", afterMs: 800 },
  { key: "signals", labelKey: "loading.stages.signals", afterMs: 2000 },
  { key: "evidence", labelKey: "loading.stages.evidence", afterMs: 3500 },
  { key: "validation", labelKey: "loading.stages.validation", afterMs: 5000 },
  { key: "report", labelKey: "loading.stages.report", afterMs: 6500 },
  { key: "narrative", labelKey: "loading.stages.narrative", afterMs: 8000 },
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

  // Determine the likely current pipeline stage from elapsed time
  let stage: PipelineStage = "parsing";
  for (let i = STAGES.length - 1; i >= 0; i--) {
    if (elapsed >= STAGES[i].afterMs) {
      stage = STAGES[i].key;
      break;
    }
  }

  return {
    task,
    isLoading: query.isLoading,
    isError: query.isError,
    isRunning,
    stage,
    elapsed,
    stages: STAGES,
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
