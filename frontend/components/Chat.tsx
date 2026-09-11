"use client";

// The chat window. A client component: it runs in the browser because it
// needs state (the messages), events (typing, clicking) and streaming fetch.
// https://nextjs.org/docs/app/getting-started/server-and-client-components

import { type FormEvent, type KeyboardEvent, useEffect, useRef, useState } from "react";

import { createSseParser } from "@/lib/sse";

type Message = { role: "user" | "assistant"; content: string };
type Usage = { input_tokens: number; output_tokens: number; latency_ms: number };

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [usage, setUsage] = useState<Usage | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Keep the newest words in view while they stream in.
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages]);

  function appendToAnswer(piece: string) {
    // Functional update: build on the latest state even when pieces arrive fast.
    // https://react.dev/reference/react/useState#updating-state-based-on-the-previous-state
    setMessages((prev) => {
      const next = [...prev];
      const last = next[next.length - 1];
      next[next.length - 1] = { ...last, content: last.content + piece };
      return next;
    });
  }

  async function send() {
    const text = input.trim();
    if (!text || busy) return;

    // The whole conversation goes to the API each time: the model has no memory.
    // Empty answers from failed turns are dropped, because the API rejects empty messages.
    const history: Message[] = [
      ...messages.filter((m) => m.content !== ""),
      { role: "user", content: text },
    ];
    setMessages([...history, { role: "assistant", content: "" }]);
    setInput("");
    setError(null);
    setUsage(null);
    setBusy(true);

    try {
      const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: history }),
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
          if (event === "delta") appendToAnswer(JSON.parse(data) as string);
          else if (event === "usage") setUsage(JSON.parse(data) as Usage);
          else if (event === "error") setError((JSON.parse(data) as { message: string }).message);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
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

  function newChat() {
    setMessages([]);
    setUsage(null);
    setError(null);
  }

  return (
    <div className="flex h-dvh flex-col bg-zinc-50 text-zinc-900 dark:bg-zinc-950 dark:text-zinc-100">
      <header className="border-b border-zinc-200 px-6 py-4 dark:border-zinc-800">
        <div className="mx-auto flex max-w-3xl items-center justify-between">
          <div>
            <h1 className="text-lg font-semibold">Docs Copilot</h1>
            <p className="text-sm text-zinc-500">Streaming answers from Amazon Bedrock</p>
          </div>
          <button
            type="button"
            onClick={newChat}
            disabled={busy || messages.length === 0}
            className="rounded-lg border border-zinc-300 px-3 py-1.5 text-sm hover:bg-zinc-100 disabled:opacity-40 dark:border-zinc-700 dark:hover:bg-zinc-900"
          >
            New chat
          </button>
        </div>
      </header>

      {/* aria-live: screen readers announce new text as it arrives. */}
      <main className="flex-1 overflow-y-auto px-6 py-6" aria-live="polite">
        <div className="mx-auto flex max-w-3xl flex-col gap-4">
          {messages.length === 0 && (
            <p className="mt-24 text-center text-zinc-500">
              Ask anything to start. The answer streams in as it is written.
            </p>
          )}

          {/* Index as key is fine here: messages are only ever appended, never reordered. */}
          {messages.map((message, index) => (
            <div
              key={index}
              className={
                message.role === "user"
                  ? "max-w-[80%] self-end whitespace-pre-wrap rounded-2xl rounded-br-sm bg-indigo-600 px-4 py-2.5 text-white"
                  : "max-w-[80%] self-start whitespace-pre-wrap rounded-2xl rounded-bl-sm bg-white px-4 py-2.5 shadow-sm ring-1 ring-zinc-200 dark:bg-zinc-900 dark:ring-zinc-800"
              }
            >
              {message.content ||
                (busy && index === messages.length - 1 ? (
                  <span className="animate-pulse text-zinc-400">Thinking...</span>
                ) : null)}
            </div>
          ))}

          {usage && !busy && (
            <p className="self-start text-xs text-zinc-500">
              {usage.input_tokens} tokens in · {usage.output_tokens} out · {usage.latency_ms} ms
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
            placeholder="Type a message. Enter to send, Shift+Enter for a new line."
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
  );
}

async function describeFailure(response: Response): Promise<string> {
  if (response.status === 503) return "The model is busy. Try again in a few seconds.";
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
