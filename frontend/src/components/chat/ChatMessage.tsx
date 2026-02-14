import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import BlockRenderer from "./BlockRenderer";

type ChatMessageProps = {
  role: "user" | "assistant" | "tool";
  content: string;
  blocks?: any[];
  status?: "loading" | "streaming" | "done" | "error";
  onAction?: (action: string, params?: Record<string, any>) => void;
};

export default function ChatMessage({ role, content, blocks, status, onAction }: ChatMessageProps) {
  const showContent = !!content;

  return (
    <div className={`chat-message ${role}`}>
      <div className="chat-bubble">
        {status === "loading" && !content ? (
          <div className="typing-indicator" aria-label="loading">
            <span />
            <span />
            <span />
          </div>
        ) : null}

        {showContent && (
          <div className="chat-markdown">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
          </div>
        )}

        {blocks && blocks.length > 0 && <BlockRenderer blocks={blocks} onAction={onAction} />}
      </div>
    </div>
  );
}
