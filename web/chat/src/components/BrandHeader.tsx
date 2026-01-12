import { Button, Link, Text } from "@fluentui/react-components";
import { PersonFeedback16Regular } from "@fluentui/react-icons";
import { useEffect, useState } from "react";

type BrandHeaderProps = {
  title: string;
  feedbackUrl?: string;
  onStop?: () => void;
  isStreaming?: boolean;
};

const BrandHeader = ({ title, feedbackUrl, onStop, isStreaming }: BrandHeaderProps) => {
  const [isSmall, setIsSmall] = useState(window.innerWidth < 600);

  useEffect(() => {
    const handler = () => setIsSmall(window.innerWidth < 600);
    window.addEventListener("resize", handler);
    return () => window.removeEventListener("resize", handler);
  }, []);

  return (
    <div className="brand-header">
      <div className="brand-left">
        <div className="microsoft-logo">
          <div className="logo-square logo-red"></div>
          <div className="logo-square logo-green"></div>
          <div className="logo-square logo-blue"></div>
          <div className="logo-square logo-yellow"></div>
        </div>
        <span className="microsoft-text">Microsoft</span>
        <span className="brand-divider">|</span>
        <Link href="/">{title}</Link>
      </div>
      <div className="brand-actions">
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
