
/** Response from POST /upload/ */
interface UploadResponse {
  task_id: string;
  status: string;
}

/** Upload a single CSV/Excel file. Returns the task ID for polling. */
export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);

  const res = await fetch("/api/upload/", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `${res.status} ${res.statusText}`);
  }

  return res.json();
}

/** Upload a primary file + optional secondary files (Phase 9). */
export async function investigateFiles(
  primary: File,
  secondary: File[],
): Promise<UploadResponse & { primary: string; secondary: string[] }> {
  const form = new FormData();
  form.append("primary_file", primary);
  for (const f of secondary) {
    form.append("secondary_files", f);
  }

  const res = await fetch("/api/upload/investigate/", {
    method: "POST",
    body: form,
  });

  if (!res.ok) {
    const body = await res.text();
    throw new Error(body || `${res.status} ${res.statusText}`);
  }

  return res.json();
}
