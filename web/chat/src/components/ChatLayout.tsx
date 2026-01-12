import { PropsWithChildren, ReactNode } from "react";

type ChatLayoutProps = PropsWithChildren<{
  header?: ReactNode;
  footer?: ReactNode;
}>;

const ChatLayout = ({ header, footer, children }: ChatLayoutProps) => {
  return (
    <div className="chat-shell">
      {header ? <header className="chat-header">{header}</header> : null}
      <main className="chat-main">{children}</main>
      {footer ? <footer className="chat-footer">{footer}</footer> : null}
    </div>
  );
};

export default ChatLayout;
