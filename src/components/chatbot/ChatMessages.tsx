import React from 'react';
import { Bot, User } from 'lucide-react';

interface ChatMessageProps {
  content: string;
  role: 'user' | 'assistant';
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ content, role }) => {
  const isUser = role === 'user';

  return (
    <div className={`flex items-start gap-2.5 ${isUser ? 'flex-row-reverse' : ''}`}>
      <div className={`flex h-8 w-8 items-center justify-center rounded-full ${
        isUser ? 'bg-primary-600' : 'bg-accent-600'
      }`}>
        {isUser ? <User className="h-5 w-5 text-white" /> : <Bot className="h-5 w-5 text-white" />}
      </div>
      <div className={`max-w-[80%] rounded-lg px-4 py-2 ${
        isUser 
          ? 'bg-primary-600 text-white' 
          : 'bg-gray-800 text-gray-100'
      }`}>
        <p className="text-sm">{content}</p>
      </div>
    </div>
  );
};