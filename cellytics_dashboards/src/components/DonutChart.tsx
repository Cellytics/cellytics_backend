/**
 * SIMPLE DONUT CHART COMPONENT
 * 
 * Displays data as a donut chart with a center label.
 * Uses SVG for simplicity (no external charting library).
 * 
 * Usage:
 *   <DonutChart
 *     data={[
 *       { label: "First Timers", value: 45, color: "#3B82F6" },
 *       { label: "Souls Won", value: 55, color: "#10B981" }
 *     ]}
 *     centerLabel="Total"
 *     centerValue="100"
 *   />
 */

interface DonutDataPoint {
  label: string;
  value: number;
  color?: string;
}

interface DonutChartProps {
  data: DonutDataPoint[];
  centerLabel?: string;
  centerValue?: string;
  title?: string;
}

export function DonutChart({
  data,
  centerLabel = '',
  centerValue = '',
  title,
}: DonutChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="rounded-lg border border-gray-200 bg-white px-6 py-5 shadow-sm">
        {title && <h2 className="mb-4 font-serif text-base text-navy">{title}</h2>}
        <p className="text-center text-sm text-slate-500">No data available</p>
      </div>
    );
  }

  const total = data.reduce((sum, item) => sum + item.value, 0);
  const defaultColors = ['#1E3A8A', '#F59E0B', '#10B981', '#EF4444', '#6366F1'];

  // Calculate SVG paths for donut
  let currentAngle = -Math.PI / 2;
  const slices = data.map((item, index) => {
    const sliceAngle = (item.value / total) * 2 * Math.PI;
    const startAngle = currentAngle;
    const endAngle = currentAngle + sliceAngle;
    currentAngle = endAngle;

    const radius = 60;
    const innerRadius = 40;

    const x1 = 100 + radius * Math.cos(startAngle);
    const y1 = 100 + radius * Math.sin(startAngle);
    const x2 = 100 + radius * Math.cos(endAngle);
    const y2 = 100 + radius * Math.sin(endAngle);

    const ix1 = 100 + innerRadius * Math.cos(startAngle);
    const iy1 = 100 + innerRadius * Math.sin(startAngle);
    const ix2 = 100 + innerRadius * Math.cos(endAngle);
    const iy2 = 100 + innerRadius * Math.sin(endAngle);

    const largeArc = sliceAngle > Math.PI ? 1 : 0;

    const path = `
      M ${ix1} ${iy1}
      L ${x1} ${y1}
      A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}
      L ${ix2} ${iy2}
      A ${innerRadius} ${innerRadius} 0 ${largeArc} 0 ${ix1} ${iy1}
      Z
    `;

    return {
      path,
      color: item.color || defaultColors[index % defaultColors.length],
      label: item.label,
      value: item.value,
      percentage: ((item.value / total) * 100).toFixed(1),
    };
  });

  return (
    <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="px-6 py-5">
        {title && <h2 className="mb-4 font-serif text-base text-navy">{title}</h2>}
        <div className="flex flex-col items-center gap-6 lg:flex-row">
          {/* Donut Chart */}
          <div className="flex-shrink-0">
            <svg viewBox="0 0 200 200" className="h-40 w-40">
              {slices.map((slice, index) => (
                <path
                  key={index}
                  d={slice.path}
                  fill={slice.color}
                  opacity="0.85"
                  style={{ transition: 'opacity 0.3s' }}
                />
              ))}
              {/* Center text */}
              {centerValue && (
                <>
                  <text
                    x="100"
                    y="95"
                    textAnchor="middle"
                    fontSize="24"
                    fontWeight="bold"
                    fill="#1E3A8A"
                  >
                    {centerValue}
                  </text>
                  {centerLabel && (
                    <text
                      x="100"
                      y="115"
                      textAnchor="middle"
                      fontSize="12"
                      fill="#64748B"
                    >
                      {centerLabel}
                    </text>
                  )}
                </>
              )}
            </svg>
          </div>

          {/* Legend */}
          <div className="flex-1 space-y-3">
            {slices.map((slice, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div
                    className="h-3 w-3 rounded-full"
                    style={{ backgroundColor: slice.color }}
                  />
                  <span className="text-sm font-medium text-slate-700">
                    {slice.label}
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-bold text-navy">{slice.value.toLocaleString()}</p>
                  <p className="text-xs text-slate-500">{slice.percentage}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
