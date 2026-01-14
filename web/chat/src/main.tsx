import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import { useGlobalStyles } from "./GlobalStyles";

// Initialize axe-core for accessibility testing in development
if (import.meta.env.DEV && import.meta.env.VITE_A11Y === 'true') {
  import('@axe-core/react').then(axe => {
    axe.default(React, ReactDOM, 1000, {});
    console.log('🔍 Axe-core accessibility testing enabled');
  }).catch(err => {
    console.warn('Failed to load axe-core:', err);
  });
}

const queryClient = new QueryClient();

const themeName = (import.meta.env.VITE_THEME as string | undefined) ?? "webDark";
const theme = themeName === "webDark" ? webDarkTheme : webLightTheme;

// Add a class to html for CSS variables when using dark theme
if (themeName === "webDark") {
  document.documentElement.classList.add("dark");
} else {
  document.documentElement.classList.remove("dark");
}

// Wrapper component to apply global styles inside React context
function AppWithStyles() {
  useGlobalStyles();
  return <App />;
}

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <FluentProvider theme={theme} style={{ height: "100%" }}>
      <QueryClientProvider client={queryClient}>
        <AppWithStyles />
      </QueryClientProvider>
    </FluentProvider>
  </React.StrictMode>
);
