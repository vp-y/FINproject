"use client";

import { useEffect, useRef, useState } from "react";
import { api } from "@/lib/api";
import { Card, SectionTitle } from "@/components/ui";
import type { ChatMessage, RecommendationSource } from "@/lib/types";

type ChatResponse = {
  conversation_id: string;
  message: { role: "assistant"; content: string };
  sources: RecommendationSource[];
};

function storageKey(portfolioId: number) {
  return `aegis-chat-conversation-${portfolioId}`;
}

const SUGGESTED_QUESTIONS = [
  "Why is my portfolio risky?",
  "What should I do about my biggest holding?",
  "Suggest diversification options",
  "What's the outlook for my top sector?",
];

export default function ChatPanel({
  portfolioId,
}: {
  portfolioId: number;
}) {

  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [lastSources, setLastSources] = useState<RecommendationSource[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const scrollRef = useRef<HTMLDivElement>(null);

  // Reload an existing conversation for this portfolio, if the browser
  // already has one — otherwise a fresh conversation_id is minted by
  // the backend on the first message.
  useEffect(() => {

    const existingId = window.localStorage.getItem(storageKey(portfolioId));

    if (!existingId) {
      return;
    }

    setConversationId(existingId);

    api.get<ChatMessage[]>(`/chat/${portfolioId}/${existingId}`)
      .then((response) => setMessages(response.data))
      .catch(() => {});

  }, [portfolioId]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight });
  }, [messages]);

  const send = (override?: string) => {

    const text = (override ?? input).trim();

    if (!text || sending) {
      return;
    }

    setSending(true);
    setError(null);
    setInput("");
    setMessages((previous) => [...previous, { role: "user", content: text }]);

    api.post<ChatResponse>(`/chat/${portfolioId}`, {
      conversation_id: conversationId,
      message: text,
    })
      .then((response) => {

        setConversationId(response.data.conversation_id);
        window.localStorage.setItem(storageKey(portfolioId), response.data.conversation_id);

        setMessages((previous) => [...previous, response.data.message]);
        setLastSources(response.data.sources ?? []);

      })
      .catch(() => {
        setError("Couldn't reach the chatbot — is the backend running?");
      })
      .finally(() => {
        setSending(false);
      });

  };

  const handleKeyDown = (event: React.KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      send();
    }
  };

  return (

    <Card>

      <SectionTitle>
        Ask Aegis
      </SectionTitle>

      <div
        ref={scrollRef}
        className="max-h-80 space-y-3 overflow-y-auto px-5 py-3"
      >

        {

          messages.length === 0 ? (

            <div className="space-y-3">

              <p className="text-sm text-[var(--ink-3)]">
                Ask about your holdings, risk, or the recommendation above.
              </p>

              <div className="flex flex-wrap gap-2">
                {
                  SUGGESTED_QUESTIONS.map((question) => (
                    <button
                      key={question}
                      onClick={() => send(question)}
                      disabled={sending}
                      className="rounded-full border border-[var(--border)] px-3 py-1.5 text-xs text-[var(--ink-2)] transition-colors hover:border-[var(--accent)] hover:text-[var(--accent)] disabled:cursor-not-allowed disabled:opacity-50"
                    >
                      {question}
                    </button>
                  ))
                }
              </div>

            </div>

          ) : (

            messages.map((message, index) => (

              <div
                key={index}
                className={`flex ${message.role === "user" ? "justify-end" : "justify-start"}`}
              >
                <p
                  className={`max-w-[85%] whitespace-pre-wrap rounded-lg px-3 py-2 text-sm ${
                    message.role === "user"
                      ? "bg-[var(--accent)] text-[var(--accent-ink)]"
                      : "bg-[var(--surface-raised)] text-[var(--ink)]"
                  }`}
                >
                  {message.content}
                </p>
              </div>

            ))

          )

        }

        {

          sending && (
            <div className="flex justify-start">
              <p className="rounded-lg bg-[var(--surface-raised)] px-3 py-2 text-sm text-[var(--ink-3)]">
                Thinking...
              </p>
            </div>
          )

        }

      </div>

      {

        lastSources.length > 0 && (

          <div className="border-t border-[var(--gridline)] px-5 py-2">
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-[var(--ink-3)]">
              Sources
            </p>
            <ul className="space-y-0.5">
              {
                lastSources.map((source, index) => (
                  <li key={index} className="text-xs text-[var(--ink-2)]">
                    {source.document}
                    {source.page != null && ` — Page ${source.page}`}
                  </li>
                ))
              }
            </ul>
          </div>

        )

      }

      <div className="flex gap-2 border-t border-[var(--border)] p-3">

        <input
          value={input}
          onChange={(event) => setInput(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Ask a question..."
          disabled={sending}
          className="min-w-0 flex-1 rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2 text-sm outline-none focus:border-[var(--accent)] disabled:opacity-60"
        />

        <button
          onClick={() => send()}
          disabled={sending || !input.trim()}
          className="rounded-lg bg-[var(--accent)] px-4 py-2 text-sm font-medium text-[var(--accent-ink)] disabled:cursor-not-allowed disabled:opacity-40"
        >
          Send
        </button>

      </div>

      {
        error && (
          <p className="px-3 pb-3 text-xs text-[var(--critical)]">
            {error}
          </p>
        )
      }

    </Card>

  );

}
