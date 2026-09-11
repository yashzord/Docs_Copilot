// Splits an answer into plain text and citation markers like [1], so the UI can
// show each marker as a small link to its source card.

export type Piece = { kind: "text"; text: string } | { kind: "cite"; n: number };

// "[1]" is what the prompt asks for. gpt-oss often writes its own habit instead,
// "【1】" or "【1†L13-L17】" (the † part points at lines), so both are accepted.
const MARKER = /\[(\d{1,2})\]|【(\d{1,2})(?:†[^】]*)?】/g;

export function splitCitations(text: string): Piece[] {
  const pieces: Piece[] = [];
  let last = 0;
  for (const match of text.matchAll(MARKER)) {
    if (match.index > last) pieces.push({ kind: "text", text: text.slice(last, match.index) });
    pieces.push({ kind: "cite", n: Number(match[1] ?? match[2]) });
    last = match.index + match[0].length;
  }
  if (last < text.length) pieces.push({ kind: "text", text: text.slice(last) });
  return pieces;
}
