import { makeStyles, tokens, shorthands } from "@fluentui/react-components";

const useStyles = makeStyles({
  hero: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXXL),
    ...shorthands.padding(tokens.spacingVerticalXXL, tokens.spacingHorizontalXXL),
    maxWidth: "1200px",
    ...shorthands.margin("0", "auto"),
    width: "100%",
  },
  content: {
    textAlign: "center",
  },
  titleLarge: {
    fontSize: tokens.fontSizeHero800,
    fontWeight: tokens.fontWeightBold,
    lineHeight: tokens.lineHeightHero800,
    color: tokens.colorNeutralForeground1,
  },
  subtitle: {
    fontSize: tokens.fontSizeBase400,
    color: tokens.colorNeutralForeground3,
    marginTop: tokens.spacingVerticalM,
  },
  promptInstruction: {
    textAlign: "center",
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase300,
  },
  cards: {
    display: "grid",
    gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
    ...shorthands.gap(tokens.spacingVerticalL, tokens.spacingHorizontalL),
  },
  card: {
    ...shorthands.padding(tokens.spacingVerticalL, tokens.spacingHorizontalL),
    backgroundColor: tokens.colorNeutralBackground1,
    ...shorthands.borderRadius(tokens.borderRadiusLarge),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke2),
    cursor: "pointer",
    transitionProperty: "all",
    transitionDuration: tokens.durationNormal,
    transitionTimingFunction: tokens.curveEasyEase,
    ":hover": {
      ...shorthands.borderColor(tokens.colorBrandStroke1),
      boxShadow: tokens.shadow4,
      transform: "translateY(-2px)",
    },
    ":active": {
      transform: "translateY(0)",
      boxShadow: tokens.shadow2,
    },
    ":focus-visible": {
      ...shorthands.outline("2px", "solid", tokens.colorBrandStroke1),
      outlineOffset: "2px",
    },
  },
  cardTitle: {
    fontSize: tokens.fontSizeBase400,
    fontWeight: tokens.fontWeightSemibold,
    color: tokens.colorNeutralForeground1,
    marginBottom: tokens.spacingVerticalS,
  },
  cardSubtitle: {
    fontSize: tokens.fontSizeBase300,
    color: tokens.colorNeutralForeground3,
  },
  cardDisabled: {
    cursor: "not-allowed",
    opacity: 0.5,
    ":hover": {
      ...shorthands.borderColor(tokens.colorNeutralStroke2),
      boxShadow: "none",
      transform: "none",
    },
  },
});

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
  const styles = useStyles();
  return (
    <section className={styles.hero}>
      <div className={styles.content}>
        <div className={styles.titleLarge}>{heading}</div>
        {subheading ? <div className={styles.subtitle}>{subheading}</div> : null}
      </div>
      {promptInstruction ? (
        <div className={styles.promptInstruction}>
          <em>{promptInstruction}</em>
        </div>
      ) : null}
      <div className={styles.cards}>
        {cards.map((card) => (
          <div
            key={card.title}
            className={`${styles.card} ${disabled ? styles.cardDisabled : ""}`}
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
            <div className={styles.cardTitle}>{card.title}</div>
            {card.subtitle ? <div className={styles.cardSubtitle}>{card.subtitle}</div> : null}
          </div>
        ))}
      </div>
    </section>
  );
};

export default HeroCards;
