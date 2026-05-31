"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Bot, User, X } from "lucide-react";

interface Message { role: "user" | "assistant"; content: string; }

interface Props {
  incidentId:    number;
  incidentTitle: string;
  onClose:       () => void;
}

const BASE    = process.env.NEXT_PUBLIC_API_URL  ?? "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? "";

/** Render markdown bold (**text**) and code (`code`) safely — no innerHTML, no XSS. */
function SafeMarkdown({ text }: { text: string }) {
  const parts: React.ReactNode[] = [];
  // Split on **bold** and `code` patterns
  const regex = /(\*\*[^*]+\*\*|`[^`]+`)/g;
  let last = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) {
      parts.push(text.slice(last, match.index));
    }
    const token = match[0];
    if (token.startsWith("**")) {
      parts.push(<strong key={match.index}>{token.slice(2, -2)}</strong>);
    } else if (token.startsWith("`")) {
      parts.push(
        <code key={match.index} style={{ background: "rgba(255,255,255,0.1)", padding: "1px 5px", borderRadius: "4px", fontSize: "12px", fontFamily: "monospace" }}>
          {token.slice(1, -1)}
        </code>
      );
    }
    last = match.index + token.length;
  }

  if (last < text.length) parts.push(text.slice(last));
  return <>{parts}</>;
}

export default function ChatPanel({ incidentId, incidentTitle, onClose }: Props) {
  const [messages, setMessages] = useState<Message[]>([
    { role: "assistant", content: `Hi! I'm here to help with incident **#${incidentId}**. Ask me anything about the root cause, remediation steps, or similar past issues.` }
  ]);
  const [input, setInput]       = useState("");
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef  = useRef<HTMLInputElement>(null);

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: "smooth" }); }, [messages]);
  useEffect(() => { inputRef.current?.focus(); }, []);

  async function send() {
    if (!input.trim() || streaming) return;
    const userMsg: Message = { role: "user", content: input.trim() };
    const newHistory = [...messages, userMsg];
    setMessages(newHistory);
    setInput("");
    setStreaming(true);
    setMessages(prev => [...prev, { role: "assistant", content: "" }]);

    try {
      const res = await fetch(`${BASE}/chat/stream`, {
        method:  "POST",
        headers: { "Content-Type": "application/json", "X-API-Key": API_KEY },
        body: JSON.stringify({
          incident_id: incidentId,
          messages:    newHistory.map(m => ({ role: m.role, content: m.content })),
        }),
      });

      if (!res.ok || !res.body) throw new Error("Stream failed");

      const reader  = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });
        const text = accumulated;
        setMessages(prev => {
          const updated = [...prev];
          updated[updated.length - 1] = { role: "assistant", content: text };
          return updated;
        });
      }
    } catch (err) {
      setMessages(prev => {
        const updated = [...prev];
        updated[updated.length - 1] = { role: "assistant", content: `⚠ Error: ${err instanceof Error ? err.message : "Request failed"}` };
        return updated;
      });
    } finally {
      setStreaming(false);
    }
  }

  return (
    <div style={{
      position: "fixed", bottom: "24px", right: "24px", width: "min(420px, 95vw)",
      height: "520px", background: "var(--card-bg)", border: "1px solid var(--border-accent)",
      borderRadius: "20px", backdropFilter: "blur(24px)", boxShadow: "0 20px 60px rgba(0,0,0,0.5)",
      display: "flex", flexDirection: "column", zIndex: 800, overflow: "hidden",
    }}>
      {/* Header */}
      <div style={{ padding: "14px 18px", borderBottom: "1px solid var(--border)", display: "flex", alignItems: "center", gap: "10px" }}>
        <div style={{ width: "32px", height: "32px", borderRadius: "50%", background: "linear-gradient(135deg,#33ff88,#00c3ff)", display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
          <Bot size={16} color="black" />
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{ fontWeight: 700, fontSize: "13px", color: "var(--text-primary)" }}>OpsPilot AI Chat</div>
          <div style={{ fontSize: "11px", color: "var(--text-tertiary)", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
            Incident #{incidentId} — {incidentTitle}
          </div>
        </div>
        <button onClick={onClose} aria-label="Close chat" style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-tertiary)", display: "flex" }}>
          <X size={16} />
        </button>
      </div>

      {/* Messages */}
      <div style={{ flex: 1, overflowY: "auto", padding: "16px", display: "flex", flexDirection: "column", gap: "12px" }}>
        {messages.map((msg, i) => (
          <div key={i} style={{ display: "flex", gap: "10px", alignItems: "flex-start", flexDirection: msg.role === "user" ? "row-reverse" : "row" }}>
            <div style={{
              width: "28px", height: "28px", borderRadius: "50%", flexShrink: 0,
              background: msg.role === "user" ? "linear-gradient(135deg,#33ff88,#00c3ff)" : "rgba(255,255,255,0.08)",
              display: "flex", alignItems: "center", justifyContent: "center",
            }}>
              {msg.role === "user" ? <User size={14} color="black" /> : <Bot size={14} color="var(--accent)" />}
            </div>
            <div style={{
              maxWidth: "78%", padding: "10px 14px",
              borderRadius: msg.role === "user" ? "16px 4px 16px 16px" : "4px 16px 16px 16px",
              background: msg.role === "user" ? "rgba(57,255,136,0.12)" : "rgba(255,255,255,0.04)",
              border: `1px solid ${msg.role === "user" ? "rgba(57,255,136,0.25)" : "var(--border)"}`,
              fontSize: "13px", lineHeight: 1.6, color: "var(--text-primary)",
            }}>
              {msg.content === "" && streaming ? (
                <span style={{ display: "inline-block", width: "8px", height: "14px", background: "var(--accent)", animation: "blink 0.8s step-end infinite" }} />
              ) : (
                /* Safe React rendering — no innerHTML, no XSS risk */
                <SafeMarkdown text={msg.content} />
              )}
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ padding: "12px 16px", borderTop: "1px solid var(--border)", display: "flex", gap: "10px" }}>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); } }}
          placeholder="Ask about this incident..."
          disabled={streaming}
          aria-label="Chat message input"
          style={{
            flex: 1, background: "var(--input-bg)", border: "1px solid var(--border)",
            borderRadius: "12px", padding: "10px 14px", color: "var(--text-primary)",
            fontSize: "13px", outline: "none",
          }}
        />
        <button
          onClick={() => void send()}
          disabled={!input.trim() || streaming}
          aria-label="Send message"
          style={{
            width: "40px", height: "40px", borderRadius: "12px", border: "none",
            background: input.trim() && !streaming ? "linear-gradient(135deg,#33ff88,#00c3ff)" : "var(--input-bg)",
            cursor: input.trim() && !streaming ? "pointer" : "not-allowed",
            display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0,
          }}
        >
          <Send size={16} color={input.trim() && !streaming ? "black" : "var(--text-tertiary)"} />
        </button>
      </div>
    </div>
  );
}
