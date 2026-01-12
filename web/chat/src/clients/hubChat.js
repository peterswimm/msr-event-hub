// Streams chat responses from the hub backend, which should authenticate with Azure OpenAI using managed identity.
export async function* streamHubChat({ baseUrl, messages, signal }) {
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
        if (done)
            break;
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() ?? "";
        for (const raw of lines) {
            const line = raw.trim();
            if (!line || !line.startsWith("data:"))
                continue;
            const payload = line.replace(/^data:\s*/, "");
            if (payload === "[DONE]")
                return;
            try {
                const json = JSON.parse(payload);
                const delta = json?.delta ?? json?.choices?.[0]?.delta?.content ?? "";
                if (delta) {
                    yield delta;
                }
            }
            catch (err) {
                console.warn("Failed to parse hub stream chunk", err);
            }
        }
    }
}
async function safeReadError(response) {
    try {
        const text = await response.text();
        return text ? `- ${text}` : "";
    }
    catch (err) {
        return "";
    }
}
