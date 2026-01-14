# @msr/webchat - Embedded Chat Component

A reusable, atomic React component for embedding the MSR Event Hub Chat widget in any React application.

## Installation

```bash
npm install @msr/webchat react react-dom
```

The component requires React 18+ as a peer dependency.

## Basic Usage

### Standalone (Default)

The component works out of the box with default configuration:

```jsx
import { MSREventChat } from '@msr/webchat';

export function MyApp() {
  return <MSREventChat />;
}
```

### With Custom Backend

Pass a custom backend URL:

```jsx
<MSREventChat 
  backendUrl="https://api.example.com"
/>
```

### Full Configuration

```jsx
<MSREventChat
  backendUrl="https://api.example.com"
  siteTitle="My Research Assistant"
  systemPrompt="You are a helpful research assistant..."
  theme={{
    primaryColor: '#0078d4',
    accentColor: '#50e6ff'
  }}
  onMessageSent={(message) => {
    console.log('Message sent:', message);
  }}
/>
```

## Component Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `backendUrl` | string | `http://localhost:8000/api` | Backend API base URL |
| `siteTitle` | string | "MSR Event Hub Chat" | Title displayed in header |
| `systemPrompt` | string | Default prompt | System message for AI |
| `theme` | object | - | Theme configuration (primaryColor, accentColor) |
| `welcomeMessage` | string | - | Custom welcome message |
| `preferHubProxy` | boolean | true | Use Hub API proxy if available |
| `onMessageSent` | function | - | Callback when message is sent |
| `className` | string | - | CSS class name |
| `style` | object | - | Inline CSS styles |

## Examples

### Embedded in a Sidebar

```jsx
export function DashboardWithChat() {
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: 1, padding: '20px' }}>
        <h1>Dashboard</h1>
        {/* Your dashboard content */}
      </div>
      <div style={{ width: '400px', borderLeft: '1px solid #ddd' }}>
        <MSREventChat 
          backendUrl="https://api.myapp.com"
          siteTitle="Assistant"
        />
      </div>
    </div>
  );
}
```

### In a Modal

```jsx
import { useState } from 'react';
import { MSREventChat } from '@msr/webchat';

export function ChatModal() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button onClick={() => setIsOpen(true)}>
        Open Chat
      </button>
      
      {isOpen && (
        <div style={{
          position: 'fixed',
          inset: 0,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          backgroundColor: 'rgba(0,0,0,0.5)'
        }}>
          <div style={{
            width: '600px',
            height: '600px',
            backgroundColor: 'white',
            borderRadius: '8px'
          }}>
            <MSREventChat backendUrl="https://api.myapp.com" />
            <button onClick={() => setIsOpen(false)}>
              Close
            </button>
          </div>
        </div>
      )}
    </>
  );
}
```

### With Message Tracking

```jsx
export function ChatWithTracking() {
  const handleMessageSent = (message) => {
    console.log('User message:', message.content);
    // Send to analytics
    analytics.trackEvent('chat_message', {
      messageId: message.id,
      role: message.role,
      length: message.content.length
    });
  };

  return (
    <MSREventChat 
      backendUrl="https://api.myapp.com"
      onMessageSent={handleMessageSent}
    />
  );
}
```

## Styling

The component includes default Fluent UI styling. To customize:

### CSS Variables

```css
:root {
  --msr-primary-color: #0078d4;
  --msr-accent-color: #50e6ff;
  --msr-font-family: 'Segoe UI', sans-serif;
}
```

### Component Container Styling

```jsx
<div style={{
  width: '100%',
  height: '600px',
  border: '1px solid #ddd',
  borderRadius: '8px',
  overflow: 'hidden'
}}>
  <MSREventChat backendUrl="..." />
</div>
```

## Type Safety

Full TypeScript support with exported types:

```typescript
import { MSREventChat, type MSREventChatProps, type ChatMessage } from '@msr/webchat';

const props: MSREventChatProps = {
  backendUrl: 'https://api.example.com',
  siteTitle: 'Chat'
};

const handleMessage = (msg: ChatMessage) => {
  console.log(msg.content);
};
```

## Backend API Contract

The component expects a backend API with these endpoints:

```
POST /chat/action          - Send action/message
GET  /chat/welcome         - Get welcome message
GET  /data/projects        - List projects
GET  /data/projects/:id    - Get project details
```

See [API Reference](../msr-event-agent-bridge/docs/API_REFERENCE.md) for full details.

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

Requires ES2020+ JavaScript support.

## License

MIT

## Support

For issues, questions, or contributions, see the main [README.md](../README.md).

---

**Version**: 1.0.0  
**Last Updated**: January 14, 2026
