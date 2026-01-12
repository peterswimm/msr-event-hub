import React from "react";
import ReactMarkdown from "react-markdown";
import { ChatMessage } from "../types/messages";

type MessageListProps = {
  messages: ChatMessage[];
};

const MessageList = ({ messages }: MessageListProps) => {
  return (
    <div className="message-list">
      {messages.map((msg) => (
        <div key={msg.id} className={`message-card ${msg.role}`}>
          {msg.role === "assistant" ? (
            <div className="answer-markdown">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
          ) : (
            <div>{msg.content}</div>
          )}
        </div>
      ))}
    </div>
  );
};

export default MessageList;
