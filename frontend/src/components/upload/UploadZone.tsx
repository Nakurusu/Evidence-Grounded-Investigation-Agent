import { useCallback, type DragEvent, useState } from "react";
import {
  Upload,
  FileSpreadsheet,
  X,
  Plus,
  Loader2,
  AlertTriangle,
  ArrowRight,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useT } from "@/i18n/LanguageProvider";
import { useUpload } from "@/hooks/useUpload";
import { cn } from "@/lib/utils";

/* ------------------------------------------------------------------ */
/*  Public API                                                         */
/* ------------------------------------------------------------------ */

export function UploadZone() {
  const t = useT();
  const {
    state,
    primaryFile,
    secondaryFiles,
    showSecondary,
    setPrimary,
    addSecondary,
    removeSecondary,
    setShowSecondary,
    start,
    reset,
    ACCEPTED,
  } = useUpload();

  const isIdle = state.phase === "idle";
  const isUploading = state.phase === "uploading";
  const hasFile = !!primaryFile;

  return (
    <div className="w-full max-w-xl space-y-5">
      {/* --- Primary drop zone ---------------------------------------- */}
      {!hasFile ? (
        <DropZone
          onFile={setPrimary}
          accept={ACCEPTED}
          disabled={!isIdle}
        />
      ) : (
        <FileCard
          file={primaryFile}
          onRemove={reset}
          disabled={!isIdle}
        />
      )}

      {/* --- Secondary files toggle (Phase 9) ------------------------- */}
      {hasFile && isIdle && (
        <div className="space-y-3">
          <button
            onClick={() => setShowSecondary(!showSecondary)}
            className="inline-flex items-center gap-1.5 text-xs text-muted-foreground transition-colors hover:text-foreground"
          >
            <Plus className="h-3.5 w-3.5" />
            {showSecondary
              ? "Hide secondary datasets"
              : "Add secondary datasets"}
            {showSecondary ? (
              <ChevronUp className="h-3 w-3" />
            ) : (
              <ChevronDown className="h-3 w-3" />
            )}
          </button>

          {showSecondary && (
            <div className="space-y-2">
              {secondaryFiles.map((f, i) => (
                <div
                  key={`${f.name}-${i}`}
                  className="flex items-center gap-3 rounded-md border border-border bg-surface px-3 py-2"
                >
                  <FileSpreadsheet className="h-4 w-4 shrink-0 text-muted" />
                  <span className="min-w-0 flex-1 truncate text-sm text-muted-foreground">
                    {f.name}
                  </span>
                  <span className="text-xs text-muted">
                    {formatSize(f.size)}
                  </span>
                  <button
                    onClick={() => removeSecondary(i)}
                    className="ml-1 flex h-5 w-5 items-center justify-center rounded text-muted-foreground transition-colors hover:text-foreground"
                  >
                    <X className="h-3.5 w-3.5" />
                  </button>
                </div>
              ))}
              <DropZone
                onFile={(f) => addSecondary([f])}
                accept={ACCEPTED}
                disabled={!isIdle}
                compact
              />
            </div>
          )}
        </div>
      )}

      {/* --- Error ---------------------------------------------------- */}
      {state.phase === "error" && (
        <div className="flex items-start gap-2 rounded-md bg-danger-muted p-3">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-danger" />
          <div className="min-w-0">
            <p className="text-sm text-danger">{state.message}</p>
            <button
              onClick={reset}
              className="mt-1 text-xs font-medium text-danger underline underline-offset-2"
            >
              Try again
            </button>
          </div>
        </div>
      )}

      {/* --- Submit button -------------------------------------------- */}
      {hasFile && isIdle && (
        <button
          onClick={start}
          className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-5 py-2.5 text-sm font-medium text-accent-foreground transition-all hover:opacity-90 animate-slide-up"
        >
          {t.home.cta}
          <ArrowRight className="h-4 w-4" />
        </button>
      )}

      {/* --- Uploading ------------------------------------------------- */}
      {isUploading && (
        <div className="flex items-center justify-center gap-3 py-4">
          <Loader2 className="h-5 w-5 animate-spin text-accent" />
          <span className="text-sm text-muted-foreground">Uploading...</span>
        </div>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Drop zone                                                          */
/* ------------------------------------------------------------------ */

function DropZone({
  onFile,
  accept,
  disabled,
  compact = false,
}: {
  onFile: (file: File) => void;
  accept: Record<string, string[]>;
  disabled: boolean;
  compact?: boolean;
}) {
  const [dragOver, setDragOver] = useState(false);
  const acceptStr = Object.values(accept).flat().join(",");

  const handleDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      if (disabled) return;
      const file = e.dataTransfer.files?.[0];
      if (file) onFile(file);
    },
    [disabled, onFile],
  );

  const handleDragOver = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      if (!disabled) setDragOver(true);
    },
    [disabled],
  );

  const handleDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    setDragOver(false);
  }, []);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) onFile(file);
      // Reset so re-selecting the same file triggers onChange
      e.target.value = "";
    },
    [onFile],
  );

  return (
    <label
      className={cn(
        "flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border border-dashed border-border transition-colors",
        compact ? "px-4 py-3" : "px-8 py-10",
        dragOver && "border-accent bg-accent-muted",
        disabled && "pointer-events-none opacity-50",
        !dragOver && !disabled && "hover:border-muted-foreground/40",
      )}
      onDrop={handleDrop}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
    >
      <Upload
        className={cn(
          "text-muted-foreground",
          compact ? "h-4 w-4" : "h-6 w-6",
        )}
      />
      <div className="text-center">
        <p
          className={cn(
            "text-muted-foreground",
            compact ? "text-xs" : "text-sm",
          )}
        >
          {compact
            ? "Drop or click to add"
            : "Drop your CSV or Excel file here, or click to browse"}
        </p>
        {!compact && (
          <p className="mt-1 text-xs text-muted">
            CSV, XLSX, XLS · up to 50 MB
          </p>
        )}
      </div>
      <input
        type="file"
        accept={acceptStr}
        onChange={handleChange}
        disabled={disabled}
        className="hidden"
      />
    </label>
  );
}

/* ------------------------------------------------------------------ */
/*  File card (shown after selection)                                  */
/* ------------------------------------------------------------------ */

function FileCard({
  file,
  onRemove,
  disabled,
}: {
  file: File;
  onRemove: () => void;
  disabled: boolean;
}) {
  return (
    <div className="flex items-center gap-4 rounded-lg border border-border bg-surface px-4 py-3">
      <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-md bg-accent-muted">
        <FileSpreadsheet className="h-5 w-5 text-accent" />
      </div>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-foreground">
          {file.name}
        </p>
        <p className="text-xs text-muted">{formatSize(file.size)}</p>
      </div>
      {disabled && (
        <button
          onClick={onRemove}
          className="flex h-7 w-7 items-center justify-center rounded text-muted-foreground transition-colors hover:bg-surface-elevated hover:text-foreground"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}

/* ------------------------------------------------------------------ */
/*  Helpers                                                            */
/* ------------------------------------------------------------------ */

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}
