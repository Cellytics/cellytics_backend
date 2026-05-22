/**
 * SIMPLE ATTENDANCE CHART COMPONENT
 * 
 * Displays attendance trend as a basic bar chart.
 * Uses CSS/Tailwind for simplicity (no external charting library yet).
 * 
 * Usage:
 *   <AttendanceChart
 *     data={[
 *       { week: "Week 1", active_members: 150, first_timers: 12 },
 *       { week: "Week 2", active_members: 165, first_timers: 18 }
 *     ]}
 *   />
 */

interface ChartDataPoint {
  week: string;
  active_members: number;
  first_timers: number;
}

interface AttendanceChartProps {
  data: ChartDataPoint[];
  title?: string;
}

export function AttendanceChart({ data, title = 'Zone Attendance Trend' }: AttendanceChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="font-bold text-lg text-navy mb-4">{title}</h3>
        <p className="text-gray-600 text-center py-12">No data available</p>
      </div>
    );
  }

  // Find max value for scaling
  const maxValue = Math.max(
    ...data.flatMap((d) => [d.active_members, d.first_timers])
  );

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <h3 className="font-bold text-lg text-navy mb-6">{title}</h3>

      {/* Legend */}
      <div className="flex gap-6 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-navy rounded"></div>
          <span className="text-sm text-gray-700">Active Members</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-gold rounded"></div>
          <span className="text-sm text-gray-700">First Timers</span>
        </div>
      </div>

      {/* Chart */}
      <div className="space-y-6">
        {data.map((point, idx) => (
          <div key={idx}>
            {/* Week label */}
            <p className="text-sm text-gray-600 mb-2 font-medium">{point.week}</p>

            {/* Bars container */}
            <div className="flex gap-4">
              {/* Active Members Bar */}
              <div className="flex-1">
                <div className="h-6 bg-gray-200 rounded overflow-hidden">
                  <div
                    className="h-full bg-navy transition-all"
                    style={{
                      width: `${(point.active_members / maxValue) * 100}%`,
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-700 mt-1">
                  {point.active_members.toLocaleString()}
                </p>
              </div>

              {/* First Timers Bar */}
              <div className="flex-1">
                <div className="h-6 bg-gray-200 rounded overflow-hidden">
                  <div
                    className="h-full bg-gold transition-all"
                    style={{
                      width: `${(point.first_timers / maxValue) * 100}%`,
                    }}
                  ></div>
                </div>
                <p className="text-xs text-gray-700 mt-1">
                  {point.first_timers.toLocaleString()}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Footer stats */}
      <div className="mt-6 pt-4 border-t border-gray-200 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-gray-600">Total Active Members</p>
          <p className="text-lg font-bold text-navy">
            {data.reduce((sum, d) => sum + d.active_members, 0).toLocaleString()}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Total First Timers</p>
          <p className="text-lg font-bold text-gold">
            {data.reduce((sum, d) => sum + d.first_timers, 0).toLocaleString()}
          </p>
        </div>
      </div>
    </div>
  );
}
