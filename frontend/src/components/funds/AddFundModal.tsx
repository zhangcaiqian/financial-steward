import { useEffect, useState } from "react";

type AddFundModalProps = {
  open: boolean;
  onClose: () => void;
  onSubmit: (payload: {
    code: string;
    name: string;
    fund_type: string;
    cycle: string;
  }) => Promise<void> | void;
  title?: string;
  submitLabel?: string;
  initial?: {
    code: string;
    name: string;
    fund_type: string;
    cycle: string;
  };
  readOnlyCode?: boolean;
};

const cycleLabels: Record<string, string> = {
  strong_recovery: "强复苏",
  weak_recovery: "弱复苏",
  weak_recession: "弱衰退",
  strong_recession: "强衰退",
};

const defaultForm = {
  code: "",
  name: "",
  fund_type: "open",
  cycle: "strong_recovery",
};

export default function AddFundModal({
  open,
  onClose,
  onSubmit,
  title = "新增基金",
  submitLabel = "保存",
  initial,
  readOnlyCode = false,
}: AddFundModalProps) {
  const [form, setForm] = useState(defaultForm);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!open) return;
    setForm({ ...defaultForm, ...initial });
  }, [open, initial]);

  if (!open) return null;

  const handleSubmit = async () => {
    if (submitting) return;
    setSubmitting(true);
    try {
      await onSubmit({
        code: form.code,
        name: form.name,
        fund_type: form.fund_type,
        cycle: form.cycle,
      });
      onClose();
      setForm(defaultForm);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="modal-overlay" role="dialog" aria-modal="true">
      <div className="modal">
        <div className="modal-header">
          <h3>{title}</h3>
          <button className="icon-button" onClick={onClose}>
            <i className="fa-solid fa-xmark" />
          </button>
        </div>
        <div className="modal-body">
          <div className="field">
            <label>基金代码</label>
            <input
              value={form.code}
              onChange={(e) => setForm({ ...form, code: e.target.value })}
              disabled={readOnlyCode}
            />
          </div>
          <div className="field">
            <label>基金名称</label>
            <input
              value={form.name}
              onChange={(e) => setForm({ ...form, name: e.target.value })}
            />
          </div>
          <div className="field">
            <label>类型</label>
            <select
              value={form.fund_type}
              onChange={(e) => setForm({ ...form, fund_type: e.target.value })}
            >
              <option value="open">场外基金</option>
              <option value="listed">场内基金</option>
            </select>
          </div>
          <div className="field">
            <label>周期分类</label>
            <select
              value={form.cycle}
              onChange={(e) => setForm({ ...form, cycle: e.target.value })}
            >
              {Object.entries(cycleLabels).map(([key, label]) => (
                <option key={key} value={key}>
                  {label}
                </option>
              ))}
            </select>
          </div>
        </div>
        <div className="modal-actions">
          <button className="secondary" onClick={onClose}>
            取消
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting}
          >
            {submitting ? "处理中..." : submitLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
