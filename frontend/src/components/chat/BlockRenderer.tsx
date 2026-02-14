import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import EChart from "../charts/EChart";

type BlockProps = {
  blocks?: any[];
  onAction?: (action: string, params?: Record<string, any>) => void;
};

export default function BlockRenderer({ blocks = [], onAction }: BlockProps) {
  return (
    <div className="block-stack">
      {blocks.map((block, index) => {
        switch (block.type) {
          case "text":
            return (
              <div key={index} className="block-text chat-markdown">
                <ReactMarkdown remarkPlugins={[remarkGfm]}>{block.content || ""}</ReactMarkdown>
              </div>
            );
          case "table":
            return <TableBlock key={index} block={block} />;
          case "chart":
            return <ChartBlock key={index} block={block} />;
          case "buttons":
            return <ButtonsBlock key={index} block={block} onAction={onAction} />;
          case "form":
            return <FormBlock key={index} block={block} onAction={onAction} />;
          default:
            return (
              <pre key={index} className="block-text">
                {JSON.stringify(block, null, 2)}
              </pre>
            );
        }
      })}
    </div>
  );
}

function TableBlock({ block }: { block: any }) {
  const columns = block.columns || (block.rows?.[0] ? Object.keys(block.rows[0]) : []);
  const rows = block.rows || [];
  return (
    <table className="table">
      <thead>
        <tr>
          {columns.map((col: string) => (
            <th key={col}>{col}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((row: any, rowIdx: number) => (
          <tr key={rowIdx}>
            {columns.map((col: string, colIdx: number) => (
              <td key={col}>{Array.isArray(row) ? row[colIdx] : row[col]}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function ChartBlock({ block }: { block: any }) {
  const option = buildChartOption(block);
  return <EChart option={option} />;
}

function buildChartOption(block: any) {
  if (block.option) {
    return block.option;
  }
  const type = block.chartType || "line";
  if (type === "pie") {
    return {
      tooltip: { trigger: "item" },
      series: [
        {
          type: "pie",
          radius: ["40%", "70%"],
          data: block.data || [],
          label: { formatter: "{b}: {d}%" },
        },
      ],
    };
  }
  const categories = block.data?.categories || [];
  const series = block.data?.series || [];
  return {
    tooltip: { trigger: "axis" },
    xAxis: { type: "category", data: categories },
    yAxis: { type: "value" },
    series: series.map((item: any) => ({
      ...item,
      type,
      smooth: type === "line",
    })),
  };
}

function ButtonsBlock({
  block,
  onAction,
}: {
  block: any;
  onAction?: (action: string, params?: Record<string, any>) => void;
}) {
  return (
    <div className="actions">
      {(block.actions || []).map((action: any, idx: number) => (
        <button
          key={idx}
          className={action.variant === "secondary" ? "secondary" : ""}
          onClick={() => onAction?.(action.action, action.params)}
        >
          {action.label}
        </button>
      ))}
    </div>
  );
}

function FormBlock({
  block,
  onAction,
}: {
  block: any;
  onAction?: (action: string, params?: Record<string, any>) => void;
}) {
  const [values, setValues] = useState<Record<string, any>>({});
  return (
    <div className="form-block">
      <h4>{block.title}</h4>
      {(block.fields || []).map((field: any) => (
        <div className="field" key={field.name}>
          <label>{field.label}</label>
          <input
            type={field.type || "text"}
            placeholder={field.placeholder}
            value={values[field.name] || ""}
            onChange={(e) => setValues({ ...values, [field.name]: e.target.value })}
          />
        </div>
      ))}
      <button onClick={() => onAction?.(block.action, values)}>
        {block.submitLabel || "提交"}
      </button>
    </div>
  );
}
