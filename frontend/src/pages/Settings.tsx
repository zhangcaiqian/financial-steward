import { useEffect, useState } from "react";
import { fetchSettings, updateSettings } from "../services/portfolio";
import type { Settings as SettingsType } from "../types";

export default function Settings() {
  const [settings, setSettings] = useState<SettingsType | null>(null);

  const load = async () => {
    const data = await fetchSettings();
    setSettings(data);
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    if (!settings) return;
    await updateSettings({
      rebalance_frequency_days: Number(settings.rebalance_frequency_days),
      rebalance_threshold_ratio: Number(settings.rebalance_threshold_ratio),
      cash_target_ratio: Number(settings.cash_target_ratio),
      dca_batches: Number(settings.dca_batches),
    });
  };

  if (!settings) {
    return (
      <div className="page">
        <p>加载中...</p>
      </div>
    );
  }

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1>组合参数设置</h1>
          <p>配置调仓频率、偏离阈值和分批次数。</p>
        </div>
      </div>

      <div className="card">
        <div className="field">
          <label>调仓频率（天）</label>
          <input
            value={settings.rebalance_frequency_days}
            onChange={(e) =>
              setSettings({ ...settings, rebalance_frequency_days: Number(e.target.value) })
            }
          />
        </div>
        <div className="field">
          <label>偏离阈值</label>
          <input
            value={settings.rebalance_threshold_ratio}
            onChange={(e) =>
              setSettings({ ...settings, rebalance_threshold_ratio: Number(e.target.value) })
            }
          />
        </div>
        <div className="field">
          <label>现金比例</label>
          <input
            value={settings.cash_target_ratio}
            onChange={(e) =>
              setSettings({ ...settings, cash_target_ratio: Number(e.target.value) })
            }
          />
        </div>
        <div className="field">
          <label>分批次数</label>
          <input
            value={settings.dca_batches}
            onChange={(e) =>
              setSettings({ ...settings, dca_batches: Number(e.target.value) })
            }
          />
        </div>
        <button onClick={() => void save()}>保存设置</button>
      </div>
    </div>
  );
}
