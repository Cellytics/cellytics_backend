/**
 * STATS GRID COMPONENT
 * 
 * Displays key metrics in a responsive grid layout.
 * Used by all dashboards to show aggregate statistics.
 * 
 * Usage:
 *   <StatsGrid
 *     stats={[
 *       { label: "Total Fellowships", value: 9, icon: "⛪" },
 *       { label: "Souls Won", value: 245, icon: "✨" }
 *     ]}
 *   />
 */

interface StatItem {
  label: string;
  value: number;
  icon?: string;
  trend?: number; // percentage change (positive = up)
  unit?: string;
}

interface StatsGridProps {
  stats: StatItem[];
  columns?: number;
}

export function StatsGrid({ stats, columns = 4 }: StatsGridProps) {
  const colClass = {
    1: 'grid-cols-1',
    2: 'grid-cols-2',
    3: 'grid-cols-3',
    4: 'grid-cols-4',
  }[columns] || 'grid-cols-4';

  return (
    <div className={`grid ${colClass} gap-6`}>
      {stats.map((stat, idx) => (
        <div
          key={idx}
          className="bg-white rounded-lg shadow-md p-6 border-l-4 border-gold"
        >
          {/* Icon */}
          {stat.icon && <span className="text-3xl mb-2 block">{stat.icon}</span>}

          {/* Value */}
          <div className="flex items-baseline gap-2">
            <span className="text-3xl font-bold text-navy">
              {stat.value.toLocaleString()}
            </span>
            {stat.unit && <span className="text-gray-600">{stat.unit}</span>}
          </div>

          {/* Label */}
          <p className="text-gray-600 text-sm mt-2">{stat.label}</p>

          {/* Trend indicator */}
          {stat.trend !== undefined && (
            <div
              className={`text-xs mt-2 ${
                stat.trend >= 0 ? 'text-forest-green' : 'text-red-alert'
              }`}
            >
              {stat.trend >= 0 ? '↑' : '↓'} {Math.abs(stat.trend)}%
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
