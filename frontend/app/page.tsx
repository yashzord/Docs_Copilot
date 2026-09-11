// The home page. A server component (the default in the App Router): it runs on
// the server and just renders the chat, which is a client component.
// https://nextjs.org/docs/app/getting-started/server-and-client-components
import Chat from "@/components/Chat";

export default function Home() {
  return <Chat />;
}
