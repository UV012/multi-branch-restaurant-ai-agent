import React, { useState, useEffect, useRef } from 'react';
import { api } from '../../api';
import { Send, Bot, User, Sparkles, AlertCircle, RefreshCw } from 'lucide-react';

export default function ChatWidget({
  currentCustomer,
  selectedBranch,
  onRequireAuth,
  prefilledPrompt,
  onClearPrefill,
}) {
  const [messages, setMessages] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: "Hello! Welcome to GourmetBistro. I'm your AI Dining Assistant powered by DeepSeek R1. How can I help you today? You can ask for our menu, place food orders, or book a table with instant auto-confirmation!",
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const chatMessagesRef = useRef(null);

  const quickChips = [
    "What's on the menu?",
    "Book a table for 4 tonight at 7 PM",
    "Order 2 Margherita Pizzas",
    "Where are you located & what are your hours?",
    "Check status of my latest order",
  ];

  // Auto-scroll messages container to bottom without scrolling window
  const scrollToBottom = () => {
    if (chatMessagesRef.current) {
      chatMessagesRef.current.scrollTop = chatMessagesRef.current.scrollHeight;
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Handle prefilled prompt from MenuExplorer
  useEffect(() => {
    if (prefilledPrompt) {
      handleSendMessage(prefilledPrompt);
      if (onClearPrefill) onClearPrefill();
    }
  }, [prefilledPrompt]);

  const handleSendMessage = async (textToSend = null) => {
    const text = (textToSend || inputText).trim();
    if (!text) return;

    // Guard: Require customer authentication
    if (!currentCustomer) {
      onRequireAuth();
      return;
    }

    const userMessage = {
      id: Date.now(),
      sender: 'user',
      text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
    };

    setMessages((prev) => [...prev, userMessage]);
    if (!textToSend) setInputText('');
    setLoading(true);
    setError('');

    try {
      const branchId = selectedBranch ? selectedBranch.id : null;
      const response = await api.sendMessage(text, branchId);

      const botMessage = {
        id: Date.now() + 1,
        sender: 'assistant',
        text: response.reply,
        active_flow: response.active_flow,
        order_id: response.order_id,
        reservation_id: response.reservation_id,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };

      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      setError(err.message || 'Error communicating with AI agent.');
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: `⚠️ Error: ${err.message || 'Unable to connect to the agent. Please try again.'}`,
          isError: true,
          timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleResetChat = () => {
    setMessages([
      {
        id: 1,
        sender: 'assistant',
        text: `Welcome! I'm your AI concierge for ${selectedBranch?.name || 'GourmetBistro'}. How can I assist you with dining, menu items, or reservations?`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      },
    ]);
  };

  return (
    <div className="chat-main">
      {/* Chat Header */}
      <div className="chat-header">
        <div className="chat-agent-info">
          <div
            style={{
              width: '38px',
              height: '38px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'white',
            }}
          >
            <Bot size={20} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <span style={{ fontWeight: 700, fontSize: '0.95rem', color: 'var(--secondary)' }}>
                BistroAI Agent
              </span>
              <span className="status-dot" title="Ollama DeepSeek R1 Connected" />
            </div>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {selectedBranch ? `${selectedBranch.name} • DeepSeek R1 8B` : 'Select a branch'}
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <button
            onClick={handleResetChat}
            className="btn-outline btn-sm"
            style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '0.75rem' }}
            title="Start new conversation"
          >
            <RefreshCw size={13} /> Reset
          </button>
        </div>
      </div>

      {/* Messages List */}
      <div className="chat-messages" ref={chatMessagesRef}>
        {messages.map((m) => (
          <div
            key={m.id}
            className={`message-bubble ${m.sender}`}
            style={{
              background: m.isError ? '#fee2e2' : undefined,
              color: m.isError ? '#991b1b' : undefined,
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '4px' }}>
              {m.sender === 'assistant' ? (
                <Bot size={14} style={{ color: 'var(--primary)' }} />
              ) : (
                <User size={14} style={{ color: 'white' }} />
              )}
              <span style={{ fontSize: '0.75rem', fontWeight: 600, opacity: 0.8 }}>
                {m.sender === 'assistant' ? 'AI Assistant' : currentCustomer?.name || 'You'}
              </span>
              <span style={{ fontSize: '0.7rem', opacity: 0.6, marginLeft: 'auto' }}>
                {m.timestamp}
              </span>
            </div>

            <div>{m.text}</div>

            {m.order_id && (
              <div
                style={{
                  marginTop: '6px',
                  background: 'white',
                  color: 'var(--text-main)',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  display: 'inline-block',
                }}
              >
                🎉 Order #{m.order_id} Confirmed
              </div>
            )}

            {m.reservation_id && (
              <div
                style={{
                  marginTop: '6px',
                  background: 'white',
                  color: 'var(--text-main)',
                  padding: '4px 8px',
                  borderRadius: '6px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  display: 'inline-block',
                }}
              >
                ✅ Reservation #{m.reservation_id} Auto-Confirmed
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="message-bubble assistant" style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sparkles size={16} className="spin" style={{ color: 'var(--primary)' }} />
            <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              DeepSeek R1 is reasoning and checking restaurant availability...
            </span>
          </div>
        )}
      </div>

      {/* Suggested Quick Action Chips */}
      <div className="chat-chips">
        {quickChips.map((chip, idx) => (
          <button
            key={idx}
            className="chip-btn"
            onClick={() => handleSendMessage(chip)}
            disabled={loading}
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input Area */}
      <div className="chat-input-area">
        {!currentCustomer ? (
          <div
            style={{
              width: '100%',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '8px 12px',
              background: 'var(--primary-light)',
              borderRadius: '8px',
              fontSize: '0.85rem',
            }}
          >
            <span style={{ color: '#9a3412', fontWeight: 500 }}>
              Please sign in to chat with the AI assistant, place orders, and book tables.
            </span>
            <button onClick={onRequireAuth} className="btn-primary btn-sm">
              Sign In / Register
            </button>
          </div>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            style={{ display: 'flex', width: '100%', gap: '8px' }}
          >
            <input
              type="text"
              placeholder={`Ask about ${selectedBranch?.name || 'our restaurant'}, order items, or reserve a table...`}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              disabled={loading}
            />
            <button
              type="submit"
              className="btn-primary"
              disabled={loading || !inputText.trim()}
              style={{ padding: '0 18px' }}
            >
              <Send size={16} />
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
