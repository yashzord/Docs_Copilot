"use client";

// The whole app screen: the sidebar on the left, the conversation on the right.
// A client component: it runs in the browser because it needs state (messages,
// the current conversation), events (typing, clicking) and streaming fetch.
// https://nextjs.org/docs/app/getting-started/server-and-client-components

import { type FormEvent, Fragment, type KeyboardEvent, useEffect, useRef, useState } from "react";

import Sidebar from "@/components/Sidebar";
import { type Inline, parseMarkdown } from "@/lib/markdown";
import { createSseParser } from "@/lib/sse";

type Source = { n: number; title: string; score: number; excerpt: string };
type ToolCall = { name: string; input: unknown };
type Message = {
  role: "user" | "assistant";
  content: string;
  tools?: ToolCall[]; // what the agent did before answering
  sources?: Source[]; // what its [1], [2] markers point to
};
type Usage = { input_tokens: number; output_tokens: number; model_calls: number };

export default function Chat() {
  // null = a new conversation; the backend creates the id on the first message.
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  // Bumped when a new conversation starts, so the sidebar reloads its list.
  const [sessionsVersion, setSessionsVersion] = useState(0);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the newest words in view while they stream in.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function updateAnswer(change: (answer: Message) => Message) {
    // Functional update: build on the latest state even when pieces arrive fast.
    // https://react.dev/reference/react/useState#updating-state-based-on-the-previous-state
    setMessages((prev) => [...prev.slice(0, -1), change(prev[prev.length - 1])]);
  }

  async function send() {
    const text = input.trim();
    if (!text || busy) return;

    setMessages((prev) => [...prev, { role: "user", content: text }, { role: "assistant", content: "" }]);
    setInput("");
    setError(null);
    setUsage(null);
    setBusy(true);
    let startedNewSession = false;

    try {
      // Only the new message goes up. The agent keeps the history in AgentCore Memory.
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: sessionId }),
      });
      if (!response.ok || !response.body) {
        throw new Error(await describeFailure(response));
      }

      // Bytes -> text. TextDecoderStream also handles a character split across two chunks.
      // https://developer.mozilla.org/en-US/docs/Web/API/TextDecoderStream
      const reader = response.body.pipeThrough(new TextDecoderStream()).getReader();
      const parse = createSseParser();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        for (const { event, data } of parse(value)) {
          if (event === "done") continue; // its data is [DONE], not JSON
          const payload: unknown = JSON.parse(data);
          if (event === "session") {
            const id = (payload as { session_id: string }).session_id;
            startedNewSession = id !== sessionId;
            setSessionId(id);
          } else if (event === "tool") {
            const call = payload as ToolCall;
            updateAnswer((a) => ({ ...a, tools: [...(a.tools ?? []), call] }));
          } else if (event === "sources") {
            updateAnswer((a) => ({ ...a, sources: payload as Source[] }));
          } else if (event === "delta") {
            updateAnswer((a) => ({ ...a, content: a.content + (payload as string) }));
          } else if (event === "usage") {
            setUsage(payload as Usage);
          } else if (event === "error") {
            setError((payload as { message: string }).message);
          }
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
      if (startedNewSession) setSessionsVersion((v) => v + 1);
    }
  }

  async function openSession(id: string) {
    if (busy) return;
    setError(null);
    setUsage(null);
    const response = await fetch(`/api/sessions/${encodeURIComponent(id)}/messages`);
    if (!response.ok) {
      setError(await describeFailure(response));
      return;
    }
    const history = (await response.json()) as { role: Message["role"]; text: string }[];
    setMessages(history.map((m) => ({ role: m.role, content: m.text })));
    setSessionId(id);
  }

  function newChat() {
    setSessionId(null);
    setMessages([]);
    setUsage(null);
    setError(null);
  }

  function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    void send();
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    // Enter sends, Shift+Enter makes a new line. isComposing: don't send while
    // typing with an input method (Chinese, Japanese, ...).
    if (event.key === "Enter" && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault();
      void send();
    }
  }

  return (
    <div className="flex h-dvh bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <Sidebar
        activeSessionId={sessionId}
        sessionsVersion={sessionsVersion}
        disabled={busy}
        onOpenSession={(id) => void openSession(id)}
        onNewChat={newChat}
      />

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <h1 className="text-lg font-semibold">Docs Copilot</h1>
          <p className="text-sm text-zinc-500">Answers from your documents, with sources</p>
        </header>

        {/* aria-live: screen readers announce new text as it arrives. */}
        <main className="flex-1 overflow-y-auto px-6 py-6" aria-live="polite">
          <div className="mx-auto flex max-w-3xl flex-col gap-4">
            {messages.length === 0 && (
              <p className="mt-24 text-center text-zinc-500">
                Upload a document on the left, then ask about it.
              </p>
            )}

            {/* Index as key is fine here: messages are only ever appended, never reordered. */}
            {messages.map((message, index) =>
              message.role === "user" ? (
                <div
                  key={index}
                  className="max-w-[80%] self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-white"
                >
                  {message.content}
                </div>
              ) : (
                <Answer
                  key={index}
                  message={message}
                  thinking={busy && index === messages.length - 1}
                />
              ),
            )}

            {usage && !busy && (
              <p className="self-start text-xs text-zinc-500">
                {usage.input_tokens} tokens in · {usage.output_tokens} out · {usage.model_calls} model
                calls
              </p>
            )}

            {error && (
              <p
                role="alert"
                className="rounded-lg border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-900 dark:bg-red-950 dark:text-red-200"
              >
                {error}
              </p>
            )}

            <div ref={bottomRef} />
          </div>
        </main>

        <form onSubmit={onSubmit} className="border-t border-zinc-200 px-6 py-4 dark:border-zinc-800">
          <div className="mx-auto flex max-w-3xl gap-3">
            <textarea
              aria-label="Message"
              rows={1}
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask about your documents. Enter to send, Shift+Enter for a new line."
              className="flex-1 resize-none rounded-xl border border-zinc-300 bg-white px-4 py-3 focus:outline-none focus:ring-2 focus:ring-indigo-500 dark:border-zinc-700 dark:bg-zinc-900"
            />
            <button
              type="submit"
              disabled={busy || !input.trim()}
              className="rounded-xl bg-indigo-600 px-5 font-medium text-white hover:bg-indigo-500 disabled:opacity-40"
            >
              Send
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

/** One answer: what the agent did, the text with citation markers, and the sources. */
function Answer({ message, thinking }: { message: Message; thinking: boolean }) {
  return (
    <div className="flex max-w-[85%] flex-col gap-2 self-start">
      {message.tools?.map((tool, i) => {
        const line = describeTool(tool);
        return (
          line && (
            <p key={i} className="text-xs text-zinc-500">
              {line}
            </p>
          )
        );
      })}

      <div className="flex flex-col gap-2 rounded-2xl rounded-bl-sm bg-white px-4 py-2.5 shadow-sm ring-1 ring-zinc-200 dark:bg-zinc-900 dark:ring-zinc-800">
        {message.content ? (
          <Markdown source={message.content} />
        ) : (
          thinking && <span className="animate-pulse text-zinc-400">Thinking...</span>
        )}
      </div>

      {message.sources && message.sources.length > 0 && (
        <div className="flex flex-col gap-1">
          {message.sources.map((source) => (
            // <details> opens and closes on click with no JavaScript.
            // ponytail: ids repeat across answers, so a marker jumps to the first match.
            <details
              key={source.n}
              id={`source-${source.n}`}
              className="rounded-lg border border-zinc-200 px-3 py-2 text-sm dark:border-zinc-800"
            >
              <summary className="cursor-pointer">
                <span className="font-medium">[{source.n}]</span> {source.title}
                <span className="ml-2 text-xs text-zinc-500">relevance {source.score}</span>
              </summary>
              <p className="mt-2 whitespace-pre-wrap text-xs text-zinc-600 dark:text-zinc-400">
                {source.excerpt}
              </p>
            </details>
          ))}
        </div>
      )}
    </div>
  );
}

/** The answer's markdown as page elements. Parsing lives in lib/markdown.ts. */
function Markdown({ source }: { source: string }) {
  return parseMarkdown(source).map((block, i) => {
    if (block.kind === "item") {
      return (
        <div key={i} className="flex gap-2" style={{ paddingLeft: `${block.depth * 1.25}rem` }}>
          <span className="shrink-0 text-zinc-500">{block.marker}</span>
          <span>
            <Pieces inline={block.inline} />
          </span>
        </div>
      );
    }
    return (
      <p key={i} className={block.kind === "h" ? "font-semibold" : undefined}>
        <Pieces inline={block.inline} />
      </p>
    );
  });
}

/** Bold, code and citation markers inside one block. [1] links to source card 1. */
function Pieces({ inline }: { inline: Inline[] }) {
  return inline.map((piece, i) => {
    if (piece.kind === "bold") return <strong key={i}>{piece.text}</strong>;
    if (piece.kind === "code") {
      return (
        <code key={i} className="rounded bg-zinc-100 px-1 text-[0.9em] dark:bg-zinc-800">
          {piece.text}
        </code>
      );
    }
    if (piece.kind === "cite") {
      return (
        <a
          key={i}
          href={`#source-${piece.n}`}
          className="mx-0.5 rounded bg-indigo-100 px-1 text-xs font-medium text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
        >
          {piece.n}
        </a>
      );
    }
    return <Fragment key={i}>{piece.text}</Fragment>;
  });
}

/** One line per tool call for the trace above an answer, or null to hide it. */
function describeTool(tool: ToolCall): string | null {
  const input = tool.input as {
    retrievalQuery?: { text?: string };
    query?: string;
    browser_input?: { action?: { type?: string; url?: string } };
  } | null;
  const docsQuery = input?.retrievalQuery?.text;
  if (docsQuery) return `Searched your documents for "${docsQuery}"`;
  if (tool.name.startsWith("graph___") && input?.query) {
    return `Searched the knowledge graph for "${input.query}"`;
  }
  if (tool.name === "browser" || input?.browser_input) {
    // A page read is several browser steps (open session, navigate, read text,
    // close). Only "navigate" says something useful: which page. Steps whose
    // input did not arrive as JSON are hidden too.
    const action = input?.browser_input?.action;
    return action?.type === "navigate" && action.url ? `Opened ${action.url}` : null;
  }
  return `Used ${tool.name}`;
}

async function describeFailure(response: Response): Promise<string> {
  if (response.status === 503) return "The assistant is busy. Try again in a few seconds.";
  try {
    const body: unknown = await response.json();
    if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // The body was not JSON. Fall through to the generic message below.
  }
  return `Request failed (HTTP ${response.status}).`;
}
