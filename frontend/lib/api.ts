// fetch() for our API: adds the signed-in person's token, and signs in again on a 401.
//
// Every call to /api/... goes through here, so no component has to think about
// tokens. The proxy forwards the header to FastAPI, which verifies it (lesson 31).

import { accessToken, forgetTokens, signIn } from "@/lib/auth";

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = accessToken();
  if (!token) {
    await signIn(); // leaves the page; nothing below runs
    throw new Error("Signing in...");
  }
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...init, headers });
  if (response.status === 401) {
    // The backend refused the token (expired, or the pool's settings changed). Start over.
    forgetTokens();
    await signIn();
    throw new Error("Signing in...");
  }
  return response;
}
