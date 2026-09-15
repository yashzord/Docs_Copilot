"use client";

// Where Cognito sends the browser after sign-in, with ?code=... in the URL.
// A client component: the code exchange must run in the browser, because that is
// where the PKCE secret from step 1 lives (lib/auth.ts).

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { finishSignIn } from "@/lib/auth";

export default function Callback() {
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    finishSignIn()
      .then(() => router.replace("/"))
      .catch((err: unknown) => setError(err instanceof Error ? err.message : "Sign-in failed."));
  }, [router]);

  return (
    <main className="flex h-dvh items-center justify-center text-zinc-600">
      {error ? (
        <p role="alert">
          {error}{" "}
          <Link className="underline" href="/">
            Back
          </Link>
        </p>
      ) : (
        <p>Signing you in...</p>
      )}
    </main>
  );
}
