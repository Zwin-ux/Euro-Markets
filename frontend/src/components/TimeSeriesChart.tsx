import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { formatCurrency, formatDateLabel, formatPercent } from '../lib/format';

type Series = {
  key: string;
  label: string;
  color: string;
  valueType?: 'currency' | 'percent' | 'number';
};

type TimeSeriesChartProps = {
  title: string;
  data: Array<Record<string, string | number>>;
  xKey: string;
  series: Series[];
  height?: number;
};

function formatTooltipValue(value: number, valueType: Series['valueType']) {
  if (valueType === 'currency') {
    return formatCurrency(value);
  }
  if (valueType === 'percent') {
    return formatPercent(value);
  }
  return value.toLocaleString('en-US');
}

export function TimeSeriesChart({ title, data, xKey, series, height = 320 }: TimeSeriesChartProps) {
  return (
    <section className="panel chart-panel">
      <div className="panel__header">
        <h3>{title}</h3>
      </div>
      <div className="chart-shell" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="rgba(182, 255, 199, 0.14)" strokeDasharray="4 6" vertical={false} />
            <XAxis
              dataKey={xKey}
              tickFormatter={(value) => formatDateLabel(String(value))}
              tick={{ fill: '#b6ffc7', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(182, 255, 199, 0.14)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#b6ffc7', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(182, 255, 199, 0.14)' }}
              tickLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#08110b',
                border: '1px solid rgba(182, 255, 199, 0.24)',
                borderRadius: '8px',
                boxShadow: '0 12px 28px rgba(0, 0, 0, 0.32)',
              }}
              labelFormatter={(value) => formatDateLabel(String(value))}
              formatter={(value, _name, item) =>
                formatTooltipValue(Number(value), series.find((entry) => entry.key === item.dataKey)?.valueType)
              }
            />
            <Legend wrapperStyle={{ color: '#d9e6db', fontSize: 11, letterSpacing: '0.08em', textTransform: 'uppercase' }} />
            {series.map((entry) => (
              <Line
                key={entry.key}
                type="monotone"
                dataKey={entry.key}
                name={entry.label}
                stroke={entry.color}
                strokeWidth={2.3}
                dot={false}
                activeDot={{ r: 5, stroke: '#f3faf0', strokeWidth: 1.5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
