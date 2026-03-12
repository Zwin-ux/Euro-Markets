import type { ReactNode } from 'react';

type TableColumn = {
  key: string;
  label: string;
  align?: 'left' | 'right';
};

type DataRow = Record<string, ReactNode>;

type DataTableProps = {
  columns: TableColumn[];
  rows: DataRow[];
  emptyMessage?: string;
};

export function DataTable({ columns, rows, emptyMessage = 'No data available.' }: DataTableProps) {
  if (rows.length === 0) {
    return <div className="panel-empty">{emptyMessage}</div>;
  }

  return (
    <div className="table-wrap">
      <table className="data-table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key} className={column.align === 'right' ? 'align-right' : undefined}>
                {column.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={`${index}-${String(row[columns[0].key])}`}>
              {columns.map((column) => (
                <td key={column.key} className={column.align === 'right' ? 'align-right' : undefined}>
                  {row[column.key]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
