import React, { useState, useEffect } from 'react';
import { Bot } from 'lucide-react';
import { useChatStore } from './ChatStore';

export const ChatButton: React.FC = () => {
  const { toggleChat, isOpen } = useChatStore();
  const [scrollPosition, setScrollPosition] = useState(0);
  const [isHovered, setIsHovered] = useState(false);
  const [isAnimating, setIsAnimating] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      const newPosition = window.scrollY;
      setScrollPosition(newPosition);
      setIsAnimating(true);
      
      // Reset animation state after a short delay
      const timeout = setTimeout(() => setIsAnimating(false), 300);
      return () => clearTimeout(timeout);
    };

    window.addEventListener('scroll', handleScroll, { passive: true });
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <button
      onClick={() => {
        setIsAnimating(true);
        setTimeout(() => {
          toggleChat();
          setIsAnimating(false);
        }, 300);
      }}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      className={`fixed bottom-6 right-6 p-4 rounded-full shadow-elevation transition-all duration-300 transform 
        ${isOpen ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}
        ${isHovered ? 'scale-110' : ''}
        ${isAnimating ? 'animate-bounce-subtle' : ''}
        bg-gradient-to-r from-primary-600 to-accent-600 hover:from-primary-500 hover:to-accent-500
        sm:bottom-8 sm:right-8`}
      style={{
        transform: `translate3d(0, ${Math.min(Math.max(scrollPosition * 0.1, -20), 20)}px, 0)`,
        transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      <div className="relative">
        {/* Glow effect */}
        <div className={`absolute -inset-2 bg-gradient-to-r from-primary-400 to-accent-400 rounded-full blur-md opacity-20 
          transition-all duration-300 animate-glow ${isHovered ? 'scale-150 opacity-30' : 'scale-100'}`} />
        
        {/* Pulse ring */}
        <div className={`absolute -inset-1 rounded-full bg-gradient-to-r from-primary-400/30 to-accent-400/30
          animate-pulse transition-transform duration-300 ${isHovered ? 'scale-125' : 'scale-100'}`} />
        
        {/* Bot icon */}
        <div className="relative">
          <Bot 
            className={`h-6 w-6 text-white transform transition-all duration-300
              ${isHovered ? 'scale-110 rotate-12' : ''}
              ${isAnimating ? 'animate-float' : ''}`}
          />
          
          {/* Eye glow */}
          <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3
            bg-accent-400/30 rounded-full blur-sm transition-opacity duration-300
            ${isHovered ? 'opacity-100' : 'opacity-0'}`} />
        </div>
      </div>
    </button>
  );
};