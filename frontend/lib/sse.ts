// Turns a Server-Sent Events stream into { event, data } objects.
//
// The wire format: lines of "field: value", and a blank line ends one event.
// Text arrives in chunks that can cut an event (or a line) in half, so the
// parser keeps the unfinished part and waits for the rest.
// https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation

export type SseEvent = { event: string; data: string };

/** Returns a function you feed text as it arrives. Each call returns the events completed so far. */
export function createSseParser(): (chunk: string) => SseEvent[] {
  let buffer = "";

  return function push(chunk: string): SseEvent[] {
    // The spec allows \n, \r\n, or \r line endings. Normalize to \n, but keep a
    // trailing \r: it may be the first half of a \r\n split across two chunks.
    buffer = (buffer + chunk).replace(/\r\n|\r(?!$)/g, "\n");

    const events: SseEvent[] = [];
    let end = buffer.indexOf("\n\n");
    while (end !== -1) {
      const parsed = parseBlock(buffer.slice(0, end));
      if (parsed) events.push(parsed);
      buffer = buffer.slice(end + 2);
      end = buffer.indexOf("\n\n");
    }
    return events;
  };
}

function parseBlock(block: string): SseEvent | null {
  let event = "message"; // the spec's name for an event with no "event:" line
  const data: string[] = [];

  for (const line of block.split("\n")) {
    if (line.startsWith(":")) continue; // comment line, e.g. FastAPI's keep-alive ping
    const colon = line.indexOf(":");
    const field = colon === -1 ? line : line.slice(0, colon);
    let value = colon === -1 ? "" : line.slice(colon + 1);
    if (value.startsWith(" ")) value = value.slice(1); // one space after ":" is not part of the value
    if (field === "event") event = value;
    else if (field === "data") data.push(value);
  }

  // A block with no data (only comments) is not an event.
  return data.length > 0 ? { event, data: data.join("\n") } : null;
}
