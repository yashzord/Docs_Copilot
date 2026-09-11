// Tests for the answer markdown reader. Run with: npm test
// The first case is a real answer from Mistral Large 3 (2026-09-11), shortened.

import assert from "node:assert/strict";
import { test } from "node:test";

import { parseInline, parseMarkdown } from "./markdown.ts";

test("a real answer: intro, numbered items with bold, a nested bullet, citations", () => {
  const answer = [
    "Neptune was treated specially:",
    "",
    "1. **Cost**: it bills by the hour [1].",
    "",
    "2. **Rules**: to control costs:",
    "   - stop it when idle [2].",
  ].join("\n");

  assert.deepEqual(parseMarkdown(answer), [
    { kind: "p", inline: [{ kind: "text", text: "Neptune was treated specially:" }] },
    {
      kind: "item",
      marker: "1.",
      depth: 0,
      inline: [
        { kind: "bold", text: "Cost" },
        { kind: "text", text: ": it bills by the hour " },
        { kind: "cite", n: 1 },
        { kind: "text", text: "." },
      ],
    },
    {
      kind: "item",
      marker: "2.",
      depth: 0,
      inline: [
        { kind: "bold", text: "Rules" },
        { kind: "text", text: ": to control costs:" },
      ],
    },
    {
      kind: "item",
      marker: "•",
      depth: 1,
      inline: [
        { kind: "text", text: "stop it when idle " },
        { kind: "cite", n: 2 },
        { kind: "text", text: "." },
      ],
    },
  ]);
});

test("wrapped lines join their paragraph, blank lines split paragraphs", () => {
  assert.deepEqual(parseMarkdown("one\ntwo\n\nthree"), [
    { kind: "p", inline: [{ kind: "text", text: "one two" }] },
    { kind: "p", inline: [{ kind: "text", text: "three" }] },
  ]);
});

test("headings and inline code", () => {
  assert.deepEqual(parseMarkdown("## Setup\nrun `uv sync`"), [
    { kind: "h", inline: [{ kind: "text", text: "Setup" }] },
    {
      kind: "p",
      inline: [
        { kind: "text", text: "run " },
        { kind: "code", text: "uv sync" },
      ],
    },
  ]);
});

test("a lone asterisk or an unclosed ** stays plain text", () => {
  assert.deepEqual(parseInline("2 * 3 is **six"), [{ kind: "text", text: "2 * 3 is **six" }]);
});
