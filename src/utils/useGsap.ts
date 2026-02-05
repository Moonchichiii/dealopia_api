import { useEffect } from 'react';

// Import GSAP core
import { gsap } from 'gsap';

// Import plugins
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { ScrollSmoother } from 'gsap/ScrollSmoother';
import { SplitText } from 'gsap/SplitText';
import { Observer } from 'gsap/Observer';
import { ScrollToPlugin } from 'gsap/ScrollToPlugin';
import { Draggable } from 'gsap/Draggable';
import { Flip } from 'gsap/Flip';

// Register plugins
if (typeof window !== 'undefined') {
    gsap.registerPlugin(
        ScrollTrigger,
        ScrollSmoother,
        SplitText,
        Observer,
        ScrollToPlugin,
        Draggable,
        Flip
    );
}

// Set default GSAP settings
gsap.config({
    autoSleep: 60,
    force3D: true,
    nullTargetWarn: false,
});

// Type for dependencies
type DependencyList = ReadonlyArray<unknown>;

/**
 * Hook for initializing GSAP in components
 * @param callback - Function that receives the GSAP context
 * @param dependencies - Dependency array for the effect
 */
export const useGSAP = (
    callback: (ctx: gsap.Context) => void,
    dependencies: DependencyList = []
  ): void => {
    useEffect(() => {
      const ctx = gsap.context(callback);
      return () => ctx.revert();
    }, [callback, ...dependencies]);
  };
  

// Export GSAP and plugins
export {
    gsap,
    ScrollTrigger,
    ScrollSmoother,
    SplitText,
    Observer,
    ScrollToPlugin,
    Draggable,
    Flip,
};