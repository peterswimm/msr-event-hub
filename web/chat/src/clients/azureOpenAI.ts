import { ChatMessage } from "../types/messages";

export type AzureOpenAIStreamParams = {
  endpoint: string;
  deployment: string;
  apiVersion: string;
  apiKey: string;
  messages: ChatMessage[];
  signal?: AbortSignal;
  temperature?: number;
  maxTokens?: number;
};

// Streams chat completions from Azure OpenAI using the Chat Completions API with stream=true.
export async function* streamChatCompletion({
  endpoint,
  deployment,
  apiVersion,
  apiKey,
  messages,
  signal,
  temperature = 0.3,
  maxTokens = 400
}: AzureOpenAIStreamParams): AsyncGenerator<string, void, unknown> {
  const url = `${endpoint}/openai/deployments/${deployment}/chat/completions?api-version=${apiVersion}`;

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "api-key": apiKey
    },
    body: JSON.stringify({
      messages: messages.map(({ role, content }) => ({ role, content })),
      temperature,
      max_tokens: maxTokens,
      stream: true
    }),
    signal
  });

  if (!response.ok || !response.body) {
    const detail = await safeReadError(response);
    throw new Error(`Azure OpenAI request failed: ${response.status} ${response.statusText} ${detail}`.trim());
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
      if (payload === "[DONE]") {
        return;
      }
      try {
        const json = JSON.parse(payload);
        const delta: string = json?.choices?.[0]?.delta?.content ?? "";
        if (delta) {
          yield delta;
        }
      } catch (err) {
        console.warn("Failed to parse stream chunk", err);
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
