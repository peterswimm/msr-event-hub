import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../types/messages";
import AdaptiveCardRenderer from "./AdaptiveCardRenderer";
import * as AdaptiveCards from "adaptivecards";

type MessageListProps = {
  messages: ChatMessage[];
  onCardAction?: (action: any) => void;
};

const MessageList = ({ messages, onCardAction }: MessageListProps) => {
  const listRef = useRef<HTMLDivElement>(null);
  const bottomRef = useRef<HTMLDivElement>(null);

  const handleCardAction = (action: AdaptiveCards.Action) => {
    if (action instanceof AdaptiveCards.SubmitAction) {
      const data = action.data;
      if (onCardAction) {
        onCardAction(data);
      }
    }
  };

  console.log("MessageList rendering with", messages.length, "messages");
  messages.forEach((msg, idx) => {
    console.log(`Message ${idx}:`, {role: msg.role, contentLength: msg.content.length, hasCard: !!msg.adaptive_card});
  });

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    // Prefer scrolling the bottom anchor to ensure focus moves
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
    // Also set container scroll to bottom for good measure
    const el = listRef.current;
    if (el) {
      el.scrollTop = el.scrollHeight;
    }
  }, [messages]);

  return (
    <div className="message-list" ref={listRef}>
      {messages.map((msg) => (
        <div key={msg.id} className={`message-card ${msg.role}`}>
          {msg.role === "assistant" ? (
            <div className="answer-markdown">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
              {msg.adaptive_card && (
                <AdaptiveCardRenderer 
                  card={msg.adaptive_card} 
                  onAction={handleCardAction}
                />
              )}
            </div>
          ) : (
            <div>{msg.content}</div>
          )}
        </div>
      ))}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
