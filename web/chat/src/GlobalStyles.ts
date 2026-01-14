import { makeStaticStyles, tokens } from "@fluentui/react-components";

// Global styles using Griffel's makeStaticStyles for non-component styles
export const useGlobalStyles = makeStaticStyles({
  a: {
    color: tokens.colorBrandForegroundLink,
    textDecoration: "none",
  },
  "a:hover": {
    textDecoration: "underline",
  },
});
