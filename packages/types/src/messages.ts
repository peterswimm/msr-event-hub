export type ChatRole = "system" | "user" | "assistant";

export type AdaptiveCardPayload = Record<string, any>;

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  adaptive_card?: AdaptiveCardPayload;
  isWelcomeCard?: boolean;
};

export type CardActionData = {
  action?: string;
  projectId?: string;
  researchArea?: string;
  query?: string;
  [key: string]: any;
};

export type StreamChunk =
  | string
  | {
      delta?: string;
      adaptive_card?: AdaptiveCardPayload;
      [key: string]: any;
    };

export type ChatRequest = {
  messages: ChatMessage[];
};

export type ChatResponse = {
  content: string;
  adaptive_card?: AdaptiveCardPayload;
};
