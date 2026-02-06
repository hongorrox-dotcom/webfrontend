import { useCallback, useState } from "react";

export function useChat(onSend) {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const resetMessages = useCallback(() => {
    setMessages([]);
    setError("");
  }, []);

  const sendMessage = useCallback(
    async (question) => {
      const q = (question || "").trim();
      if (!q) return;

      setMessages((prev) => [...prev, { role: "user", text: q }]);
      setLoading(true);
      setError("");
      try {
        const reply = await onSend(q);
        setMessages((prev) => [...prev, { role: "assistant", text: reply }]);
      } catch (e) {
        setError("Чатбот хариу авахад алдаа гарлаа");
        setMessages((prev) => [
          ...prev,
          { role: "assistant", text: "Уучлаарай, алдаа гарлаа." }
        ]);
      } finally {
        setLoading(false);
      }
    },
    [onSend]
  );

  return { messages, loading, error, sendMessage, resetMessages };
}
