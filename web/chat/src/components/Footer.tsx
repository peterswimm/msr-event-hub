import { Caption1Strong, Link, makeStyles, tokens, shorthands } from "@fluentui/react-components";

const useStyles = makeStyles({
  container: {
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    ...shorthands.gap(tokens.spacingHorizontalS),
    ...shorthands.padding(tokens.spacingVerticalM, tokens.spacingHorizontalL),
    flexWrap: "wrap",
  },
  text: {
    color: tokens.colorNeutralForeground3,
  },
});

const Footer = () => {
  const styles = useStyles();
  return (
    <div className={styles.container}>
      <Link href="mailto:mcrinfo@microsoft.com" target="_blank" rel="noreferrer">
        <Caption1Strong className={styles.text}>Contact Us</Caption1Strong>
      </Link>
      <Caption1Strong className={styles.text}>|</Caption1Strong>
      <Link href="https://www.microsoft.com/en-us/legal/terms-of-use" target="_blank" rel="noreferrer">
        <Caption1Strong className={styles.text}>Terms of Use</Caption1Strong>
      </Link>
      <Caption1Strong className={styles.text}>|</Caption1Strong>
      <Link href="https://go.microsoft.com/fwlink/?LinkId=521839" target="_blank" rel="noreferrer">
        <Caption1Strong className={styles.text}>Privacy & Cookies</Caption1Strong>
      </Link>
      <Caption1Strong className={styles.text}>|</Caption1Strong>
      <Caption1Strong className={styles.text}>© {new Date().getFullYear()} Microsoft</Caption1Strong>
    </div>
  );
};

export default Footer;
