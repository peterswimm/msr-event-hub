import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  Button,
  Spinner,
  Subtitle2,
  Text,
  Title2,
  Tooltip
} from "@fluentui/react-components";
import { Dismiss24Regular, ShieldError24Regular } from "@fluentui/react-icons";
import ChatLayout from "./components/ChatLayout";
import MessageInput from "./components/MessageInput";
import MessageList from "./components/MessageList";
import BrandHeader from "./components/BrandHeader";
import HeroCards from "./components/HeroCards";
import Footer from "./components/Footer";
import { streamChatCompletion } from "./clients/azureOpenAI";
import { streamHubChat } from "./clients/hubChat";
import { ChatMessage } from "./types/messages";

const systemPrompt =
  "You are a helpful assistant for the MSR Event Hub. Keep replies concise and cite sources when available.";

function App() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const config = useMemo(
    () => ({
      endpoint: import.meta.env.VITE_AOAI_ENDPOINT as string | undefined,
      deployment: import.meta.env.VITE_AOAI_DEPLOYMENT as string | undefined,
      apiVersion: (import.meta.env.VITE_AOAI_API_VERSION as string | undefined) ?? "2024-02-15-preview",
      apiKey: import.meta.env.VITE_AOAI_KEY as string | undefined,
      hubApiBase: (import.meta.env.VITE_CHAT_API_BASE as string | undefined) ?? "/api",
      siteTitle: (import.meta.env.VITE_SITE_TITLE as string | undefined) ?? "MSR Red: Redmond Research Showcase copilot",
      frontHeading: (import.meta.env.VITE_FRONTPAGE_HEADING as string | undefined) ?? "Questions about Microsoft Research?",
      frontSubheading:
        (import.meta.env.VITE_FRONTPAGE_SUBHEADING as string | undefined) ??
        "Use this copilot experience to explore MSR's extensive catalog of research contributions: internal and external projects, events, publications, and more.",
      promptInstruction: import.meta.env.VITE_PROMPT_INSTRUCTION as string | undefined,
      aiDisclaimer: import.meta.env.VITE_AI_DISCLAIMER as string | undefined,
      suggestionQuestions:
        (() => {
          try {
            const raw = import.meta.env.VITE_FRONTPAGE_QUESTIONS as string | undefined;
            return raw ? (JSON.parse(raw) as string[]) : [
              "Detail MSR's latest contributions to small language models",
              "What are the top 5 papers from NeurIPS 2023?",
              "What are the key themes in MSR's research?",
            ];
          } catch {
            return [
              "Detail MSR's latest contributions to small language models",
              "What are the top 5 papers from NeurIPS 2023?",
              "What are the key themes in MSR's research?",
            ];
          }
        })(),
    }),
    []
  );

  const prefersHubProxy = Boolean(config.hubApiBase);
  const canStreamDirect = Boolean(config.endpoint && config.deployment && config.apiKey);

  const handleSend = useCallback(
    async (text: string) => {
      if (!text.trim()) return;
      if (!prefersHubProxy && !canStreamDirect) {
        setError("No chat backend configured. Set VITE_CHAT_API_BASE or Azure OpenAI env vars.");
        return;
      }

      const userMessage: ChatMessage = {
        id: crypto.randomUUID(),
        role: "user",
        content: text
      };

      const baseMessages: ChatMessage[] = [
        { id: "system", role: "system", content: systemPrompt },
        ...messages,
        userMessage
      ];

      setMessages((prev: ChatMessage[]) => [...prev, userMessage]);
      setError(null);
      setIsStreaming(true);

      const controller = new AbortController();
      abortRef.current = controller;

      const assistantId = crypto.randomUUID();
      let assistantContent = "";

      try {
        const stream = prefersHubProxy
          ? streamHubChat({
              baseUrl: config.hubApiBase!,
              messages: baseMessages,
              signal: controller.signal
            })
          : streamChatCompletion({
              endpoint: config.endpoint!,
              deployment: config.deployment!,
              apiVersion: config.apiVersion!,
              apiKey: config.apiKey!,
              messages: baseMessages,
              signal: controller.signal
            });

        for await (const delta of stream) {
          assistantContent += delta;
          setMessages((prev: ChatMessage[]) => {
            const next = prev.filter((m: ChatMessage) => m.id !== assistantId);
            return [
              ...next,
              {
                id: assistantId,
                role: "assistant",
                content: assistantContent
              }
            ];
          });
        }
      } catch (err) {
        const fallback = err instanceof Error ? err.message : "Unexpected error";
        setError(fallback);
      } finally {
        setIsStreaming(false);
        abortRef.current = null;
      }
    },
    [canStreamDirect, config.apiKey, config.apiVersion, config.deployment, config.endpoint, config.hubApiBase, messages, prefersHubProxy]
  );

  const handleStop = useCallback(() => {
    abortRef.current?.abort();
  }, []);

  const handleClear = useCallback(() => {
    setMessages([]);
    setError(null);
  }, []);

  return (
    <ChatLayout
      header={<BrandHeader title={config.siteTitle!} feedbackUrl={import.meta.env.VITE_FEEDBACK_URL as string | undefined} onStop={handleStop} isStreaming={isStreaming} />}
      footer={<Footer />}
    >
      {!prefersHubProxy && !canStreamDirect ? (
        <div className="status-card warning">
          <div className="status-title">
            <ShieldError24Regular />
            <Text weight="semibold">Configure chat backend</Text>
          </div>
          <Text size={300}>
            Set VITE_CHAT_API_BASE to route through the hub (managed identity). For local direct calls, also set
            VITE_AOAI_ENDPOINT, VITE_AOAI_DEPLOYMENT, VITE_AOAI_API_VERSION, and VITE_AOAI_KEY.
          </Text>
        </div>
      ) : null}

      {error ? (
        <div className="status-card error">
          <div className="status-title">
            <ShieldError24Regular />
            <Text weight="semibold">{error}</Text>
          </div>
          <Text size={300}>Check your network, credentials, or deployment name.</Text>
        </div>
      ) : null}

      {messages.length === 0 ? (
        <HeroCards
          heading={config.frontHeading!}
          subheading={config.frontSubheading!}
          promptInstruction={config.promptInstruction}
          cards={(import.meta.env.VITE_HERO_CARDS ? JSON.parse(import.meta.env.VITE_HERO_CARDS as string) : undefined) || [
            { title: "Help me find projects that match my interests.", subtitle: "Ask a few questions to get to know me.", prompt: "Help me find projects that match my interests." },
            { title: "Activate Agenda Mode to plan my visit.", subtitle: "Ask a few questions about my interests.", prompt: "Activate Agenda Mode to plan my visit." },
            { title: "Evaluate collaboration opportunities.", subtitle: "Focus on AI and renewable energy.", prompt: "Evaluate the collaboration opportunities between projects focused on artificial intelligence and renewable energy at the showcase." },
          ]}
          onPick={(prompt: string) => handleSend(prompt)}
          disabled={isStreaming}
        />
      ) : null}

      <MessageList messages={messages} />

      {isStreaming ? (
        <div className="streaming-indicator">
          <Spinner size="small" />
          <Tooltip content="Receiving tokens from Azure OpenAI" relationship="label">
            <Text size={200}>Streaming...</Text>
          </Tooltip>
        </div>
      ) : null}

      <MessageInput onSend={handleSend} onClear={handleClear} disabled={isStreaming} disclaimer={config.aiDisclaimer} />
    </ChatLayout>
  );
}

export default App;
