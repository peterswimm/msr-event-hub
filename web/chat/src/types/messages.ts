export type ChatRole = "system" | "user" | "assistant";

export type ChatMessage = {
  id: string;
  role: ChatRole;
  content: string;
  adaptive_card?: any; // Adaptive Card JSON payload
};
