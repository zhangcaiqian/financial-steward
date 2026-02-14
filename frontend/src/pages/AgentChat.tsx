import { useEffect, useRef, useState } from "react";
import { useAgentSocket } from "../hooks/useAgentSocket";
import ChatMessage from "../components/chat/ChatMessage";

export default function AgentChat() {
  const { messages, sendMessage, sendAction, connected } = useAgentSocket();
  const [input, setInput] = useState("");
  const chatWindowRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLTextAreaElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const hasMessages = messages.length > 0;
  const isIdle = !hasMessages;
  const suggestions = [
    "查看我当前的配置情况",
    "给我一份调仓建议",
    "查询沪深300指数走势",
  ];

  useEffect(() => {
    const container = chatWindowRef.current;
    if (!container) return;
    if (autoScroll) {
      container.scrollTop = container.scrollHeight;
    }
  }, [messages, autoScroll]);

  const submit = () => {
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput("");
  };

  const applySuggestion = (text: string) => {
    setInput(text);
    inputRef.current?.focus();
  };

  const handleScroll = () => {
    const container = chatWindowRef.current;
    if (!container) return;
    const threshold = 80;
    const distance = container.scrollHeight - (container.scrollTop + container.clientHeight);
    setAutoScroll(distance <= threshold);
  };

  const scrollToBottom = () => {
    const container = chatWindowRef.current;
    if (!container) return;
    container.scrollTop = container.scrollHeight;
    setAutoScroll(true);
  };

  return (
    <div className={`page chat-page${isIdle ? " hero-mode" : ""}`}>
      {isIdle ? (
        <div className="hero">
          <div className="hero-header">
            <div>
              <h1>资产配置管家</h1>
              <p>智能体会结合你的配置策略、持仓与市场数据给出建议。</p>
            </div>
            <span className={`status-dot ${connected ? "online" : "offline"}`}>
              {connected ? "在线" : "离线"}
            </span>
          </div>

          <div className="hero-body">
            <div className="agent-stage">
              <div className="agent-visual" aria-hidden="true">
                <div className="agent-halo" />
                <div className="agent-orb">
                  <div className="agent-core" />
                  <div className="agent-scan" />
                </div>
                <div className="agent-particles">
                  <span className="p1" />
                  <span className="p2" />
                  <span className="p3" />
                  <span className="p4" />
                </div>
              </div>
              <div className="agent-copy">
                <h2>我是你的资产配置管家</h2>
                <p>随时帮你查看配置、生成调仓方案、解读指数与周期信号。</p>
                <div className="agent-suggestions">
                  {suggestions.map((item) => (
                    <button key={item} onClick={() => applySuggestion(item)}>
                      {item}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </div>

          <div className="chat-input hero-input">
            <textarea
              rows={3}
              value={input}
              ref={inputRef}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder="例如：查看我当前的配置情况 / 给我调仓建议 / 查询沪深300指数走势"
            />
            <button onClick={submit}>
              <i className="fa-solid fa-paper-plane" /> 发送
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="page-header">
            <div>
              <h1>资产配置管家</h1>
              <p>智能体会结合你的配置策略、持仓与市场数据给出建议。</p>
            </div>
            <span className={`status-dot ${connected ? "online" : "offline"}`}>
              {connected ? "在线" : "离线"}
            </span>
          </div>

          <div className="chat-window" ref={chatWindowRef} onScroll={handleScroll}>
            {messages.map((msg) => (
              <ChatMessage
                key={msg.id}
                role={msg.role}
                content={msg.content}
                blocks={msg.blocks}
                status={msg.status}
                onAction={sendAction}
              />
            ))}
            {!autoScroll && messages.length > 0 ? (
              <button className="chat-jump" onClick={scrollToBottom}>
                跳到最新
              </button>
            ) : null}
          </div>

          <div className="chat-input">
            <textarea
              rows={3}
              value={input}
              ref={inputRef}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  submit();
                }
              }}
              placeholder="例如：查看我当前的配置情况 / 给我调仓建议 / 查询沪深300指数走势"
            />
            <button onClick={submit}>
              <i className="fa-solid fa-paper-plane" /> 发送
            </button>
          </div>
        </>
      )}
    </div>
  );
}
