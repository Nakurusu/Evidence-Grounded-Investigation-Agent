import { useState, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { uploadFile, investigateFiles } from "@/api/upload";

type UploadState =
  | { phase: "idle" }
  | { phase: "uploading" }
  | { phase: "error"; message: string };

const ACCEPTED = {
  "text/csv": [".csv"],
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": [".xlsx"],
  "application/vnd.ms-excel": [".xls"],
};

const MAX_SIZE = 50 * 1024 * 1024; // 50 MB

export function useUpload() {
  const navigate = useNavigate();
  const [state, setState] = useState<UploadState>({ phase: "idle" });
  const [primaryFile, setPrimaryFile] = useState<File | null>(null);
  const [secondaryFiles, setSecondaryFiles] = useState<File[]>([]);
  const [investigationQuestion, setInvestigationQuestion] = useState("");
  const [showSecondary, setShowSecondary] = useState(false);

  const setPrimary = useCallback((file: File | null) => {
    setState({ phase: "idle" });
    setPrimaryFile(file);
  }, []);

  const addSecondary = useCallback((files: File[]) => {
    setSecondaryFiles((prev) => [...prev, ...files]);
  }, []);

  const removeSecondary = useCallback((index: number) => {
    setSecondaryFiles((prev) => prev.filter((_, i) => i !== index));
  }, []);

  const start = useCallback(async () => {
    if (!primaryFile) return;

    setState({ phase: "uploading" });

    try {
      let taskId: string;

      if (secondaryFiles.length > 0) {
        const res = await investigateFiles(
          primaryFile,
          secondaryFiles,
          investigationQuestion,
        );
        taskId = res.task_id;
      } else {
        const res = await uploadFile(primaryFile, investigationQuestion);
        taskId = res.task_id;
      }

      navigate(`/investigation/${taskId}`);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : "Upload failed. Please try again.";
      setState({ phase: "error", message });
    }
  }, [primaryFile, secondaryFiles, investigationQuestion, navigate]);

  const reset = useCallback(() => {
    setState({ phase: "idle" });
    setPrimaryFile(null);
    setSecondaryFiles([]);
    setInvestigationQuestion("");
    setShowSecondary(false);
  }, []);

  return {
    state,
    primaryFile,
    secondaryFiles,
    investigationQuestion,
    showSecondary,
    setPrimary,
    addSecondary,
    removeSecondary,
    setInvestigationQuestion,
    setShowSecondary,
    start,
    reset,
    ACCEPTED,
    MAX_SIZE,
  };
}
