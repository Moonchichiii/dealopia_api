import React, { useEffect, useRef } from 'react';
import { Mic, Send, X, Bot } from 'lucide-react';
import { useChatStore } from './ChatStore';
import { ChatMessage } from './ChatMessage';

export const ChatWindow: React.FC = () => {
  const {
    messages,
    isOpen,
    isListening,
    toggleChat,
    toggleListening,
    addMessage,
  } = useChatStore();
  
  const inputRef = useRef<HTMLInputElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const input = inputRef.current;
    if (!input?.value.trim()) return;

    const userMessage = input.value;
    addMessage(userMessage, 'user');
    input.value = '';

    try {
      // Replace with your Django backend endpoint
      const response = await fetch('YOUR_DJANGO_ENDPOINT', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message: userMessage }),
      });

      const data = await response.json();
      addMessage(data.response, 'assistant');
    } catch (error) {
      console.error('Failed to get response:', error);
      addMessage('Sorry, I encountered an error. Please try again.', 'assistant');
    }
  };

  const handleVoiceInput = () => {
    if (!('webkitSpeechRecognition' in window)) {
      alert('Voice recognition is not supported in this browser.');
      return;
    }

    const recognition = new (window as any).webkitSpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = false;

    recognition.onstart = () => {
      toggleListening();
    };

    recognition.onresult = (event: any) => {
      const transcript = event.results[0][0].transcript;
      if (inputRef.current) {
        inputRef.current.value = transcript;
      }
    };

    recognition.onend = () => {
      toggleListening();
    };

    recognition.start();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed bottom-4 right-4 w-96 max-w-[calc(100vw-2rem)] rounded-2xl bg-gray-900/95 backdrop-blur-sm border border-gray-800/50 shadow-elevation animate-slide-up">
      <div className="flex items-center justify-between p-4 border-b border-gray-800/50">
        <div className="flex items-center gap-2">
          <div className="relative">
            <div className="absolute -inset-1 bg-gradient-to-r from-primary-600 to-accent-600 rounded-full blur opacity-40 animate-pulse" />
            <div className="relative flex h-8 w-8 items-center justify-center rounded-full bg-gray-900">
              <Bot className="h-5 w-5 text-white" />
            </div>
          </div>
          <h2 className="text-lg font-semibold text-white">AI Assistant</h2>
        </div>
        <button
          onClick={toggleChat}
          className="p-1 hover:bg-gray-800 rounded-lg transition-colors"
        >
          <X className="h-5 w-5 text-gray-400" />
        </button>
      </div>

      <div className="h-96 overflow-y-auto p-4 space-y-4">
        {messages.map((message) => (
          <ChatMessage
            key={message.id}
            content={message.content}
            role={message.role}
          />
        ))}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={handleSubmit} className="p-4 border-t border-gray-800/50">
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            placeholder="Type your message..."
            className="flex-1 bg-gray-800/50 border border-gray-700 rounded-lg px-4 py-2 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:border-primary-500/50"
          />
          <button
            type="button"
            onClick={handleVoiceInput}
            className={`p-2 rounded-lg transition-colors ${
              isListening
                ? 'bg-primary-600 text-white'
                : 'bg-gray-800 hover:bg-gray-700 text-gray-400'
            }`}
          >
            <Mic className="h-5 w-5" />
          </button>
          <button
            type="submit"
            className="p-2 bg-primary-600 hover:bg-primary-700 text-white rounded-lg transition-colors"
          >
            <Send className="h-5 w-5" />
          </button>
        </div>
      </form>
    </div>
  );
};