"use client";

// Left column: past conversations (from AgentCore Memory) and documents (from S3),
// with an upload button that shows the Knowledge Base sync as it runs.

import { type ChangeEvent, useEffect, useState } from "react";

import { apiFetch } from "@/lib/api";

// title: the chat's first question, made by the backend. Older chats may have none.
type Session = { session_id: string; created_at: string; title?: string | null };
type Doc = { name: string; size: number; last_modified: string };
type Sync = { status: string; scanned: number; indexed: number; failed: number };

const ACCEPTED = ".pdf,.md,.txt,.html,.docx,.csv"; // the same list the backend allows
const SYNC_DONE = new Set(["COMPLETE", "FAILED", "STOPPED"]);

type Props = {
  activeSessionId: string | null;
  sessionsVersion: number; // changes when the list should be reloaded
  disabled: boolean;
  onOpenSession: (id: string) => void;
  onNewChat: () => void;
};

export default function Sidebar({ activeSessionId, sessionsVersion, disabled, onOpenSession, onNewChat }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [note, setNote] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);

  // Runs on first render and whenever sessionsVersion changes.
  // https://react.dev/reference/react/useEffect
  useEffect(() => {
    void getJson<Session[]>("/api/sessions").then((list) => list && setSessions(list));
  }, [sessionsVersion]);

  // State is set in .then(), after the fetch, never directly in the effect body:
  // React's lint rule flags a synchronous setState inside an effect.
  useEffect(() => {
    void getJson<Doc[]>("/api/documents").then((list) => list && setDocs(list));
  }, []);

  async function loadDocs() {
    const list = await getJson<Doc[]>("/api/documents");
    if (list) setDocs(list);
  }

  async function upload(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = ""; // so choosing the same file again still fires onChange
    if (!file) return;

    setUploading(true);
    setNote(`Uploading ${file.name}...`);
    try {
      // FormData makes a multipart body, the format the backend's UploadFile reads.
      // https://developer.mozilla.org/en-US/docs/Web/API/FormData
      const form = new FormData();
      form.append("file", file);
      const response = await apiFetch("/api/documents", { method: "POST", body: form });
      const body = (await response.json()) as {
        ingestion_job_id?: string | null;
        graph_ingestion_job_id?: string | null;
        detail?: string;
      };
      if (!response.ok) {
        setNote(body.detail ?? `Upload failed (HTTP ${response.status}).`);
        return;
      }
      await loadDocs();
      // The graph Knowledge Base syncs too. It is not polled: it only matters for
      // relationship questions, and the note says it is still updating.
      const graphNote = body.graph_ingestion_job_id ? " The graph is updating in the background too." : "";
      if (!body.ingestion_job_id) {
        setNote(`Uploaded. Another sync is running, so this file is indexed by the next one.${graphNote}`);
        return;
      }
      await watchSync(body.ingestion_job_id, graphNote);
    } catch {
      setNote("Upload failed. Is the backend running?");
    } finally {
      setUploading(false);
    }
  }

  async function watchSync(jobId: string, graphNote: string) {
    // ponytail: polls every 5 seconds. Fine for one user; a push channel scales better.
    while (true) {
      const sync = await getJson<Sync>(`/api/documents/sync/${jobId}`);
      if (!sync) {
        setNote("Could not check the sync.");
        return;
      }
      if (SYNC_DONE.has(sync.status)) {
        setNote(
          sync.status === "COMPLETE"
            ? `Ready to ask: ${sync.indexed} indexed, ${sync.failed} failed.${graphNote}`
            : `Sync ${sync.status.toLowerCase()}.`,
        );
        return;
      }
      setNote(`Indexing... ${sync.scanned} files scanned so far.`);
      await new Promise((resolve) => setTimeout(resolve, 5000));
    }
  }

  return (
    <aside className="flex w-72 shrink-0 flex-col gap-6 overflow-y-auto border-r border-zinc-200 p-4 dark:border-zinc-800">
      <section className="flex flex-col gap-2">
        <button
          type="button"
          onClick={onNewChat}
          disabled={disabled}
          className="rounded-lg bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-500 disabled:opacity-40"
        >
          New chat
        </button>
        <h2 className="mt-2 text-xs font-semibold uppercase text-zinc-500">Conversations</h2>
        {sessions.length === 0 && <p className="text-sm text-zinc-500">None yet.</p>}
        {sessions.map((s) => (
          <button
            key={s.session_id}
            type="button"
            onClick={() => onOpenSession(s.session_id)}
            disabled={disabled}
            className={`rounded-lg px-3 py-2 text-left text-sm hover:bg-zinc-100 disabled:opacity-40 dark:hover:bg-zinc-900 ${
              s.session_id === activeSessionId ? "bg-zinc-200 dark:bg-zinc-800" : ""
            }`}
          >
            <span className="block truncate" title={s.title ?? undefined}>
              {s.title || new Date(s.created_at).toLocaleString()}
            </span>
            {s.title && (
              <span className="block text-xs text-zinc-500">{new Date(s.created_at).toLocaleString()}</span>
            )}
          </button>
        ))}
      </section>

      <section className="flex flex-col gap-2">
        <h2 className="text-xs font-semibold uppercase text-zinc-500">Documents</h2>
        {/* A <label> wrapping the hidden input makes the whole box the file picker. */}
        <label
          className={`cursor-pointer rounded-lg border border-dashed border-zinc-300 px-3 py-3 text-center text-sm hover:bg-zinc-100 dark:border-zinc-700 dark:hover:bg-zinc-900 ${
            uploading ? "pointer-events-none opacity-40" : ""
          }`}
        >
          Upload a file
          <input type="file" accept={ACCEPTED} onChange={(e) => void upload(e)} className="hidden" />
        </label>
        {note && (
          <p role="status" className="text-xs text-zinc-500">
            {note}
          </p>
        )}
        {docs.map((d) => (
          <p key={d.name} className="truncate text-sm" title={d.name}>
            {d.name} <span className="text-xs text-zinc-500">{Math.ceil(d.size / 1024)} KB</span>
          </p>
        ))}
      </section>
    </aside>
  );
}

/** GET some JSON, or null if the request failed. */
async function getJson<T>(url: string): Promise<T | null> {
  try {
    const response = await apiFetch(url);
    return response.ok ? ((await response.json()) as T) : null;
  } catch {
    return null;
  }
}
