type ToggleFilterGroupProps = {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (option: string) => void;
  summary?: string;
  onSelectAll?: () => void;
  onClear?: () => void;
};

export function ToggleFilterGroup({
  label,
  options,
  selected,
  onToggle,
  summary,
  onSelectAll,
  onClear,
}: ToggleFilterGroupProps) {
  if (options.length === 0) {
    return null;
  }

  return (
    <section className="control-group">
      <div className="toggle-group__header">
        <div>
          <span className="control-group__label">{label}</span>
          {summary ? <p className="toggle-group__summary">{summary}</p> : null}
        </div>
        {onSelectAll || onClear ? (
          <div className="toggle-group__actions">
            {onSelectAll ? (
              <button type="button" className="toggle-group__action" onClick={onSelectAll}>
                All
              </button>
            ) : null}
            {onClear ? (
              <button type="button" className="toggle-group__action" onClick={onClear}>
                Clear
              </button>
            ) : null}
          </div>
        ) : null}
      </div>
      <div className="toggle-grid">
        {options.map((option) => {
          const isActive = selected.includes(option);
          return (
            <button
              key={option}
              type="button"
              className={`toggle-chip ${isActive ? 'toggle-chip--active' : ''}`}
              aria-pressed={isActive}
              onClick={() => onToggle(option)}
            >
              {option}
            </button>
          );
        })}
      </div>
    </section>
  );
}
