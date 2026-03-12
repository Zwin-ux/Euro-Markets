type SectionTitleProps = {
  title: string;
  description: string;
  eyebrow?: string;
};

export function SectionTitle({ title, description, eyebrow }: SectionTitleProps) {
  return (
    <header className="section-title">
      {eyebrow ? <span className="section-title__eyebrow">{eyebrow}</span> : null}
      <h2>{title}</h2>
      <p>{description}</p>
    </header>
  );
}
