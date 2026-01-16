import React, { useCallback, useMemo, useRef, useState } from "react";
import {
  Spinner,
  Text,
  Tooltip
} from "@fluentui/react-components";
import { ShieldError24Regular } from "@fluentui/react-icons";
import ChatLayout from "./components/ChatLayout";
import MessageInput from "./components/MessageInput";
import MessageList from "./components/MessageList";
import BrandHeader from "./components/BrandHeader";
import HamburgerMenu from "./components/HamburgerMenu";
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
  const [examplePrompts, setExamplePrompts] = useState<Array<{title: string; prompt: string}>>([]);
  const abortRef = useRef<AbortController | null>(null);

  // Load welcome message and examples on mount
  React.useEffect(() => {
    const loadWelcome = async () => {
      try {
        // Determine the correct backend URL
        // In dev: backend is at localhost:8000
        // In production: backend is at same origin or configured via env
        const baseUrl = (import.meta.env.VITE_CHAT_API_BASE as string | undefined) ?? 
                       (import.meta.env.DEV ? "http://localhost:8000/api" : "/api");
        console.log("Loading welcome from:", `${baseUrl}/chat/welcome`);
        const response = await fetch(`${baseUrl}/chat/welcome`);
        console.log("Welcome response status:", response.status);
        if (response.ok) {
          const data = await response.json();
          console.log("Welcome data received:", data);
          setMessages([{
            id: "welcome",
            role: "assistant",
            content: `${data.message}\n\n${data.description}`,
            adaptive_card: data.adaptive_card, // Include the adaptive card
            isWelcomeCard: true // Mark this as the welcome card for filtering
          }]);
          console.log("Messages set with welcome card:", data.adaptive_card ? "has card" : "no card");
          setExamplePrompts(data.examples || []);
        }
      } catch (err) {
        console.error("Failed to load welcome message:", err);
        // Use default messages if API fails
        setMessages([{
          id: "welcome",
          role: "assistant",
          content: "Welcome to MSR Event Hub Chat! 🎓\n\nI can help you explore research projects, find sessions, and learn about the Redmond Research Showcase.",
          isWelcomeCard: true // Mark this as the welcome card for filtering
        }]);
      }
    };
    
    loadWelcome();
  }, []);

  const config = useMemo(
    () => ({
      endpoint: import.meta.env.VITE_AOAI_ENDPOINT as string | undefined,
      deployment: import.meta.env.VITE_AOAI_DEPLOYMENT as string | undefined,
      apiVersion: (import.meta.env.VITE_AOAI_API_VERSION as string | undefined) ?? "2024-02-15-preview",
      apiKey: import.meta.env.VITE_AOAI_KEY as string | undefined,
      hubApiBase: (import.meta.env.VITE_CHAT_API_BASE as string | undefined) ?? 
                  (import.meta.env.DEV ? "http://localhost:8000/api" : "/api"),
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
      console.log("[App.handleSend] Called with text:", text.substring(0, 50));
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
      let assistantCard: any = null;

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

        for await (const chunk of stream) {
          // Handle both string deltas (from Azure) and payload objects (from hub)
          const delta = typeof chunk === "string" ? chunk : chunk?.delta || "";
          const adaptiveCard = typeof chunk === "object" ? chunk?.adaptive_card : null;
          // Debug: log incoming chunk structure
          if (typeof chunk === "object") {
            console.log("[stream] payload keys:", Object.keys(chunk));
            console.log("[stream] has adaptive_card:", Boolean(chunk?.adaptive_card));
          } else {
            console.log("[stream] delta chunk length:", delta.length);
          }
          
          if (delta) {
            assistantContent += delta;
          }
          if (adaptiveCard && !assistantCard) {
            assistantCard = adaptiveCard;
          }
          
          setMessages((prev: ChatMessage[]) => {
            const next = prev.filter((m: ChatMessage) => m.id !== assistantId);
            return [
              ...next,
              {
                id: assistantId,
                role: "assistant",
                content: assistantContent,
                adaptive_card: assistantCard
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

  const handleCardAction = useCallback(async (actionData: any) => {
    // Handle different card actions
    // Send card action as JSON query to backend
    if (actionData.action) {
      const cardActionQuery = JSON.stringify({
        action: actionData.action,
        projectId: actionData.projectId,
        researchArea: actionData.researchArea
      });
      
      // Build messages with card action as a user message so backend detects it
      const baseMessages: ChatMessage[] = [
        { id: "system", role: "system", content: systemPrompt },
        ...messages,
        { id: "action", role: "user", content: cardActionQuery } // Changed from system to user
      ];
      
      setError(null);
      setIsStreaming(true);
      
      const controller = new AbortController();
      abortRef.current = controller;
      
      const assistantId = crypto.randomUUID();
      let assistantContent = "";
      let assistantCard: any = null;
      
      try {
        console.log("[App] prefersHubProxy:", prefersHubProxy, "config.hubApiBase:", config?.hubApiBase);
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

        for await (const chunk of stream) {
          const delta = typeof chunk === "string" ? chunk : chunk?.delta || "";
          const adaptiveCard = typeof chunk === "object" ? chunk?.adaptive_card : null;
          
          console.log("[handleCardAction stream]", {
            chunkType: typeof chunk,
            deltaLength: delta.length,
            hasAdaptiveCard: Boolean(adaptiveCard),
            chunkKeys: typeof chunk === "object" ? Object.keys(chunk) : "N/A"
          });
          
          if (delta) {
            assistantContent += delta;
          }
          if (adaptiveCard && !assistantCard) {
            console.log("[handleCardAction] Setting assistantCard");
            assistantCard = adaptiveCard;
          }
          
          setMessages((prev: ChatMessage[]) => {
            // Remove the assistant message being updated and welcome card messages
            const filtered = prev.filter((m: ChatMessage) => {
              // Keep if it's not the current assistant message
              if (m.id !== assistantId) {
                // Remove the welcome card when a new response comes in
                if ((m as any).isWelcomeCard) {
                  return false;
                }
                return true;
              }
              return false;
            });
            return [
              ...filtered,
              {
                id: assistantId,
                role: "assistant",
                content: assistantContent,
                adaptive_card: assistantCard
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
    } else if (actionData.query) {
      // If the card action has a query, send it
      handleSend(actionData.query);
    } else {
      // Default: just send the card data as a message
      handleSend(JSON.stringify(actionData));
    }
  }, [handleSend, config.hubApiBase, config.endpoint, config.deployment, config.apiVersion, config.apiKey, messages, prefersHubProxy, canStreamDirect, systemPrompt]);

  const handleMenuAction = useCallback((action: string) => {
    // Trigger card action from menu
    handleCardAction({ action });
  }, [handleCardAction]);

  return (
    <ChatLayout
      header={
        <BrandHeader 
          title={config.siteTitle!} 
          feedbackUrl={import.meta.env.VITE_FEEDBACK_URL as string | undefined} 
          onStop={handleStop} 
          isStreaming={isStreaming}
          hamburgerMenu={<HamburgerMenu onMenuItemClick={handleMenuAction} />}
        />
      }
      footer={<MessageInput onSend={handleSend} onClear={handleClear} disabled={isStreaming} disclaimer={config.aiDisclaimer} />}
      linksFooter={<Footer />}
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
        <div className="loading-message">
          <p>Loading chat interface...</p>
        </div>
      ) : null}

      {messages.length === 0 ? (
        <HeroCards
          heading={config.frontHeading!}
          subheading={config.frontSubheading!}
          promptInstruction={config.promptInstruction}
          cards={(import.meta.env.VITE_HERO_CARDS ? JSON.parse(import.meta.env.VITE_HERO_CARDS as string) : undefined) || examplePrompts.map((ex: any) => ({
            title: ex.title,
            subtitle: `Ask: "${ex.prompt}"`,
            prompt: ex.prompt
          })) || [
            { title: "Help me find projects that match my interests.", subtitle: "Ask a few questions to get to know me.", prompt: "Help me find projects that match my interests." },
            { title: "Activate Agenda Mode to plan my visit.", subtitle: "Ask a few questions about my interests.", prompt: "Activate Agenda Mode to plan my visit." },
            { title: "Evaluate collaboration opportunities.", subtitle: "Focus on AI and renewable energy.", prompt: "Evaluate the collaboration opportunities between projects focused on artificial intelligence and renewable energy at the showcase." },
          ]}
          onPick={(prompt: string) => handleSend(prompt)}
          disabled={isStreaming}
        />
      ) : null}

      <MessageList messages={messages} onCardAction={handleCardAction} />

      {isStreaming ? (
        <div className="streaming-indicator">
          <Spinner size="small" />
          <Tooltip content="Receiving tokens from Azure OpenAI" relationship="label">
            <Text size={200}>Streaming...</Text>
          </Tooltip>
        </div>
      ) : null}
    </ChatLayout>
  );
}

export default App;
