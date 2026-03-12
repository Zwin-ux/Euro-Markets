type ToggleFilterGroupProps = {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (option: string) => void;
};

export function ToggleFilterGroup({ label, options, selected, onToggle }: ToggleFilterGroupProps) {
  if (options.length === 0) {
    return null;
  }

  return (
    <section className="control-group">
      <span className="control-group__label">{label}</span>
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
