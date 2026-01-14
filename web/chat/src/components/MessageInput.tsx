import { Button, Textarea, Toolbar, ToolbarButton, makeStyles, tokens, shorthands } from "@fluentui/react-components";
import { Mic24Regular, Send24Regular, SpeakerMute24Regular, Broom16Regular, Info16Regular } from "@fluentui/react-icons";
import { useCallback, useState } from "react";

const useStyles = makeStyles({
  container: {
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalS),
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalS),
  },
  inputRow: {
    display: "flex",
    alignItems: "center",
  },
  inputWrapper: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    ...shorthands.gap(tokens.spacingVerticalXS),
    ...shorthands.borderRadius(tokens.borderRadiusMedium),
    ...shorthands.border("1px", "solid", tokens.colorNeutralStroke1),
    ...shorthands.padding(tokens.spacingVerticalS, tokens.spacingHorizontalS),
  },
  textarea: {
    ...shorthands.border("none"),
    backgroundColor: "transparent",
  },
  actionsRow: {
    display: "flex",
    justifyContent: "flex-end",
    alignItems: "center",
    ...shorthands.gap(tokens.spacingHorizontalXS),
  },
  footer: {
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  disclaimer: {
    color: tokens.colorNeutralForeground3,
    fontSize: tokens.fontSizeBase200,
  },
});

type MessageInputProps = {
  onSend: (text: string) => void;
  onClear?: () => void;
  disabled?: boolean;
  disclaimer?: string;
};

const MessageInput = ({ onSend, onClear, disabled = false, disclaimer }: MessageInputProps) => {
  const styles = useStyles();
  const [value, setValue] = useState("");
  const [isMuted, setIsMuted] = useState(true);

  const handleSend = useCallback(() => {
    const text = value.trim();
    if (!text) return;
    onSend(text);
    setValue("");
  }, [onSend, value]);

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.inputRow}>
        <div className={styles.inputWrapper}>
          <Textarea
            id="chat-input"
            name="chat-message"
            className={styles.textarea}
            value={value}
            onChange={(e, data) => setValue(data.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Type a new question..."
            resize="none"
            rows={3}
            autoComplete="off"
          />
          <div className={styles.actionsRow}>
            <Toolbar aria-label="Chat actions" className={styles.actionsRow}>
              <ToolbarButton
                appearance="subtle"
                icon={<SpeakerMute24Regular />}
                disabled={disabled}
                onClick={() => setIsMuted(!isMuted)}
                aria-label={isMuted ? "Unmute" : "Mute"}
                title={isMuted ? "Unmute" : "Mute"}
              />
              <ToolbarButton
                appearance="subtle"
                icon={<Broom16Regular />}
                disabled={disabled}
                onClick={onClear}
                aria-label="Clear chat"
                title="Clear chat"
              />
              <ToolbarButton
                appearance="subtle"
                icon={<Mic24Regular />}
                disabled={disabled}
                title="Start recording"
                aria-label="Start recording"
              />
              <ToolbarButton
                appearance="subtle"
                icon={<Send24Regular />}
                disabled={disabled || !value.trim()}
                onClick={handleSend}
                aria-label="Send message"
                title="Send"
              />
            </Toolbar>
          </div>
        </div>
      </div>
      <div className={styles.footer}>
        {disclaimer ? (
          <div className={styles.disclaimer}>
            <em>{disclaimer}</em>
          </div>
        ) : null}
        <Button
          appearance="subtle"
          icon={<Info16Regular />}
          title="About"
        />
      </div>
    </div>
  );
};

export default MessageInput;
