import { tokens } from "@fluentui/react-components";

// This is a global style that will help override the default styles of the Chat answers output due to it not using the Fluent UI components

const GlobalStyles = `
a {
    color: ${tokens.colorBrandForegroundLink};
    text-decoration: none;
    
  }

a:hover {
    text-decoration: underline;
}
`;

export const applyGlobalStyles = () => {
    const styleElement = document.createElement('style');
    styleElement.textContent = GlobalStyles;

    // Append the style element to the document head
    document.head.appendChild(styleElement);
}
