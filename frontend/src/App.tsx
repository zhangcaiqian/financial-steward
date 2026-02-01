import { useEffect, useMemo, useState } from "react";

type Fund = {
  id: number;
  code: string;
  name: string;
  fund_type: string;
};

type RebalancePlan = {
  id: number;
  status: string;
  total_assets: number;
  cash_balance: number;
  cash_target: number;
  should_rebalance: boolean;
  batches: { id: number; batch_no: number; due_at: string; status: string }[];
  trades: {
    id: number;
    action: string;
    amount: number;
    status: string;
    batch_no: number | null;
    fund_code: string;
    fund_name: string;
  }[];
};

const API_BASE = "/api";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  return response.json();
}

export default function App() {
  const [funds, setFunds] = useState<Fund[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [plan, setPlan] = useState<RebalancePlan | null>(null);
  const [chatText, setChatText] = useState("");
  const [chatResult, setChatResult] = useState<any>(null);
  const [chatHistory, setChatHistory] = useState<any[]>([]);
  const [promptText, setPromptText] = useState("");
  const [settings, setSettings] = useState<any>({});
  const [cycleTargets, setCycleTargets] = useState<Record<string, string>>({
    strong_recovery: "23",
    weak_recovery: "24",
    weak_recession: "23",
    strong_recession: "30",
  });
  const cycleLabels: Record<string, string> = {
    strong_recovery: "强复苏",
    weak_recovery: "弱复苏",
    weak_recession: "弱衰退",
    strong_recession: "强衰退",
  };

  const [fundForm, setFundForm] = useState({
    code: "",
    name: "",
    fund_type: "open",
    strong_recovery: "",
    weak_recovery: "",
    weak_recession: "",
    strong_recession: "",
  });

  const [holdingForm, setHoldingForm] = useState({
    fund_code: "",
    shares: "",
    avg_cost: "",
  });

  const [cashForm, setCashForm] = useState({ amount: "" });

  useEffect(() => {
    void refreshFunds();
    void refreshSummary();
    void refreshChatHistory();
    void refreshPrompt();
    void refreshSettings();
    void refreshCycleTargets();
  }, []);

  const refreshFunds = async () => {
    const data = await apiFetch<Fund[]>("/funds");
    setFunds(data);
  };

  const refreshSummary = async () => {
    const data = await apiFetch("/portfolio/summary");
    setSummary(data);
  };

  const refreshChatHistory = async () => {
    const data = await apiFetch<any[]>("/chat/history");
    setChatHistory(data);
  };

  const refreshPrompt = async () => {
    try {
      const data = await apiFetch("/prompts/chat_extraction");
      setPromptText(data.content);
    } catch {
      setPromptText("");
    }
  };

  const refreshSettings = async () => {
    const data = await apiFetch("/settings");
    setSettings(data);
  };

  const refreshCycleTargets = async () => {
    const data = await apiFetch<Record<string, number>>("/cycles/targets");
    const next: Record<string, string> = {};
    Object.entries(data).forEach(([key, value]) => {
      next[key] = (value * 100).toFixed(2);
    });
    setCycleTargets((prev) => ({ ...prev, ...next }));
  };

  const submitFund = async () => {
    const cycle_weights: Record<string, number> = {};
    const mapping = [
      ["strong_recovery", fundForm.strong_recovery],
      ["weak_recovery", fundForm.weak_recovery],
      ["weak_recession", fundForm.weak_recession],
      ["strong_recession", fundForm.strong_recession],
    ];
    mapping.forEach(([code, value]) => {
      if (value) {
        cycle_weights[code] = Number(value) / 100;
      }
    });
    await apiFetch("/funds", {
      method: "POST",
      body: JSON.stringify({
        code: fundForm.code,
        name: fundForm.name,
        fund_type: fundForm.fund_type,
        cycle_weights,
      }),
    });
    setFundForm({
      code: "",
      name: "",
      fund_type: "open",
      strong_recovery: "",
      weak_recovery: "",
      weak_recession: "",
      strong_recession: "",
    });
    await refreshFunds();
  };

  const submitHolding = async () => {
    await apiFetch("/holdings", {
      method: "POST",
      body: JSON.stringify({
        fund_code: holdingForm.fund_code,
        shares: Number(holdingForm.shares),
        avg_cost: Number(holdingForm.avg_cost || 0),
      }),
    });
    setHoldingForm({ fund_code: "", shares: "", avg_cost: "" });
    await refreshSummary();
  };

  const depositCash = async () => {
    await apiFetch("/cash/deposit", {
      method: "POST",
      body: JSON.stringify({ amount: Number(cashForm.amount) }),
    });
    setCashForm({ amount: "" });
    await refreshSummary();
  };

  const syncNavs = async () => {
    await apiFetch("/prices/sync", { method: "POST" });
    await refreshSummary();
  };

  const createPlan = async () => {
    const data = await apiFetch<{ plan_id: number }>("/portfolio/rebalance", {
      method: "POST",
      body: JSON.stringify({ persist: true, batch_interval_days: 7, recalc_each_batch: true }),
    });
    const detail = await apiFetch<RebalancePlan>(`/portfolio/rebalance/${data.plan_id}`);
    setPlan(detail);
  };

  const executeBatch = async (batchNo: number) => {
    if (!plan) return;
    await apiFetch(`/portfolio/rebalance/${plan.id}/execute/${batchNo}`, { method: "POST" });
    const detail = await apiFetch<RebalancePlan>(`/portfolio/rebalance/${plan.id}`);
    setPlan(detail);
    await refreshSummary();
  };

  const recalcPlan = async () => {
    if (!plan) return;
    await apiFetch(`/portfolio/rebalance/${plan.id}/recalculate`, { method: "POST" });
    const detail = await apiFetch<RebalancePlan>(`/portfolio/rebalance/${plan.id}`);
    setPlan(detail);
  };

  const ingestChat = async (confirm = false) => {
    if (!confirm) {
      const data = await apiFetch("/chat/ingest", {
        method: "POST",
        body: JSON.stringify({ text: chatText }),
      });
      setChatResult(data);
      await refreshChatHistory();
      return;
    }

    if (chatResult?.chat_id) {
      const data = await apiFetch("/chat/confirm", {
        method: "POST",
        body: JSON.stringify({ chat_id: chatResult.chat_id }),
      });
      setChatResult(data);
      await refreshSummary();
      await refreshFunds();
      await refreshChatHistory();
    }
  };

  const savePrompt = async () => {
    await apiFetch("/prompts", {
      method: "PUT",
      body: JSON.stringify({ name: "chat_extraction", content: promptText }),
    });
    await refreshPrompt();
  };

  const saveCycleTargets = async () => {
    const targets: Record<string, number> = {};
    Object.entries(cycleTargets).forEach(([key, value]) => {
      targets[key] = Number(value) / 100;
    });
    await apiFetch("/cycles/targets", {
      method: "PUT",
      body: JSON.stringify({ targets }),
    });
  };

  const saveSettings = async () => {
    await apiFetch("/settings", {
      method: "PUT",
      body: JSON.stringify({
        rebalance_frequency_days: Number(settings.rebalance_frequency_days),
        rebalance_threshold_ratio: Number(settings.rebalance_threshold_ratio),
        cash_target_ratio: Number(settings.cash_target_ratio),
        dca_batches: Number(settings.dca_batches),
      }),
    });
  };

  const tradesByBatch = useMemo(() => {
    if (!plan) return {};
    const grouped: Record<string, RebalancePlan["trades"]> = {};
    plan.trades.forEach((trade) => {
      const key = trade.batch_no ? `第${trade.batch_no}批` : "卖出";
      grouped[key] = grouped[key] || [];
      grouped[key].push(trade);
    });
    return grouped;
  }, [plan]);

  return (
    <div className="app">
      <header className="header">
        <div>
          <div className="title">资产配置管理系统</div>
          <div className="subtitle">T-1 净值估值 · 调仓分批执行 · 持仓录入</div>
        </div>
        <div className="actions">
          <button onClick={syncNavs}>同步净值</button>
          <button className="secondary" onClick={createPlan}>
            生成调仓计划
          </button>
        </div>
      </header>

      <section className="grid">
        <div className="card">
          <h3>新增基金</h3>
          <div className="field">
            <label>基金代码</label>
            <input
              value={fundForm.code}
              onChange={(e) => setFundForm({ ...fundForm, code: e.target.value })}
            />
          </div>
          <div className="field">
            <label>基金名称</label>
            <input
              value={fundForm.name}
              onChange={(e) => setFundForm({ ...fundForm, name: e.target.value })}
            />
          </div>
          <div className="field">
            <label>类型</label>
            <select
              value={fundForm.fund_type}
              onChange={(e) => setFundForm({ ...fundForm, fund_type: e.target.value })}
            >
              <option value="open">场外基金</option>
              <option value="etf">ETF</option>
            </select>
          </div>
          <div className="field">
            <label>强复苏 (%)</label>
            <input
              value={fundForm.strong_recovery}
              onChange={(e) => setFundForm({ ...fundForm, strong_recovery: e.target.value })}
            />
          </div>
          <div className="field">
            <label>弱复苏 (%)</label>
            <input
              value={fundForm.weak_recovery}
              onChange={(e) => setFundForm({ ...fundForm, weak_recovery: e.target.value })}
            />
          </div>
          <div className="field">
            <label>弱衰退 (%)</label>
            <input
              value={fundForm.weak_recession}
              onChange={(e) => setFundForm({ ...fundForm, weak_recession: e.target.value })}
            />
          </div>
          <div className="field">
            <label>强衰退 (%)</label>
            <input
              value={fundForm.strong_recession}
              onChange={(e) => setFundForm({ ...fundForm, strong_recession: e.target.value })}
            />
          </div>
          <button onClick={submitFund}>保存基金</button>
        </div>

        <div className="card">
          <h3>录入持仓</h3>
          <div className="field">
            <label>基金代码</label>
            <input
              value={holdingForm.fund_code}
              onChange={(e) => setHoldingForm({ ...holdingForm, fund_code: e.target.value })}
            />
          </div>
          <div className="field">
            <label>份额</label>
            <input
              value={holdingForm.shares}
              onChange={(e) => setHoldingForm({ ...holdingForm, shares: e.target.value })}
            />
          </div>
          <div className="field">
            <label>平均成本</label>
            <input
              value={holdingForm.avg_cost}
              onChange={(e) => setHoldingForm({ ...holdingForm, avg_cost: e.target.value })}
            />
          </div>
          <button onClick={submitHolding}>保存持仓</button>
        </div>

        <div className="card">
          <h3>现金管理</h3>
          <div className="field">
            <label>新增资金</label>
            <input
              value={cashForm.amount}
              onChange={(e) => setCashForm({ ...cashForm, amount: e.target.value })}
            />
          </div>
          <button onClick={depositCash}>入金</button>
          {summary && (
            <p>
              当前现金: <strong>{summary.cash_balance?.toFixed(2)}</strong>
              <span className="badge">目标 {summary.cash_target?.toFixed(2)}</span>
            </p>
          )}
        </div>

        <div className="card">
          <h3>调仓概览</h3>
          {summary ? (
            <>
              <p>总资产: {summary.total_assets?.toFixed(2)}</p>
              <p>是否需要调仓: {summary.should_rebalance ? "是" : "否"}</p>
              <ul className="list">
                {(summary.funds || []).map((fund: any) => (
                  <li key={fund.code}>
                    {fund.name} ({fund.code}) - 偏离 {fund.delta_value.toFixed(2)}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p>暂无数据</p>
          )}
        </div>
      </section>

      <section className="grid" style={{ marginTop: 20 }}>
        <div className="card">
          <h3>调仓计划</h3>
          {plan ? (
            <>
              <p>
                计划状态: {plan.status} · 总资产 {plan.total_assets.toFixed(2)}
              </p>
              <div className="actions" style={{ marginBottom: 12 }}>
                <button className="secondary" onClick={recalcPlan}>
                  重新计算剩余批次
                </button>
              </div>
              {Object.entries(tradesByBatch).map(([batch, trades]) => (
                <div key={batch} style={{ marginBottom: 12 }}>
                  <strong>{batch}</strong>
                  <ul className="list">
                    {trades.map((trade) => (
                      <li key={trade.id}>
                        {trade.action.toUpperCase()} {trade.fund_name} ({trade.fund_code}) -{" "}
                        {trade.amount.toFixed(2)} [{trade.status}]
                      </li>
                    ))}
                  </ul>
                  {batch !== "卖出" && (
                    <button
                      className="secondary"
                      onClick={() => {
                        const no = Number(batch.replace(/\D/g, ""));
                        if (no) void executeBatch(no);
                      }}
                    >
                      执行 {batch}
                    </button>
                  )}
                </div>
              ))}
            </>
          ) : (
            <p>点击“生成调仓计划”开始</p>
          )}
        </div>

        <div className="card">
          <h3>聊天录入</h3>
          <div className="field">
            <label>输入指令</label>
            <textarea
              rows={4}
              value={chatText}
              onChange={(e) => setChatText(e.target.value)}
              placeholder="示例：买入 510310 1000"
            />
          </div>
          <div className="actions">
            <button onClick={() => ingestChat(false)}>解析</button>
            <button className="secondary" onClick={() => ingestChat(true)}>
              确认写入
            </button>
          </div>
          {chatResult && (
            <pre style={{ whiteSpace: "pre-wrap", marginTop: 12 }}>
              {JSON.stringify(chatResult, null, 2)}
            </pre>
          )}
        </div>

        <div className="card">
          <h3>聊天历史</h3>
          <ul className="list">
            {chatHistory.map((item) => (
              <li key={item.id}>
                {item.text}
                <span className="badge">{item.status}</span>
              </li>
            ))}
          </ul>
        </div>
      </section>

      <section className="grid" style={{ marginTop: 20 }}>
        <div className="card">
          <h3>周期目标权重 (%)</h3>
          {Object.entries(cycleTargets).map(([key, value]) => (
            <div className="field" key={key}>
              <label>{cycleLabels[key] || key}</label>
              <input
                value={value}
                onChange={(e) => setCycleTargets({ ...cycleTargets, [key]: e.target.value })}
              />
            </div>
          ))}
          <button onClick={saveCycleTargets}>保存周期权重</button>
        </div>

        <div className="card">
          <h3>组合参数设置</h3>
          <div className="field">
            <label>调仓频率（天）</label>
            <input
              value={settings.rebalance_frequency_days || ""}
              onChange={(e) => setSettings({ ...settings, rebalance_frequency_days: e.target.value })}
            />
          </div>
          <div className="field">
            <label>偏离阈值</label>
            <input
              value={settings.rebalance_threshold_ratio || ""}
              onChange={(e) => setSettings({ ...settings, rebalance_threshold_ratio: e.target.value })}
            />
          </div>
          <div className="field">
            <label>现金比例</label>
            <input
              value={settings.cash_target_ratio || ""}
              onChange={(e) => setSettings({ ...settings, cash_target_ratio: e.target.value })}
            />
          </div>
          <div className="field">
            <label>分批次数</label>
            <input
              value={settings.dca_batches || ""}
              onChange={(e) => setSettings({ ...settings, dca_batches: e.target.value })}
            />
          </div>
          <button onClick={saveSettings}>保存设置</button>
        </div>

        <div className="card">
          <h3>聊天提示词</h3>
          <div className="field">
            <label>提示词内容</label>
            <textarea
              rows={8}
              value={promptText}
              onChange={(e) => setPromptText(e.target.value)}
            />
          </div>
          <button onClick={savePrompt}>保存提示词</button>
        </div>
      </section>
    </div>
  );
}
