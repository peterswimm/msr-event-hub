import { ChatMessage } from "../types/messages";

type HubChatParams = {
  baseUrl: string;
  messages: ChatMessage[];
  signal?: AbortSignal;
};

type StreamPayload = {
  delta?: string;
  adaptive_card?: any;
  context?: any;
};

// Streams chat responses from the hub backend, which should authenticate with Azure OpenAI using managed identity.
export async function* streamHubChat({ baseUrl, messages, signal }: HubChatParams): AsyncGenerator<StreamPayload, void, unknown> {
  const url = `${baseUrl.replace(/\/$/, "")}/chat/stream`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ messages }),
    signal
  });

  if (!response.ok || !response.body) {
    const detail = await safeReadError(response);
    throw new Error(`Hub chat request failed: ${response.status} ${response.statusText} ${detail}`.trim());
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const raw of lines) {
      const line = raw.trim();
      if (!line || !line.startsWith("data:")) continue;
      const payload = line.replace(/^data:\s*/, "");
      if (payload === "[DONE]") return;
      try {
        const json: StreamPayload = JSON.parse(payload);
        // Yield the full payload object (includes delta, adaptive_card, context)
        yield json;
      } catch (err) {
        console.warn("Failed to parse hub stream chunk", err);
      }
    }
  }
}

async function safeReadError(response: Response): Promise<string> {
  try {
    const text = await response.text();
    return text ? `- ${text}` : "";
  } catch (err) {
    return "";
  }
}
