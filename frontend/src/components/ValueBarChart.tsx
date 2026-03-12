import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { formatCurrency } from '../lib/format';

type ValueBarChartProps = {
  title: string;
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKey: string;
  positiveColor?: string;
  negativeColor?: string;
  directional?: boolean;
  height?: number;
};

export function ValueBarChart({
  title,
  data,
  xKey,
  yKey,
  positiveColor = '#7AF0A2',
  negativeColor = '#F08D6A',
  directional = false,
  height = 320,
}: ValueBarChartProps) {
  return (
    <section className="panel chart-panel">
      <div className="panel__header">
        <h3>{title}</h3>
      </div>
      <div className="chart-shell" style={{ height }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data}>
            <CartesianGrid stroke="rgba(113, 147, 122, 0.18)" vertical={false} />
            <XAxis
              dataKey={xKey}
              tick={{ fill: '#8fa593', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(113, 147, 122, 0.18)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#8fa593', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(113, 147, 122, 0.18)' }}
              tickLine={false}
              width={84}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#0b1510',
                border: '1px solid rgba(113, 147, 122, 0.28)',
                borderRadius: '14px',
              }}
              formatter={(value) => formatCurrency(Number(value), { signed: directional })}
            />
            <Bar dataKey={yKey} radius={[8, 8, 0, 0]}>
              {data.map((row, index) => {
                const numericValue = Number(row[yKey]);
                const fill = directional && numericValue < 0 ? negativeColor : positiveColor;
                return <Cell key={`${index}-${String(row[xKey])}`} fill={fill} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
