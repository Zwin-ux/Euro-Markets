import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ReferenceLine,
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
            <CartesianGrid stroke="rgba(182, 255, 199, 0.14)" strokeDasharray="4 6" vertical={false} />
            <XAxis
              dataKey={xKey}
              tick={{ fill: '#b6ffc7', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(182, 255, 199, 0.14)' }}
              tickLine={false}
            />
            <YAxis
              tick={{ fill: '#b6ffc7', fontSize: 12 }}
              axisLine={{ stroke: 'rgba(182, 255, 199, 0.14)' }}
              tickLine={false}
              width={84}
            />
            {directional ? <ReferenceLine y={0} stroke="rgba(240, 201, 114, 0.4)" strokeDasharray="5 5" /> : null}
            <Tooltip
              contentStyle={{
                backgroundColor: '#08110b',
                border: '1px solid rgba(182, 255, 199, 0.24)',
                borderRadius: '8px',
                boxShadow: '0 12px 28px rgba(0, 0, 0, 0.32)',
              }}
              formatter={(value) => formatCurrency(Number(value), { signed: directional })}
            />
            <Bar dataKey={yKey} radius={[2, 2, 0, 0]} barSize={26}>
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
