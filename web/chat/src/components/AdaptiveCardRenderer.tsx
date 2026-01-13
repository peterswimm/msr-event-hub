import React, { useEffect, useRef } from "react";
import * as AdaptiveCards from "adaptivecards";
import "./AdaptiveCard.css";

interface AdaptiveCardRendererProps {
  card: any; // Adaptive Card JSON
  onAction?: (action: AdaptiveCards.Action) => void;
}

const AdaptiveCardRenderer: React.FC<AdaptiveCardRendererProps> = ({ card, onAction }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current || !card) return;

    console.log("Rendering Adaptive Card:", card);

    // Get computed styles from parent to inherit theme
    const computedStyle = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.classList.contains('dark');

    // Create an AdaptiveCard instance
    const adaptiveCard = new AdaptiveCards.AdaptiveCard();

    // Set host config to inherit parent page styling
    adaptiveCard.hostConfig = new AdaptiveCards.HostConfig({
      fontFamily: computedStyle.getPropertyValue('font-family') || "Segoe UI, system-ui, sans-serif",
      spacing: {
        small: 8,
        default: 12,
        medium: 16,
        large: 24,
        extraLarge: 32,
        padding: 16
      },
      separator: {
        lineThickness: 1,
        lineColor: isDark ? "#3F3F3F" : "#EEEEEE"
      },
      supportsInteractivity: true,
      imageBaseUrl: "",
      containerStyles: {
        default: {
          backgroundColor: isDark ? "#1F1F1F" : "#FFFFFF",
          foregroundColors: {
            default: {
              default: isDark ? "#FFFFFF" : "#242424",
              subtle: isDark ? "#C8C8C8" : "#616161"
            },
            accent: {
              default: "#0078D4",
              subtle: "#106EBE"
            }
          }
        }
      },
      actions: {
        maxActions: 10,
        spacing: "default",
        buttonSpacing: 8,
        showCard: {
          actionMode: "inline",
          inlineTopMargin: 12
        },
        actionsOrientation: "horizontal",
        actionAlignment: "stretch"
      }
    });

    // Handle action events
    adaptiveCard.onExecuteAction = (action: AdaptiveCards.Action) => {
      if (onAction) {
        onAction(action);
      }
    };

    // Parse and render the card
    try {
      console.log("[AdaptiveCardRenderer] parsing card version:", card?.version, "schema:", card?.$schema);
      if (!card?.type || card?.type !== "AdaptiveCard") {
        console.warn("[AdaptiveCardRenderer] Missing or invalid card type", card?.type);
      }
      adaptiveCard.parse(card);
      const renderedCard = adaptiveCard.render();
      
      if (renderedCard) {
        // Clear previous content
        containerRef.current.innerHTML = "";
        containerRef.current.appendChild(renderedCard);
        
        // Debug logging
        console.log("Card rendered successfully");
        console.log("Container styles:", {
          display: window.getComputedStyle(containerRef.current).display,
          visibility: window.getComputedStyle(containerRef.current).visibility,
          height: window.getComputedStyle(containerRef.current).height,
          overflow: window.getComputedStyle(containerRef.current).overflow,
          opacity: window.getComputedStyle(containerRef.current).opacity
        });
        console.log("Rendered card HTML length:", renderedCard.outerHTML?.length || 0);
      } else {
        console.warn("adaptiveCard.render() returned null");
      }
    } catch (error) {
      console.error("Error rendering Adaptive Card:", error);
      containerRef.current.innerHTML = `<div style="color: red; padding: 12px;">Failed to render card: ${error instanceof Error ? error.message : 'Unknown error'}</div>`;
    }
  }, [card, onAction]);

  return (
    <div 
      ref={containerRef} 
      className="adaptive-card-container"
    />
  );
};

export default AdaptiveCardRenderer;
