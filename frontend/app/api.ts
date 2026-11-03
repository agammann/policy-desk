export type DocumentRecord = { id: string; name: string; pages: number; chunks: number };
export type Citation = { id: number; document_id: string; document_name: string; page: number; text: string; score: number };
export type Answer = { answer: string; citations: Citation[]; mode: "extractive" | "generated" };
export type DocumentsResponse = { documents: DocumentRecord[]; errors?: (string | { filename?: string; message?: string })[] };

export const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  let response: Response;
  try { response = await fetch(`${API}${path}`, options); }
  catch { throw new Error("Could not connect to the policy service. Make sure the backend is running."); }
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status}).`);
  }
  return response.json() as Promise<T>;
}
