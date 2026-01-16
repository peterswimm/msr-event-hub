import { Button, Link, makeStyles, tokens, shorthands } from "@fluentui/react-components";
import { PersonFeedback16Regular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";

const useStyles = makeStyles({
  header: {
    display: "flex",
    alignItems: "center",
    justifyContent: "space-between",
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    ...shorthands.gap(tokens.spacingHorizontalM),
    backgroundColor: "transparent",
    maxWidth: "800px",
    width: "100%",
    marginLeft: "auto",
    marginRight: "auto",
  },
  hamburger: {
    display: "flex",
  },
  actions: {
    display: "flex",
    ...shorthands.gap(tokens.spacingHorizontalS),
  },
});

type BrandHeaderProps = {
  title: string;
  feedbackUrl?: string;
  onStop?: () => void;
  isStreaming?: boolean;
  hamburgerMenu?: React.ReactNode;
};

const BrandHeader = ({ title, feedbackUrl, onStop, isStreaming, hamburgerMenu }: BrandHeaderProps) => {
  const styles = useStyles();
  const [isSmall, setIsSmall] = useState(window.innerWidth < 600);

  useEffect(() => {
    const handler = () => setIsSmall(window.innerWidth < 600);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return (
    <div className={styles.header}>
      <div className={styles.hamburger}>
        {hamburgerMenu}
      </div>
      <div className={styles.actions}>
        {isStreaming ? (
          <Button appearance="secondary" onClick={onStop}>
            Stop
          </Button>
        ) : null}
        {feedbackUrl ? (
          <Link title="Submit feedback" href={feedbackUrl} target="_blank" rel="noreferrer">
            <Button appearance="primary">
              {isSmall ? <PersonFeedback16Regular /> : "Submit feedback"}
            </Button>
          </Link>
        ) : null}
      </div>
    </div>
  );
};

export default BrandHeader;
