// POST /api/chat: forwards the browser's chat request to the FastAPI backend
// and streams the answer straight back, piece by piece.
//
// Why the browser talks to this route instead of FastAPI directly:
// - same origin as the page, so no CORS setup
// - the backend URL, and from D2 the login token, stay on the server
// https://nextjs.org/docs/app/api-reference/file-conventions/route

export async function POST(request: Request): Promise<Response> {
  // Server-only variable (no NEXT_PUBLIC_ prefix), so it never reaches the browser.
  // https://nextjs.org/docs/app/guides/environment-variables
  const apiUrl = process.env.API_URL;
  if (!apiUrl) {
    console.error("chat proxy: API_URL is not set");
    return Response.json({ detail: "The frontend is not configured (API_URL)." }, { status: 500 });
  }

  let upstream: Response;
  try {
    upstream = await fetch(`${apiUrl}/v1/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        // ponytail: one fixed demo tenant. Ceiling: every browser is the same tenant.
        // Upgrade: take the tenant from the Cognito session in D2.
        "X-Tenant-Id": "dev",
      },
      // The body is forwarded as-is. FastAPI validates it, so there is one set of rules.
      body: await request.text(),
      // If the browser disconnects, cancel the backend call too, so no tokens are wasted.
      signal: request.signal,
    });
  } catch (error) {
    console.error("chat proxy: backend unreachable", error);
    return Response.json({ detail: "The backend is not reachable." }, { status: 502 });
  }

  // Pass the stream through untouched. "no-transform" stops compression and
  // proxies from holding pieces back until the answer is complete.
  // https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control#no-transform
  const headers = new Headers({
    "Content-Type": upstream.headers.get("content-type") ?? "text/event-stream",
    "Cache-Control": "no-cache, no-transform",
  });
  const retryAfter = upstream.headers.get("retry-after");
  if (retryAfter) headers.set("Retry-After", retryAfter);

  return new Response(upstream.body, { status: upstream.status, headers });
}
