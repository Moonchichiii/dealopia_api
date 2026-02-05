import { useState, useEffect } from 'react';
import { ArrowUp } from 'lucide-react';

export const ScrollToTopButton: React.FC = () => {
    const [isVisible, setIsVisible] = useState(false);
    const [isHovered, setIsHovered] = useState(false);
    const [isAnimating, setIsAnimating] = useState(false);
    const [scrollPosition, setScrollPosition] = useState(0);

    useEffect(() => {
        const handleScroll = () => {
            const newPosition = window.scrollY;
            setScrollPosition(newPosition);
            setIsVisible(newPosition > 400);
            setIsAnimating(true);
            const timeout = setTimeout(() => setIsAnimating(false), 300);
            return () => clearTimeout(timeout);
        };

        window.addEventListener('scroll', handleScroll, { passive: true });
        return () => window.removeEventListener('scroll', handleScroll);
    }, []);

    const scrollToTop = () => {
        setIsAnimating(true);
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
        setTimeout(() => setIsAnimating(false), 300);
    };

    return (
        <button
            onClick={scrollToTop}
            onMouseEnter={() => setIsHovered(true)}
            onMouseLeave={() => setIsHovered(false)}
            className={`fixed z-[10000] p-4 rounded-full shadow-lg transition-all duration-300 transform
                ${!isVisible ? 'scale-0 opacity-0' : 'scale-100 opacity-100'}
                ${isHovered ? 'scale-110' : ''}
                ${isAnimating ? 'animate-bounce-subtle' : ''}
                backdrop-blur-md bg-gray-900/60 hover:bg-gray-800/70
                left-6 bottom-[5vh]
                sm:left-8`}
            style={{
                transform: `translate3d(0, ${Math.min(Math.max(scrollPosition * 0.1, -20), 20)}px, 0)`,
                transition: 'transform 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
                boxShadow: isHovered ? '0 0 20px rgba(255,255,255,0.2)' : '0 0 10px rgba(255,255,255,0.1)',
            }}
        >
            <div className="relative">
                <div className={`absolute -inset-2 bg-gradient-to-r from-gray-500/30 to-gray-400/30 rounded-full blur-md
                    transition-all duration-300 ${isHovered ? 'scale-150 opacity-50' : 'scale-100 opacity-30'}`} />
                
                <div className={`absolute -inset-1 rounded-full bg-gradient-to-r from-white/10 to-gray-500/10
                    animate-pulse transition-transform duration-300 ${isHovered ? 'scale-125' : 'scale-100'}`} />
                
                <div className="relative">
                    <ArrowUp
                        className={`h-6 w-6 text-white transform transition-all duration-300
                            ${isHovered ? 'scale-110 -translate-y-1' : ''}
                            ${isAnimating ? 'animate-bounce-subtle' : ''}`}
                    />
                    <div className={`absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3
                        bg-white/30 rounded-full blur-sm transition-opacity duration-300
                        ${isHovered ? 'opacity-100' : 'opacity-0'}`} />
                </div>
            </div>
        </button>
    );
};
