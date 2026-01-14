import React from 'react';
import { MSREventChat } from '@msr/webchat';

/**
 * Example: Embedded MSREventChat Component
 * 
 * This demonstrates how to embed the MSR Event Chat component
 * in another React application.
 */
export const EmbeddedChatExample: React.FC = () => {
  return (
    <div style={{ display: 'flex', gap: '20px', padding: '20px' }}>
      {/* Example 1: Minimal props */}
      <div style={{ flex: 1, border: '1px solid #ddd', padding: '10px' }}>
        <h3>Minimal Configuration</h3>
        <MSREventChat />
      </div>

      {/* Example 2: With custom backend */}
      <div style={{ flex: 1, border: '1px solid #ddd', padding: '10px' }}>
        <h3>Custom Backend</h3>
        <MSREventChat
          backendUrl="https://api.example.com"
          siteTitle="My Research Tool"
        />
      </div>

      {/* Example 3: Themed */}
      <div style={{ flex: 1, border: '1px solid #ddd', padding: '10px' }}>
        <h3>Themed Chat</h3>
        <MSREventChat
          siteTitle="Themed Chat"
          theme={{
            primaryColor: '#2e8b57',
            accentColor: '#ff6347'
          }}
        />
      </div>
    </div>
  );
};

/**
 * Example: Chat in a Modal
 */
export const ChatModalExample: React.FC<{ isOpen: boolean; onClose: () => void }> = ({
  isOpen,
  onClose
}) => {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        width: '600px',
        height: '600px',
        backgroundColor: 'white',
        borderRadius: '8px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
        overflow: 'hidden'
      }}>
        <MSREventChat
          backendUrl="http://localhost:8000/api"
          siteTitle="Research Assistant"
        />
      </div>
      <button
        onClick={onClose}
        style={{
          position: 'absolute',
          top: '20px',
          right: '20px',
          background: 'white',
          border: 'none',
          borderRadius: '50%',
          width: '40px',
          height: '40px',
          fontSize: '24px',
          cursor: 'pointer'
        }}
      >
        ×
      </button>
    </div>
  );
};

/**
 * Example: Chat in a Sidebar
 */
export const ChatSidebarExample: React.FC = () => {
  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ flex: 1, padding: '20px', overflowY: 'auto' }}>
        <h1>Main Content Area</h1>
        <p>Your application content here...</p>
      </div>
      <div style={{
        width: '400px',
        borderLeft: '1px solid #ddd',
        display: 'flex',
        flexDirection: 'column'
      }}>
        <MSREventChat
          backendUrl="http://localhost:8000/api"
          siteTitle="Chat Assistant"
        />
      </div>
    </div>
  );
};

export default EmbeddedChatExample;
