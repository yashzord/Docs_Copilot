import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // From Next.js 16.3, `next dev` writes AGENTS.md and CLAUDE.md into the project
  // whenever it detects an AI coding agent, even if the app was created with
  // --no-agents-md. This repo keeps AI tooling files out of git, so it is off.
  // https://nextjs.org/docs/app/guides/ai-agents#opting-out
  agentRules: false,
};

export default nextConfig;
