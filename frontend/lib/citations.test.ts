// Tests for splitCitations. Run with: npm test

import assert from "node:assert/strict";
import { test } from "node:test";

import { splitCitations } from "./citations.ts";

test("separates text and markers", () => {
  assert.deepEqual(splitCitations("It costs money [1]. Also time [2]"), [
    { kind: "text", text: "It costs money " },
    { kind: "cite", n: 1 },
    { kind: "text", text: ". Also time " },
    { kind: "cite", n: 2 },
  ]);
});

test("text without markers stays one piece", () => {
  assert.deepEqual(splitCitations("no sources"), [{ kind: "text", text: "no sources" }]);
});

test("accepts gpt-oss's own marker style", () => {
  assert.deepEqual(splitCitations("cost【1】 and time【2†L3-L5】"), [
    { kind: "text", text: "cost" },
    { kind: "cite", n: 1 },
    { kind: "text", text: " and time" },
    { kind: "cite", n: 2 },
  ]);
});

test("ignores brackets that are not numbers", () => {
  assert.deepEqual(splitCitations("see [a] and [123]"), [
    { kind: "text", text: "see [a] and [123]" },
  ]);
});
