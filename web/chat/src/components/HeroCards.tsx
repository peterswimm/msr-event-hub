type HeroCard = {
  title: string;
  subtitle?: string;
  prompt: string;
};

type HeroCardsProps = {
  heading: string;
  subheading?: string;
  promptInstruction?: string;
  cards: HeroCard[];
  onPick: (prompt: string) => void;
  disabled?: boolean;
};

const HeroCards = ({ heading, subheading, promptInstruction, cards, onPick, disabled }: HeroCardsProps) => {
  return (
    <section className="hero">
      <div className="hero-content">
        <div className="title-large">{heading}</div>
        {subheading ? <div className="subtitle">{subheading}</div> : null}
      </div>
      {promptInstruction ? (
        <div className="prompt-instruction">
          <em>{promptInstruction}</em>
        </div>
      ) : null}
      <div className="hero-cards">
        {cards.map((card) => (
          <div
            key={card.title}
            className="hero-card"
            role="button"
            tabIndex={0}
            onClick={() => !disabled && onPick(card.prompt)}
            onKeyDown={(e) => {
              if (!disabled && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                onPick(card.prompt);
              }
            }}
          >
            <div className="hero-card-title">{card.title}</div>
            {card.subtitle ? <div className="hero-card-subtitle">{card.subtitle}</div> : null}
          </div>
        ))}
      </div>
    </section>
  );
};

export default HeroCards;
