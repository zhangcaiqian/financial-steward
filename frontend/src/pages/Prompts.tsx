import { useEffect, useState } from "react";
import { fetchPrompt, updatePrompt } from "../services/portfolio";

export default function Prompts() {
  const [content, setContent] = useState("");

  const load = async () => {
    const data = await fetchPrompt("agent_system");
    setContent(data.content);
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    await updatePrompt("agent_system", content);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>提示词管理</h1>
          <p>维护 LLM 抽取提示词，保存后立即生效。</p>
        </div>
      </div>

      <div className="card">
        <div className="field">
          <label>提示词内容</label>
          <textarea rows={12} value={content} onChange={(e) => setContent(e.target.value)} />
        </div>
        <button onClick={() => void save()}>保存提示词</button>
      </div>
    </div>
  );
}
