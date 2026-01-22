import React, { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../types/messages";
import AdaptiveCardRenderer from "./AdaptiveCardRenderer";
import * as AdaptiveCards from "adaptivecards";

type MessageListProps = {
  messages: ChatMessage[];
  onCardAction?: (action: any) => void;
};

type FeedbackButtonsProps = {
  messageId: string;
  query: string;
};

const FeedbackButtons = ({ messageId, query }: FeedbackButtonsProps) => {
  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFeedback = async (feedback: 'positive' | 'negative') => {
    if (isSubmitting) return;
    
    setIsSubmitting(true);
    try {
      const response = await fetch('/api/chat/intent-feedback', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, feedback })
      });
      
      if (response.ok) {
        setFeedbackGiven(true);
      }
    } catch (error) {
      console.error('Failed to submit feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  if (feedbackGiven) {
    return <span className="feedback-thank-you">Thank you for your feedback!</span>;
  }

  return (
    <div className="feedback-buttons">
      <button
        onClick={() => handleFeedback('positive')}
        aria-label="This response was helpful"
        disabled={isSubmitting}
        className="feedback-btn feedback-positive"
      >
        👍
      </button>
      <button
        onClick={() => handleFeedback('negative')}
        aria-label="This response was not helpful"
        disabled={isSubmitting}
        className="feedback-btn feedback-negative"
      >
        👎
      </button>
    </div>
  );
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
      {messages.map((msg, idx) => {
        // Find the user query that this assistant message is responding to
        const userQuery = msg.role === "assistant" && idx > 0 && messages[idx - 1].role === "user"
          ? messages[idx - 1].content
          : "";

        return (
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
                {userQuery && <FeedbackButtons messageId={msg.id} query={userQuery} />}
              </div>
            ) : (
              <div>{msg.content}</div>
            )}
          </div>
        );
      })}
      <div ref={bottomRef} />
    </div>
  );
};

export default MessageList;
