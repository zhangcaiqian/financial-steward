type PieSlice = {
  label: string;
  value: number;
  color: string;
};

type PieChartProps = {
  data: PieSlice[];
  size?: number;
  strokeWidth?: number;
};

const DEFAULT_SIZE = 220;

function polarToCartesian(cx: number, cy: number, radius: number, angle: number) {
  const radians = (Math.PI / 180) * angle;
  return {
    x: cx + radius * Math.cos(radians),
    y: cy + radius * Math.sin(radians),
  };
}

function describeArc(cx: number, cy: number, radius: number, startAngle: number, endAngle: number) {
  const start = polarToCartesian(cx, cy, radius, endAngle);
  const end = polarToCartesian(cx, cy, radius, startAngle);
  const largeArcFlag = endAngle - startAngle <= 180 ? "0" : "1";
  return `M ${cx} ${cy} L ${start.x} ${start.y} A ${radius} ${radius} 0 ${largeArcFlag} 0 ${end.x} ${end.y} Z`;
}

export default function PieChart({ data, size = DEFAULT_SIZE }: PieChartProps) {
  const radius = size / 2 - 8;
  const total = data.reduce((sum, item) => sum + item.value, 0);
  let currentAngle = -90;

  return (
    <div className="pie-chart">
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        {data.map((slice) => {
          const sliceAngle = total > 0 ? (slice.value / total) * 360 : 0;
          const startAngle = currentAngle;
          const endAngle = currentAngle + sliceAngle;
          currentAngle = endAngle;
          return (
            <path
              key={slice.label}
              d={describeArc(size / 2, size / 2, radius, startAngle, endAngle)}
              fill={slice.color}
            />
          );
        })}
      </svg>
      <div className="pie-legend">
        {data.map((slice) => (
          <div key={slice.label} className="legend-item">
            <span className="legend-swatch" style={{ background: slice.color }} />
            <span>{slice.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
