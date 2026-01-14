/**
 * 1DS Web Analytics initialization
 * Tracks user interactions, page views, and custom events
 */

declare global {
  interface Window {
    oneDS: any;
  }
}

let analytics: any = null;

export function initializeAnalytics(): void {
  if (typeof window === 'undefined' || !window.oneDS) {
    console.warn('[Analytics] 1DS SDK not loaded');
    return;
  }

  const instrumentationKey = import.meta.env.VITE_ANALYTICS_KEY;
  
  if (!instrumentationKey) {
    console.warn('[Analytics] No instrumentation key provided. Set VITE_ANALYTICS_KEY environment variable.');
    return;
  }

  analytics = new window.oneDS.ApplicationInsights();
  
  const config = {
    instrumentationKey,
    channelConfiguration: {
      eventsLimitInMem: 50
    },
    propertyConfiguration: {
      env: import.meta.env.MODE || 'prod'
    },
    webAnalyticsConfiguration: {
      autoCapture: {
        scroll: true,
        pageView: true,
        onLoad: true,
        onUnload: true,
        click: true,
        resize: true,
        jsError: true
      }
    }
  };

  analytics.initialize(config, []);
  console.log('[Analytics] 1DS Web Analytics initialized');
}

export function trackEvent(name: string, properties?: Record<string, any>): void {
  if (!analytics) {
    console.warn('[Analytics] Not initialized');
    return;
  }

  analytics.trackEvent({ name }, properties);
}

export function trackPageView(name: string, properties?: Record<string, any>): void {
  if (!analytics) return;
  
  analytics.trackPageView({ name }, properties);
}

export function trackChatInteraction(data: {
  conversationId: string;
  messageId: string;
  userQuery: string;
  responseLatency: number;
  success: boolean;
}): void {
  trackEvent('chat_interaction', {
    conversationId: data.conversationId,
    messageId: data.messageId,
    queryLength: data.userQuery.length,
    responseLatency: data.responseLatency,
    success: data.success
  });
}

export function trackUserFeedback(data: {
  messageId: string;
  rating: 'positive' | 'negative';
  comment?: string;
}): void {
  trackEvent('user_feedback', {
    messageId: data.messageId,
    rating: data.rating,
    hasComment: !!data.comment
  });
}

export function trackFeatureUsage(feature: string, metadata?: Record<string, any>): void {
  trackEvent('feature_usage', {
    feature,
    ...metadata
  });
}

export { analytics };
