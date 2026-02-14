import ReactECharts from "echarts-for-react";

type EChartProps = {
  option: Record<string, any>;
  height?: number;
};

export default function EChart({ option, height = 280 }: EChartProps) {
  return <ReactECharts option={option} style={{ height }} />;
}
