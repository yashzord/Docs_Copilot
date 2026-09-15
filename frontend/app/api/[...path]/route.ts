// ANY /api/<path>: forwards to the FastAPI backend's /v1/<path> and streams the answer back.
//
//   /api/chat                       -> /v1/chat              (Server-Sent Events)
//   /api/documents                  -> /v1/documents         (upload, list)
//   /api/documents/sync/<job>       -> /v1/documents/sync/<job>
//   /api/sessions/<id>/messages     -> /v1/sessions/<id>/messages
//
// Why the browser talks to this route instead of FastAPI directly:
// - same origin as the page, so no CORS setup
// - the backend URL stays on the server
// [...path] is a catch-all segment: params.path is the list of URL parts.
// https://nextjs.org/docs/app/api-reference/file-conventions/route

import type { NextRequest } from "next/server";

// Only these backend areas are reachable, so this is not an open proxy.
const ALLOWED = new Set(["chat", "documents", "sessions"]);

async function forward(request: NextRequest, ctx: RouteContext<"/api/[...path]">): Promise<Response> {
  // Server-only variable (no NEXT_PUBLIC_ prefix), so it never reaches the browser.
  // https://nextjs.org/docs/app/guides/environment-variables
  const apiUrl = process.env.API_URL;
  if (!apiUrl) {
    console.error("proxy: API_URL is not set");
    return Response.json({ detail: "The frontend is not configured (API_URL)." }, { status: 500 });
  }

  const { path } = await ctx.params;
  if (!ALLOWED.has(path[0])) {
    return Response.json({ detail: "Not found." }, { status: 404 });
  }
  const target = `${apiUrl}/v1/${path.map(encodeURIComponent).join("/")}${request.nextUrl.search}`;

  // Only two headers cross to the backend: the signed-in person's token, which
  // FastAPI verifies (lesson 31), and the content type, which keeps the multipart
  // boundary for uploads ("multipart/form-data; boundary=..."). Nothing else from
  // the browser's request is forwarded.
  const headers = new Headers();
  for (const name of ["authorization", "content-type"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method: request.method,
      headers,
      // ponytail: the body is read fully before forwarding (uploads are 50 MB at most).
      // Upgrade: stream it through, or upload straight to S3 with a presigned URL.
      body: request.method === "GET" ? undefined : await request.arrayBuffer(),
      // If the browser disconnects, cancel the backend call too, so no tokens are wasted.
      signal: request.signal,
    });
  } catch (error) {
    console.error("proxy: backend unreachable", error);
    return Response.json({ detail: "The backend is not reachable." }, { status: 502 });
  }

  // Pass the body through untouched. "no-transform" stops compression and proxies
  // from holding stream pieces back until the answer is complete.
  // https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#no-transform
  const out = new Headers({ "Cache-Control": "no-cache, no-transform" });
  for (const name of ["content-type", "retry-after"]) {
    const value = upstream.headers.get(name);
    if (value) out.set(name, value);
  }
  return new Response(upstream.body, { status: upstream.status, headers: out });
}

export const GET = forward;
export const POST = forward;
