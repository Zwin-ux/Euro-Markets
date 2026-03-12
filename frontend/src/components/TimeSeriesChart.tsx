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
            <CartesianGrid stroke="rgba(113, 147, 122, 0.18)" vertical={false} />
            <XAxis
              dataKey={xKey}
              tickFormatter={(value) => formatDateLabel(String(value))}
              tick={{ fill: '#8fa593', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(113, 147, 122, 0.18)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#8fa593', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(113, 147, 122, 0.18)' }}
              tickLine={false}
              width={80}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0b1510',
                border: '1px solid rgba(113, 147, 122, 0.28)',
                borderRadius: '14px',
              }}
              labelFormatter={(value) => formatDateLabel(String(value))}
              formatter={(value, _name, item) =>
                formatTooltipValue(Number(value), series.find((entry) => entry.key === item.dataKey)?.valueType)
              }
            />
            <Legend wrapperStyle={{ color: '#d9e6db', fontSize: 12 }} />
            {series.map((entry) => (
              <Line
                key={entry.key}
                type="monotone"
                dataKey={entry.key}
                name={entry.label}
                stroke={entry.color}
                strokeWidth={2.6}
                dot={false}
                activeDot={{ r: 5 }}
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
