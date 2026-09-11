// A small markdown reader for the agent's answers: paragraphs, headings, list
// items, **bold**, `code`, and citation markers like [1].
//
// The model writes markdown. Shown as plain text it looks like "**Cost**", so the
// page turns it into blocks and inline pieces, and Chat.tsx draws them.
// ponytail: a subset on purpose. Tables, links and quotes stay plain text.
// Upgrade: the react-markdown package, if answers start using more.

import { splitCitations } from "./citations.ts";

export type Inline =
  | { kind: "text"; text: string }
  | { kind: "bold"; text: string }
  | { kind: "code"; text: string }
  | { kind: "cite"; n: number };

export type Block =
  | { kind: "p"; inline: Inline[] }
  | { kind: "h"; inline: Inline[] }
  | { kind: "item"; marker: string; depth: number; inline: Inline[] };

const INLINE = /\*\*(.+?)\*\*|`([^`]+)`/g;
const LIST_ITEM = /^(\s*)([-*+]|\d+[.)])\s+(.*)$/;
const HEADING = /^#{1,6}\s+(.*)$/;

/** One line of text as pieces: plain text, bold, code, and citation markers. */
export function parseInline(text: string): Inline[] {
  const out: Inline[] = [];
  const pushText = (s: string) => {
    for (const piece of splitCitations(s)) out.push(piece);
  };
  let last = 0;
  for (const match of text.matchAll(INLINE)) {
    if (match.index > last) pushText(text.slice(last, match.index));
    out.push(match[1] !== undefined ? { kind: "bold", text: match[1] } : { kind: "code", text: match[2] });
    last = match.index + match[0].length;
  }
  if (last < text.length) pushText(text.slice(last));
  return out;
}

type RawBlock = { kind: "p" | "h" } | { kind: "item"; marker: string; depth: number };

/** A whole answer as blocks. Works on a half-streamed answer too: it just has fewer blocks. */
export function parseMarkdown(source: string): Block[] {
  const raw: { block: RawBlock; lines: string[] }[] = [];
  let open: { block: RawBlock; lines: string[] } | null = null;

  for (const line of source.split("\n")) {
    if (!line.trim()) {
      open = null; // a blank line ends the paragraph or item
      continue;
    }
    const item = LIST_ITEM.exec(line);
    const heading = HEADING.exec(line);
    if (item) {
      const ordered = /\d/.test(item[2]);
      open = {
        block: {
          kind: "item",
          marker: ordered ? item[2].replace(")", ".") : "•",
          depth: Math.min(2, Math.floor(item[1].length / 2)),
        },
        lines: [item[3]],
      };
      raw.push(open);
    } else if (heading) {
      raw.push({ block: { kind: "h" }, lines: [heading[1]] });
      open = null;
    } else if (open) {
      open.lines.push(line.trim()); // a wrapped line continues the paragraph or item
    } else {
      open = { block: { kind: "p" }, lines: [line.trim()] };
      raw.push(open);
    }
  }

  return raw.map(({ block, lines }) => ({ ...block, inline: parseInline(lines.join(" ")) }));
}
