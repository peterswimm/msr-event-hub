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
  console.log("[hubChat] Starting stream to:", baseUrl);
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

  console.log("[hubChat] Got response, starting to read body");

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";
  let eventCount = 0;

  try {
    while (true) {
      const { value, done } = await reader.read();
      if (done) {
        console.log("[hubChat] Stream reader done");
        break;
      }

      const chunk = decoder.decode(value, { stream: true });
      buffer += chunk;
      console.log(`[hubChat] Got chunk: ${chunk.length} bytes, buffer now: ${buffer.length} bytes`);
      
      // SSE format is "data: {...}\n" followed by blank line "\n"
      // Split on "\n\n" (blank line after event)
      const parts = buffer.split("\n\n");
      
      // Last part is incomplete, keep in buffer
      buffer = parts.pop() ?? "";
      console.log(`[hubChat] Split into ${parts.length} complete events, buffer remainder: ${buffer.length} bytes`);

      for (const part of parts) {
        const trimmed = part.trim();
        if (!trimmed) continue;
        
        // Extract data content after "data: "
        const match = trimmed.match(/^data:\s*(.*)/s);
        if (!match) {
          console.log("[hubChat] No data: prefix found");
          continue;
        }
        
        const payload = match[1].trim();
        if (payload === "[DONE]") {
          console.log("[hubChat] Received [DONE]");
          return;
        }
        
        try {
          eventCount++;
          const json: StreamPayload = JSON.parse(payload);
          console.log(`[hubChat] Event ${eventCount}:`, { 
            hasCard: !!json.adaptive_card, 
            hasDelta: !!json.delta,
            deltaLen: json.delta?.length || 0
          });
          yield json;
        } catch (err) {
          console.warn("[hubChat] Parse error:", err, "payload:", payload.substring(0, 100));
        }
      }
    }
  } catch (err) {
    console.error("[hubChat] FATAL ERROR:", err);
    throw err;
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
