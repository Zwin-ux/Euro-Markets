type SectionTitleProps = {
  title: string;
  description: string;
  eyebrow?: string;
  command?: string;
};

export function SectionTitle({ title, description, eyebrow, command }: SectionTitleProps) {
  return (
    <header className="section-title">
      {eyebrow ? <span className="section-title__eyebrow">{eyebrow}</span> : null}
      {command ? <code className="section-title__command">$ {command}</code> : null}
      <h2>{title}</h2>
      <p>{description}</p>
    </header>
  );
}
