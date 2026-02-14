import { useEffect, useState } from "react";
import { fetchCycleTargets, updateCycleTargets } from "../services/portfolio";

const labels: Record<string, string> = {
  strong_recovery: "强复苏",
  weak_recovery: "弱复苏",
  weak_recession: "弱衰退",
  strong_recession: "强衰退",
};

export default function CycleTargets() {
  const [targets, setTargets] = useState<Record<string, string>>({});

  const load = async () => {
    const data = await fetchCycleTargets();
    const formatted: Record<string, string> = {};
    Object.entries(data).forEach(([key, value]) => {
      formatted[key] = (value * 100).toFixed(2);
    });
    setTargets(formatted);
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    const payload: Record<string, number> = {};
    Object.entries(targets).forEach(([key, value]) => {
      payload[key] = Number(value) / 100;
    });
    await updateCycleTargets(payload);
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>周期目标权重</h1>
          <p>调整四大周期的目标权重。</p>
        </div>
      </div>

      <div className="card">
        {Object.entries(targets).map(([key, value]) => (
          <div className="field" key={key}>
            <label>{labels[key] || key} (%)</label>
            <input value={value} onChange={(e) => setTargets({ ...targets, [key]: e.target.value })} />
          </div>
        ))}
        <button onClick={() => void save()}>保存权重</button>
      </div>
    </div>
  );
}
