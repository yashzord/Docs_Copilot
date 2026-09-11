// Tests for the SSE parser. Run with: npm test
// Node's built-in test runner, so no test library to install.
// https://nodejs.org/api/test.html

import assert from "node:assert/strict";
import { test } from "node:test";

import { createSseParser } from "./sse.ts";

test("parses complete events", () => {
  const parse = createSseParser();

  const events = parse('event: delta\ndata: "Hel"\n\nevent: delta\ndata: "lo"\n\n');

  assert.deepEqual(events, [
    { event: "delta", data: '"Hel"' },
    { event: "delta", data: '"lo"' },
  ]);
});

test("holds a half-received event until the rest arrives", () => {
  const parse = createSseParser();

  assert.deepEqual(parse('event: delta\ndata: "Hel'), []);
  assert.deepEqual(parse('lo"\n\n'), [{ event: "delta", data: '"Hello"' }]);
});

test("skips keep-alive comment lines", () => {
  const parse = createSseParser();

  const events = parse(": ping\n\nevent: done\ndata: [DONE]\n\n");

  assert.deepEqual(events, [{ event: "done", data: "[DONE]" }]);
});

test("handles CRLF line endings, even when split between chunks", () => {
  const parse = createSseParser();

  assert.deepEqual(parse("event: usage\r\ndata: {}\r"), []);
  assert.deepEqual(parse("\n\r\n"), [{ event: "usage", data: "{}" }]);
});

test("an event with no name is called 'message'", () => {
  const parse = createSseParser();

  assert.deepEqual(parse("data: hi\n\n"), [{ event: "message", data: "hi" }]);
});
