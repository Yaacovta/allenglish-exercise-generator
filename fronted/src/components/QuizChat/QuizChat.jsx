import React, { useState } from "react";

export default function QuizChat({ onSendMessage }) {
  const [msg, setMsg] = useState("");
  const [sending, setSending] = useState(false);

  async function handleSend(e) {
    e.preventDefault();
    const trimmed = msg.trim();
    if (!trimmed) return;              // אל תשלח ריק
    try {
      setSending(true);
      await onSendMessage(trimmed);    // חשוב: מחכים לתשובה
      setMsg("");                      // נקה רק אחרי הצלחה
    } catch (err) {
      console.error("Chat send failed:", err);
      // אל תנקה את השדה במקרה כשל, כדי שהמשתמש לא יאבד את ההודעה
    } finally {
      setSending(false);
    }
  }

  return (
    <form onSubmit={handleSend} style={{ display: "flex", gap: 8, marginTop: 12 }}>
      <input
        type="text"
        value={msg}
        onChange={(e) => setMsg(e.target.value)}
        placeholder="Type your edit request..."
        style={{ flex: 1, padding: 8 }}
      />
      <button type="submit" disabled={sending || !msg.trim()}>
        {sending ? "Sending..." : "Send"}
      </button>
    </form>
  );
}
