import React, { useEffect, useRef } from "react";
import * as AdaptiveCards from "adaptivecards";
import ProjectCarousel from "./ProjectCarousel";
import "./AdaptiveCard.css";

interface AdaptiveCardRendererProps {
  card: any; // Adaptive Card JSON
  onAction?: (action: AdaptiveCards.Action) => void;
}

const AdaptiveCardRenderer: React.FC<AdaptiveCardRendererProps> = ({ card, onAction }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Check if this is a carousel card
  const isCarouselCard = card?.body?.some((item: any) => item.type === "Carousel");

  // Extract carousel data if it's a carousel card
  const getCarouselData = () => {
    if (!isCarouselCard) return null;

    const carouselElement = card.body.find((item: any) => item.type === "Carousel");
    const titleElement = card.body.find((item: any) => item.id === "carousel_title");
    const subtitleElement = card.body.find((item: any) => item.id === "carousel_subtitle");

    const projects = carouselElement?.pages?.map((page: any) => {
      const nameEl = page.body?.find((b: any) => b.size === "large" && b.weight === "bolder");
      const areaEl = page.body?.find((b: any) => b.color === "accent");
      const descEl = page.body?.find((b: any) => b.spacing === "medium" && b.wrap === true && !b.isSubtle);
      const teamEl = page.body?.find((b: any) => b.isSubtle === true);

      return {
        name: nameEl?.text || "Untitled",
        researchArea: areaEl?.text || "",
        description: descEl?.text || "",
        team: teamEl?.text ? [{ displayName: teamEl.text.replace("👥 ", "") }] : [],
      };
    });

    return {
      title: titleElement?.text || "Projects",
      subtitle: subtitleElement?.text || "",
      projects: projects || [],
      actions: card.actions || [],
    };
  };

  const handleCarouselAction = (actionData: any) => {
    if (onAction) {
      // Create a fake SubmitAction for compatibility
      const fakeAction = {
        data: actionData,
      } as any;
      onAction(fakeAction);
    }
  };

  useEffect(() => {
    if (!containerRef.current || !card) return;

    console.log("Rendering Adaptive Card:", card);

    // Get computed styles from parent to inherit theme
    const computedStyle = getComputedStyle(document.documentElement);
    const isDark = document.documentElement.classList.contains('dark');

    // Create an AdaptiveCard instance
    const adaptiveCard = new AdaptiveCards.AdaptiveCard();

    // Set host config to inherit parent page styling with transparent backgrounds
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
        lineColor: isDark ? "#424242" : "#EEEEEE"
      },
      supportsInteractivity: true,
      imageBaseUrl: "",
      containerStyles: {
        default: {
          backgroundColor: "transparent",
          foregroundColors: {
            default: {
              default: isDark ? "#F5F5F5" : "#242424",
              subtle: isDark ? "#C8C8C8" : "#616161"
            },
            accent: {
              default: "#0F6CBD",
              subtle: "#115EA3"
            }
          }
        },
        emphasis: {
          backgroundColor: isDark ? "#292929" : "#F5F5F5",
          foregroundColors: {
            default: {
              default: isDark ? "#F5F5F5" : "#242424",
              subtle: isDark ? "#C8C8C8" : "#616161"
            },
            accent: {
              default: "#0F6CBD",
              subtle: "#115EA3"
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

  // If it's a carousel card, render our custom component
  if (isCarouselCard) {
    const carouselData = getCarouselData();
    if (carouselData) {
      return (
        <ProjectCarousel
          title={carouselData.title}
          subtitle={carouselData.subtitle}
          projects={carouselData.projects}
          actions={carouselData.actions}
          onAction={handleCarouselAction}
        />
      );
    }
  }

  return (
    <div 
      ref={containerRef} 
      className="adaptive-card-container"
    />
  );
};

export default AdaptiveCardRenderer;
