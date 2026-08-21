"use client";

import {
  useEffect,
  useState,
} from "react";

export type AgentEvent = {
  type: string;
  agent?: string;
  tool?: string;
  message: string;
  data?: unknown;
};

export function useAgentWebSocket() {

  const [events, setEvents] =
    useState<AgentEvent[]>([]);

  const [connected, setConnected] =
    useState(false);

  // Generated inside useEffect (client-only) rather than at module/
  // render time, so there's no SSR/hydration mismatch — the session_id
  // only needs to exist once we're actually opening a socket.
  const [sessionId, setSessionId] =
    useState<string | null>(null);

  useEffect(() => {

    const id = crypto.randomUUID();
    setSessionId(id);

    const socket = new WebSocket(
      `ws://localhost:8000/ws/agents/${id}`
    );

    socket.onopen = () => {

      console.log(
        "WebSocket connected"
      );

      setConnected(true);
    };

    socket.onmessage = (event) => {

      const data = JSON.parse(
        event.data
      );

      setEvents((previous) => [
        ...previous,
        data,
      ]);
    };

    socket.onclose = () => {

      setConnected(false);

    };

    return () => {

      socket.close();

    };

  }, []);

  return {
    events,
    connected,
    sessionId,
  };

}
