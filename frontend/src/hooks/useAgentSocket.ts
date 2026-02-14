import { useEffect, useRef, useState } from "react";

export type MessageStatus = "loading" | "streaming" | "done" | "error";

export type AgentMessage = {
  id: string;
  role: "user" | "assistant" | "tool";
  content: string;
  blocks?: any[];
  status?: MessageStatus;
};

type ToolPayload = {
  name?: string;
  error?: string;
};

type WsPayload = {
  type: string;
  message_id?: string;
  message?: any;
  delta?: {
    content?: string;
  };
  event_id?: string;
  tool?: ToolPayload;
  error?: string;
};

export function useAgentSocket() {
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const explicitWs = import.meta.env.VITE_WS_URL;
    const apiTarget = import.meta.env.VITE_API_TARGET;
    let wsUrl = explicitWs;
    if (!wsUrl && apiTarget) {
      try {
        const apiUrl = new URL(apiTarget);
        const wsProtocol = apiUrl.protocol === "https:" ? "wss:" : "ws:";
        wsUrl = `${wsProtocol}//${apiUrl.host}/ws/agent`;
      } catch {
        wsUrl = undefined;
      }
    }
    if (!wsUrl) {
      wsUrl = `${window.location.protocol === "https:" ? "wss" : "ws"}://${
        window.location.hostname
      }:8001/ws/agent`;
    }
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onerror = () => setConnected(false);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data) as WsPayload;
      if (data.type === "error") {
        const id = crypto.randomUUID();
        setMessages((prev) => [
          ...prev,
          {
            id,
            role: "assistant",
            content: `错误: ${data.message ?? data.error ?? "未知错误"}`,
            status: "error",
          },
        ]);
        return;
      }

      if (data.type === "message.start") {
        const id = data.message?.id ?? crypto.randomUUID();
        const role = data.message?.role ?? "assistant";
        setMessages((prev) => {
          if (prev.some((msg) => msg.id === id)) {
            return prev.map((msg) =>
              msg.id === id
                ? { ...msg, role, status: "loading", content: msg.content || "" }
                : msg
            );
          }
          return [...prev, { id, role, content: "", status: "loading" }];
        });
        return;
      }

      if (data.type === "message.delta") {
        const messageId = data.message_id;
        const chunk = data.delta?.content ?? "";
        if (!messageId) return;
        setMessages((prev) => {
          const index = prev.findIndex((msg) => msg.id === messageId);
          if (index === -1) {
            return [
              ...prev,
              { id: messageId, role: "assistant", content: chunk, status: "streaming" },
            ];
          }
          const next = [...prev];
          next[index] = {
            ...next[index],
            content: `${next[index].content}${chunk}`,
            status: "streaming",
          };
          return next;
        });
        return;
      }

      if (data.type === "message.end") {
        const messageId = data.message_id ?? data.message?.id ?? crypto.randomUUID();
        const role = data.message?.role ?? "assistant";
        const content = data.message?.content ?? "";
        const blocks = Array.isArray(data.message?.blocks) ? data.message?.blocks : undefined;
        setMessages((prev) => {
          const index = prev.findIndex((msg) => msg.id === messageId);
          if (index === -1) {
            return [...prev, { id: messageId, role, content, blocks, status: "done" }];
          }
          const next = [...prev];
          next[index] = {
            ...next[index],
            role,
            content: content || next[index].content,
            blocks,
            status: "done",
          };
          return next;
        });
        return;
      }

      if (data.type === "tool.start") {
        const eventId = data.event_id ?? crypto.randomUUID();
        const toolName = data.tool?.name ?? "未知工具";
        const content = `工具调用中：${toolName}`;
        setMessages((prev) => {
          if (prev.some((msg) => msg.id === eventId)) {
            return prev.map((msg) =>
              msg.id === eventId ? { ...msg, content, status: "loading" } : msg
            );
          }
          return [...prev, { id: eventId, role: "tool", content, status: "loading" }];
        });
        return;
      }

      if (data.type === "tool.end") {
        const eventId = data.event_id ?? crypto.randomUUID();
        const toolName = data.tool?.name ?? "未知工具";
        const content = `工具调用完成：${toolName}`;
        setMessages((prev) => {
          const index = prev.findIndex((msg) => msg.id === eventId);
          if (index === -1) {
            return [...prev, { id: eventId, role: "tool", content, status: "done" }];
          }
          const next = [...prev];
          next[index] = { ...next[index], content, status: "done" };
          return next;
        });
        return;
      }

      if (data.type === "tool.error") {
        const eventId = data.event_id ?? crypto.randomUUID();
        const toolName = data.tool?.name ?? "未知工具";
        const detail = data.tool?.error ? `（${data.tool.error}）` : "";
        const content = `工具调用失败：${toolName}${detail}`;
        setMessages((prev) => {
          const index = prev.findIndex((msg) => msg.id === eventId);
          if (index === -1) {
            return [...prev, { id: eventId, role: "tool", content, status: "error" }];
          }
          const next = [...prev];
          next[index] = { ...next[index], content, status: "error" };
          return next;
        });
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const sendMessage = (content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    const id = crypto.randomUUID();
    setMessages((prev) => [...prev, { id, role: "user", content, status: "done" }]);
    wsRef.current.send(JSON.stringify({ type: "user", content }));
  };

  const sendAction = (action: string, params?: Record<string, any>) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: "action", action, params }));
  };

  return { messages, sendMessage, sendAction, connected };
}
