// Sign-in with Amazon Cognito's managed login page (docs/course/, lesson 31).
//
// The flow is OAuth 2.0 "authorization code with PKCE", the standard for a page
// that runs in the browser and has no secret to keep:
//
//   1. signIn()        make a random secret (the verifier), keep its hash
//                      (the challenge), send the browser to Cognito with the hash
//   2. (Cognito)       the person signs in; Cognito sends them back to /callback
//                      with a one-time code
//   3. finishSignIn()  trade the code plus the secret for tokens. Cognito hashes
//                      the secret and checks it matches step 1, so a stolen code
//                      is useless without the secret
//   4. accessToken()   the token every API call carries as "Authorization: Bearer"
//
// https://docs.aws.amazon.com/cognito/latest/developerguide/using-pkce-in-authorization-code.html

// Public identifiers, not secrets: they are in every login URL the browser visits.
const DOMAIN = process.env.NEXT_PUBLIC_COGNITO_DOMAIN;
const CLIENT_ID = process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID;
const SCOPE = "openid email"; // what the app client allows; email is all the page shows

// sessionStorage: per browser tab, gone when the tab closes. Good enough for a
// token that lives an hour. ponytail: no refresh token, so after an hour the next
// request gets a 401 and the page simply signs in again (Cognito remembers the
// login for that hour, so it is one redirect, no password).
const VERIFIER_KEY = "pkce_verifier";
const TOKENS_KEY = "tokens";

type Tokens = { access_token: string; id_token: string; expires_at: number };

export function isConfigured(): boolean {
  return Boolean(DOMAIN && CLIENT_ID);
}

function callbackUrl(): string {
  return `${window.location.origin}/callback`;
}

/** Step 1: remember a fresh secret, send the browser to Cognito's login page. */
export async function signIn(): Promise<void> {
  const verifier = randomString(64);
  sessionStorage.setItem(VERIFIER_KEY, verifier);
  const params = new URLSearchParams({
    response_type: "code",
    client_id: CLIENT_ID ?? "",
    redirect_uri: callbackUrl(),
    scope: SCOPE,
    code_challenge: await sha256Base64Url(verifier),
    code_challenge_method: "S256",
  });
  // https://docs.aws.amazon.com/cognito/latest/developerguide/authorization-endpoint.html
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- Cognito, not a page of ours
  window.location.href = `${DOMAIN}/oauth2/authorize?${params}`;
}

/** Step 3: on /callback, trade the code in the URL for tokens. Throws if anything is off. */
export async function finishSignIn(): Promise<void> {
  const query = new URLSearchParams(window.location.search);
  const code = query.get("code");
  const verifier = sessionStorage.getItem(VERIFIER_KEY);
  sessionStorage.removeItem(VERIFIER_KEY);
  if (query.get("error")) throw new Error(query.get("error_description") ?? query.get("error") ?? "Sign-in failed.");
  if (!code || !verifier) throw new Error("Sign-in did not complete. Try again.");

  // https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html
  const response = await fetch(`${DOMAIN}/oauth2/token`, {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: CLIENT_ID ?? "",
      code,
      redirect_uri: callbackUrl(),
      code_verifier: verifier,
    }),
  });
  if (!response.ok) throw new Error(`Cognito refused the code (HTTP ${response.status}).`);
  const body = (await response.json()) as { access_token: string; id_token: string; expires_in: number };
  const tokens: Tokens = {
    access_token: body.access_token,
    id_token: body.id_token,
    // A minute early, so a request never leaves with a token about to expire.
    expires_at: Date.now() + (body.expires_in - 60) * 1000,
  };
  sessionStorage.setItem(TOKENS_KEY, JSON.stringify(tokens));
}

/** Step 4: the token for the API, or null when signed out or expired. */
export function accessToken(): string | null {
  const tokens = readTokens();
  return tokens && tokens.expires_at > Date.now() ? tokens.access_token : null;
}

/** The signed-in person's email, for the header. From the id token: it is not verified
 * here, which is fine for showing a name; the backend verifies the access token. */
export function currentEmail(): string | null {
  const tokens = readTokens();
  if (!tokens) return null;
  try {
    const payload = JSON.parse(atob(tokens.id_token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.email === "string" ? payload.email : null;
  } catch {
    return null;
  }
}

/** Forget the tokens here, then end the Cognito session too and come back to the home page. */
export function signOut(): void {
  sessionStorage.removeItem(TOKENS_KEY);
  const params = new URLSearchParams({ client_id: CLIENT_ID ?? "", logout_uri: window.location.origin });
  // https://docs.aws.amazon.com/cognito/latest/developerguide/logout-endpoint.html
  // eslint-disable-next-line @next/next/no-location-assign-relative-destination -- Cognito, not a page of ours
  window.location.href = `${DOMAIN}/logout?${params}`;
}

export function forgetTokens(): void {
  sessionStorage.removeItem(TOKENS_KEY);
}

function readTokens(): Tokens | null {
  try {
    const raw = sessionStorage.getItem(TOKENS_KEY);
    return raw ? (JSON.parse(raw) as Tokens) : null;
  } catch {
    return null;
  }
}

function randomString(length: number): string {
  const alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  const bytes = crypto.getRandomValues(new Uint8Array(length));
  return Array.from(bytes, (b) => alphabet[b % alphabet.length]).join("");
}

/** SHA-256 of the text, base64url encoded without padding: the PKCE "S256" challenge. */
export async function sha256Base64Url(text: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return btoa(String.fromCharCode(...new Uint8Array(digest)))
    .replace(/\+/g, "-")
    .replace(/\//g, "_")
    .replace(/=+$/, "");
}
