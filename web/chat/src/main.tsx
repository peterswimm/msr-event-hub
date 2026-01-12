import { FluentProvider, webLightTheme, webDarkTheme } from "@fluentui/react-components";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./styles.css";
import { applyGlobalStyles } from "./GlobalStyles";

const queryClient = new QueryClient();

const themeName = (import.meta.env.VITE_THEME as string | undefined) ?? "webDark";
const theme = themeName === "webDark" ? webDarkTheme : webLightTheme;

// Add a class to html for CSS variables when using dark theme
if (themeName === "webDark") {
  document.documentElement.classList.add("dark");
} else {
  document.documentElement.classList.remove("dark");
}

applyGlobalStyles();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <FluentProvider theme={theme} style={{ height: "100%" }}>
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </FluentProvider>
  </React.StrictMode>
);
