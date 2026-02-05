import { useEffect, useRef } from 'react';
import gsap from 'gsap';
import { Tag } from 'lucide-react';

interface LoaderProps {
  progress?: number;
}

export default function Loader({ progress = 0 }: LoaderProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const tagRef = useRef<HTMLDivElement>(null);
  const progressRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!tagRef.current) return;

    const tl = gsap.timeline({ 
      repeat: -1,
      defaults: { duration: 0.8, ease: "bounce.out" }
    });

    tl.to(tagRef.current, {
      y: -20,
      rotation: 0
    })
    .to(tagRef.current, {
      y: 0,
      rotation: 360
    });

    return () => tl.kill();
  }, []);

  useEffect(() => {
    if (!progressRef.current) return;

    gsap.to(progressRef.current, {
      innerText: progress,
      duration: 0.7,
      snap: { innerText: 1 },
      modifiers: {
        innerText: value => `${Math.round(value)}%`
      }
    });

    if (progress >= 100 && containerRef.current) {
      gsap.to(containerRef.current, {
        opacity: 0,
        duration: 0.8,
        ease: 'power4.out',
        onComplete: () => {
          if (containerRef.current) {
            containerRef.current.style.display = 'none';
          }
        }
      });
    }
  }, [progress]);

  return (
    <div ref={containerRef} className="fixed inset-0 z-[9999] bg-[#080420] flex flex-col items-center justify-center">
      <div className="flex flex-col items-center space-y-8">
        <div ref={tagRef} className="w-20 h-20">
          <Tag className="w-full h-full text-pink-500" />
        </div>
        
        <div className="flex flex-col items-center space-y-2">
          <div className="text-lg font-medium text-white/90 tracking-wider">
            Loading Experience
          </div>
          <div 
            ref={progressRef}
            className="text-3xl font-bold bg-gradient-to-r from-pink-500 to-blue-500 bg-clip-text text-transparent"
          >
            0%
          </div>
        </div>
      </div>
    </div>
  );
}