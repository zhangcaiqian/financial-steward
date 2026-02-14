import { useEffect, useState } from "react";
import { createFund, fetchFunds, updateFund } from "../services/portfolio";
import type { Fund } from "../types";
import AddFundModal from "../components/funds/AddFundModal";

const cycleLabels: Record<string, string> = {
  strong_recovery: "强复苏",
  weak_recovery: "弱复苏",
  weak_recession: "弱衰退",
  strong_recession: "强衰退",
};

const fundTypeLabels: Record<string, string> = {
  open: "场外基金",
  listed: "场内基金",
  etf: "场内基金",
};

export default function Funds() {
  const [funds, setFunds] = useState<Fund[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [editingFund, setEditingFund] = useState<Fund | null>(null);

  const load = async () => {
    const data = await fetchFunds();
    setFunds(data);
  };

  useEffect(() => {
    void load();
  }, []);

  const submit = async (payload: {
    code: string;
    name: string;
    fund_type: string;
    cycle: string;
  }) => {
    await createFund({
      code: payload.code,
      name: payload.name,
      fund_type: payload.fund_type,
      cycle_weights: { [payload.cycle]: 1 },
    });
    await load();
  };

  const submitEdit = async (payload: {
    code: string;
    name: string;
    fund_type: string;
    cycle: string;
  }) => {
    if (!editingFund) return;
    await updateFund(editingFund.id, {
      name: payload.name,
      fund_type: payload.fund_type,
      cycle_weights: { [payload.cycle]: 1 },
    });
    setEditingFund(null);
    await load();
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>基金管理</h1>
          <p>按周期分类维护你的基金清单。</p>
        </div>
        <button onClick={() => setModalOpen(true)}>
          <i className="fa-solid fa-plus" /> 添加基金
        </button>
      </div>

      <div className="card">
        <h3>基金列表</h3>
        {funds.length ? (
          <ul className="list">
            {funds.map((fund) => (
              <li key={fund.id} className="fund-item">
                <div>
                  <div className="fund-title">
                    {fund.name} ({fund.code})
                  </div>
                  <div className="fund-meta">
                    <span className="badge">
                      {fundTypeLabels[fund.fund_type] ?? fund.fund_type}
                    </span>
                    <span className="badge badge-cycle">
                      {fund.primary_cycle
                        ? cycleLabels[fund.primary_cycle] || fund.primary_cycle
                        : "未分类"}
                    </span>
                  </div>
                </div>
                <div className="fund-actions">
                  <button className="secondary" onClick={() => setEditingFund(fund)}>
                    <i className="fa-solid fa-pen" /> 编辑
                  </button>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <p>暂无基金</p>
        )}
      </div>

      <AddFundModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onSubmit={submit}
      />

      <AddFundModal
        open={!!editingFund}
        onClose={() => setEditingFund(null)}
        onSubmit={submitEdit}
        title="编辑基金"
        submitLabel="更新"
        readOnlyCode
        initial={{
          code: editingFund?.code ?? "",
          name: editingFund?.name ?? "",
          fund_type: editingFund?.fund_type === "etf" ? "listed" : editingFund?.fund_type ?? "open",
          cycle: editingFund?.primary_cycle ?? "strong_recovery",
        }}
      />
    </div>
  );
}
