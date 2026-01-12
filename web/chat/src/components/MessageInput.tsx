import { Button, Textarea } from "@fluentui/react-components";
import { Mic24Regular, Send32Regular, SpeakerMute24Regular, Broom16Regular, Info16Regular } from "@fluentui/react-icons";
import { useCallback, useState } from "react";

type MessageInputProps = {
  onSend: (text: string) => void;
  onClear?: () => void;
  disabled?: boolean;
  disclaimer?: string;
};

const MessageInput = ({ onSend, onClear, disabled = false, disclaimer }: MessageInputProps) => {
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
    <div className="message-input-container">
      <div className="message-input-toolbar">
        <Button
          appearance="subtle"
          icon={<SpeakerMute24Regular />}
          disabled={disabled}
          onClick={() => setIsMuted(!isMuted)}
          aria-label={isMuted ? "Unmute" : "Mute"}
          title={isMuted ? "Unmute" : "Mute"}
        />
      </div>
      <div className="message-input-wrapper">
        <div className="message-input-left">
          <Button
            appearance="subtle"
            icon={<Broom16Regular />}
            disabled={disabled}
            onClick={onClear}
            aria-label="clear chat button"
          />
        </div>
        <div className="message-input">
          <Textarea
            className="message-field"
            value={value}
            onChange={(e, data) => setValue(data.value)}
            onKeyDown={handleKeyDown}
            disabled={disabled}
            placeholder="Type a new question..."
            resize="vertical"
            rows={5}
          />
          <div className="message-actions">
            <Button
              appearance="subtle"
              icon={<Mic24Regular />}
              disabled={disabled}
              title="Start recording"
              aria-label="Start recording"
            />
            <Button
              appearance="subtle"
              icon={<Send32Regular />}
              disabled={disabled || !value.trim()}
              onClick={handleSend}
              aria-label="Ask question button"
            />
          </div>
        </div>
      </div>
      <div className="message-input-footer">
        {disclaimer ? (
          <div className="input-disclaimer">
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
