import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface Message {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: number;
}

interface ChatState {
  messages: Message[];
  isOpen: boolean;
  isListening: boolean;
  addMessage: (content: string, role: 'user' | 'assistant') => void;
  toggleChat: () => void;
  toggleListening: () => void;
  clearMessages: () => void;
}

export const useChatStore = create<ChatState>()(
  persist(
    (set) => ({
      messages: [],
      isOpen: false,
      isListening: false,
      addMessage: (content, role) =>
        set((state) => ({
          messages: [
            ...state.messages,
            {
              id: crypto.randomUUID(),
              content,
              role,
              timestamp: Date.now(),
            },
          ],
        })),
      toggleChat: () => set((state) => ({ isOpen: !state.isOpen })),
      toggleListening: () => set((state) => ({ isListening: !state.isListening })),
      clearMessages: () => set({ messages: [] }),
    }),
    {
      name: 'chat-storage',
    }
  )
);