import { PropsWithChildren, ReactNode } from "react";
import { makeStyles, tokens, shorthands } from "@fluentui/react-components";

const useStyles = makeStyles({
  shell: {
    minHeight: "100vh",
    display: "flex",
    flexDirection: "column",
    padding: 0,
    backgroundColor: tokens.colorNeutralBackground3,
  },
  header: {
    backgroundColor: tokens.colorNeutralBackground3,
    position: "sticky",
    top: 0,
    zIndex: 100,
  },
  main: {
    flex: 1,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    paddingBottom: "80px",
    maxWidth: "800px",
    width: "100%",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding(0, tokens.spacingHorizontalL),
  },
  footer: {
    backgroundColor: tokens.colorNeutralBackground3,
    position: "sticky",
    bottom: 0,
    zIndex: 100,
    maxWidth: "800px",
    width: "100%",
    marginLeft: "auto",
    marginRight: "auto",
    ...shorthands.padding(0, tokens.spacingHorizontalL),
  },
});

type ChatLayoutProps = PropsWithChildren<{
  header?: ReactNode;
  footer?: ReactNode;
}>;

const ChatLayout = ({ header, footer, children }: ChatLayoutProps) => {
  const styles = useStyles();
  return (
    <div className={styles.shell}>
      {header ? <header className={styles.header}>{header}</header> : null}
      <main className={styles.main}>{children}</main>
      {footer ? <footer className={styles.footer}>{footer}</footer> : null}
    </div>
  );
};

export default ChatLayout;
