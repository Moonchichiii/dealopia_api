import { useEffect, useRef, useState } from 'react';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import {
  Globe2, Leaf, ShieldCheck, Users, Recycle, Heart, Award, Zap,
  Leaf as LeafIcon, Heart as HeartIcon, BadgeCheck, Sparkles,
} from 'lucide-react';

gsap.registerPlugin(ScrollTrigger);

const SustainabilityBackground = () => (
  <div className="absolute inset-0 -z-20 w-full h-full overflow-hidden pointer-events-none">
    <svg
      viewBox="0 0 1200 800"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-full md:scale-100 scale-150 origin-center md:opacity-100 opacity-30 hidden dark:block"
    >
      <defs>
        <linearGradient id="bgGradient" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#0a1f1a" />
          <stop offset="100%" stopColor="#071a15" />
        </linearGradient>

        <pattern id="leafPattern" patternUnits="userSpaceOnUse" width="120" height="120" patternTransform="rotate(10)">
          <path d="M40,60 Q65,20 90,60 Q65,100 40,60 Z"
                fill="none" stroke="#26755a" strokeWidth="1.5" opacity="0.25" />
        </pattern>

        <pattern id="wavePattern" patternUnits="userSpaceOnUse" width="200" height="100">
          <path d="M0,50 Q50,0 100,50 Q150,100 200,50"
                fill="none" stroke="#39a388" strokeWidth="1.5" opacity="0.2" />
        </pattern>

        <pattern id="hexPattern" patternUnits="userSpaceOnUse" width="150" height="170" patternTransform="scale(0.7) rotate(5)">
          <path d="M75,25 L125,60 L125,110 L75,145 L25,110 L25,60 Z"
                fill="none" stroke="#3ab795" strokeWidth="1.5" opacity="0.15" />
        </pattern>
      </defs>

      <rect width="100%" height="100%" fill="url(#bgGradient)" />
      <rect width="100%" height="100%" fill="url(#leafPattern)" />
      <rect width="100%" height="100%" fill="url(#wavePattern)" opacity="0.8" />
      <rect width="100%" height="100%" fill="url(#hexPattern)" />

      <path d="M-50,100 Q100,-50 250,50 Q150,150 100,300 Q0,200 -50,100 Z" fill="#26755a" opacity="0.15" />
      <path d="M1000,400 Q1150,350 1300,500 Q1100,650 950,550 Q950,450 1000,400 Z" fill="#26755a" opacity="0.15" />

      <g opacity="0.15">
        <path d="M100,300 C200,200 300,350 150,450 C50,400 50,350 100,300 Z" fill="#3ab795" />
        <path d="M1000,150 C1100,50 1150,200 1050,250 C950,200 950,200 1000,150 Z" fill="#3ab795" />
        <circle cx="250" cy="150" r="100" fill="#3ab795" opacity="0.2" />
        <circle cx="950" cy="480" r="120" fill="#26755a" opacity="0.2" />

        <path d="M0,400 Q150,350 300,400 Q450,450 600,400 Q750,350 900,400 Q1050,450 1200,400"
              fill="none" stroke="#3ab795" strokeWidth="3" />
        <path d="M0,440 Q150,390 300,440 Q450,490 600,440 Q750,390 900,440 Q1050,490 1200,440"
              fill="none" stroke="#26755a" strokeWidth="2" />

        <path d="M0,600 Q150,550 300,600 Q450,650 600,600 Q750,550 900,600 Q1050,650 1200,600"
              fill="none" stroke="#3ab795" strokeWidth="3" />
        <path d="M0,640 Q150,590 300,640 Q450,690 600,640 Q750,590 900,640 Q1050,690 1200,640"
              fill="none" stroke="#26755a" strokeWidth="2" />
      </g>

      <g transform="translate(600,400) scale(2)" opacity="0.07">
        <path d="M0,-30 L10,-10 L-10,-10 Z"              fill="#3ab795" />
        <path d="M0,-30 L10,-10 L-10,-10 Z" transform="rotate(120)" fill="#3ab795" />
        <path d="M0,-30 L10,-10 L-10,-10 Z" transform="rotate(240)" fill="#3ab795" />
        <path d="M0,-35 A35,35 0 1,1 -30.31,-17.5 L-25.98,-15 A30,30 0 1,0 0,-30 Z"              fill="#3ab795" />
        <path d="M0,-35 A35,35 0 1,1 -30.31,-17.5 L-25.98,-15 A30,30 0 1,0 0,-30 Z" transform="rotate(120)" fill="#3ab795" />
        <path d="M0,-35 A35,35 0 1,1 -30.31,-17.5 L-25.98,-15 A30,30 0 1,0 0,-30 Z" transform="rotate(240)" fill="#3ab795" />
      </g>

      <g opacity="0.3">
        <circle cx="200" cy="100" r="1.5"  fill="#5ab795" />
        <circle cx="350" cy="200" r="1.5"  fill="#5ab795" />
        <circle cx="500" cy="150" r="1.5"  fill="#5ab795" />
        <circle cx="700" cy="250" r="1.5"  fill="#5ab795" />
        <circle cx="850" cy="100" r="1.5"  fill="#5ab795" />
        <circle cx="950" cy="300" r="1.5"  fill="#5ab795" />
        <circle cx="300" cy="400" r="1.5"  fill="#5ab795" />
        <circle cx="600" cy="350" r="1.5"  fill="#5ab795" />
        <circle cx="800" cy="450" r="1.5"  fill="#5ab795" />
        <circle cx="1100" cy="200" r="1.5" fill="#5ab795" />
        <circle cx="150"  cy="150" r="1.5" fill="#5ab795" />
        <circle cx="450"  cy="250" r="1.5" fill="#5ab795" />
        <circle cx="750"  cy="300" r="1.5" fill="#5ab795" />
        <circle cx="900"  cy="150" r="1.5" fill="#5ab795" />
        <circle cx="250"  cy="350" r="1.5" fill="#5ab795" />
        <circle cx="400"  cy="500" r="1.5" fill="#5ab795" />
        <circle cx="650"  cy="550" r="1.5" fill="#5ab795" />
        <circle cx="900"  cy="500" r="1.5" fill="#5ab795" />
        <circle cx="1050" cy="550" r="1.5" fill="#5ab795" />
        <circle cx="200"  cy="600" r="1.5" fill="#5ab795" />
        <circle cx="500"  cy="650" r="1.5" fill="#5ab795" />
        <circle cx="800"  cy="600" r="1.5" fill="#5ab795" />
        <circle cx="100" cy="500" r="1.5" fill="#5ab795" />
        <circle cx="350" cy="550" r="1.5" fill="#5ab795" />
        <circle cx="550" cy="250" r="1.5" fill="#5ab795" />
        <circle cx="1050" cy="350" r="1.5" fill="#5ab795" />
        <circle cx="1150" cy="450" r="1.5" fill="#5ab795" />
        <circle cx="50"  cy="250" r="1.5" fill="#5ab795" />
        <circle cx="650" cy="150" r="1.5" fill="#5ab795" />
        <circle cx="950" cy="650" r="1.5" fill="#5ab795" />
      </g>
    </svg>

    <svg
      viewBox="0 0 1200 800"
      xmlns="http://www.w3.org/2000/svg"
      className="w-full h-full md:scale-100 scale-150 origin-center md:opacity-100 opacity-20 dark:hidden"
    >
      <defs>
        <linearGradient id="bgGradientLight" x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#ecfdf5" />
          <stop offset="100%" stopColor="#d1fae5" />
        </linearGradient>

        <pattern id="leafPatternLight" patternUnits="userSpaceOnUse" width="120" height="120" patternTransform="rotate(10)">
          <path d="M40,60 Q65,20 90,60 Q65,100 40,60 Z"
                fill="none" stroke="#6ee7b7" strokeWidth="1.5" opacity="0.25" />
        </pattern>

        <pattern id="wavePatternLight" patternUnits="userSpaceOnUse" width="200" height="100">
          <path d="M0,50 Q50,0 100,50 Q150,100 200,50"
                fill="none" stroke="#34d399" strokeWidth="1.5" opacity="0.2" />
        </pattern>

        <pattern id="hexPatternLight" patternUnits="userSpaceOnUse" width="150" height="170" patternTransform="scale(0.7) rotate(5)">
          <path d="M75,25 L125,60 L125,110 L75,145 L25,110 L25,60 Z"
                fill="none" stroke="#34d399" strokeWidth="1.5" opacity="0.15" />
        </pattern>
      </defs>

      <rect width="100%" height="100%" fill="url(#bgGradientLight)" />
      <rect width="100%" height="100%" fill="url(#leafPatternLight)" />
      <rect width="100%" height="100%" fill="url(#wavePatternLight)" opacity="0.8" />
      <rect width="100%" height="100%" fill="url(#hexPatternLight)" />
    </svg>
  </div>
);

const TimelineItem = ({
  year, title, description, isLeft = false,
}: { year: string; title: string; description: string; isLeft?: boolean }) => (
  <div className={`timeline-item relative ${isLeft ? 'md:text-right' : ''} mb-12 md:mb-0`}>
    <div className={`md:flex items-center ${isLeft ? 'md:flex-row-reverse' : ''}`}>
      <div className="hidden md:flex w-16 h-16 items-center justify-center bg-primary-100 dark:bg-primary-500/10 rounded-full border-4 border-neutral-200 dark:border-neutral-900 z-10 font-bold text-primary-600 dark:text-primary-400">
        {year}
      </div>
      <div className={`md:w-5/12 bg-white/70 dark:bg-neutral-900/50 backdrop-blur-sm rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800/50 ${isLeft ? 'md:mr-8' : 'md:ml-8'} transform transition-all duration-300 hover:shadow-lg hover:shadow-primary-500/10`}>
        <span className="inline-block md:hidden text-primary-600 dark:text-primary-400 text-sm font-semibold mb-2">
          {year}
        </span>
        <h3 className="text-xl font-display font-semibold text-neutral-900 dark:text-white mb-3">{title}</h3>
        <p className="text-neutral-600 dark:text-neutral-300">{description}</p>
      </div>
    </div>
  </div>
);

const CountUp = ({
  end, duration = 2, decimals = 0,
}: { end: number; duration?: number; decimals?: number }) => {
  const [count, setCount] = useState(0);
  useEffect(() => {
    let start: number | null = null, raf: number;
    const step = (t: number) => {
      if (!start) start = t;
      const p = Math.min((t - start) / (duration * 1000), 1);
      setCount(p * end);
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [end, duration]);
  return <>{count.toFixed(decimals)}</>;
};

const AboutSection = () => {
  const ref               = useRef<HTMLDivElement>(null);
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const ctx = gsap.context(() => {
      const fadeStagger = (sel: string, y = 30) =>
        gsap.from(sel, {
          y, opacity: 0, duration: 0.8, stagger: 0.15,
          scrollTrigger: { trigger: sel, start: 'top center+=100', toggleActions: 'play none none reverse' },
        });

      fadeStagger('.hero-content > *', 20);
      fadeStagger('.story-content');
      fadeStagger('.timeline-item');
      fadeStagger('.value-card');
      fadeStagger('.mission-content');

      gsap.from('.feature-card', {
        y: 50, opacity: 0, duration: 0.8, stagger: 0.15,
        scrollTrigger: { trigger: '.features-section', start: 'top center+=100' },
      });

      gsap.from('.quote-container', {
        y: 40, opacity: 0, duration: 1,
        scrollTrigger: { trigger: '.quote-container', start: 'top bottom-=100' },
      });
    }, ref);
    return () => ctx.revert();
  }, []);

  useEffect(() => {
    const el = document.getElementById('impact-stats');
    if (!el) return;
    const io = new IntersectionObserver(([e]) => e.isIntersecting && setStatsVisible(true), { threshold: 0.15 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const principles = [
    { icon: Leaf,        title: 'Sustainable Shopping',  desc: 'Making conscious choices that consider environmental, social & economic impacts.' },
    { icon: Globe2,      title: 'Local Focus',           desc: 'Supporting neighbourhood producers to cut emissions & boost community economy.' },
    { icon: ShieldCheck, title: 'Verified Deals',        desc: 'Every deal is vetted for quality, authenticity and ethical practice.' },
    { icon: Users,       title: 'Community Driven',      desc: 'Collective demand for eco-options makes sustainability the norm.' },
    { icon: Recycle,     title: 'Circular Economy',      desc: 'Durable, recyclable products keep resources in the loop.' },
    { icon: Heart,       title: 'Ethical Sourcing',      desc: 'Fair wages & safe working conditions across the supply chain.' },
    { icon: Award,       title: 'Quality Assurance',     desc: 'Long-lasting goods give better value and less waste.' },
    { icon: Zap,         title: 'Energy Efficiency',     desc: 'Renewables & low-carbon logistics shrink every product’s footprint.' },
  ];

  const coreValues = [
    { icon: <LeafIcon   className="w-6 h-6" />, title: 'Environmental Consciousness', desc: 'Minimising ecological impact in all we do.' },
    { icon: <HeartIcon  className="w-6 h-6" />, title: 'Community Empowerment',      desc: 'Stronger local economies, richer social ties.' },
    { icon: <BadgeCheck className="w-6 h-6" />, title: 'Ethical Transparency',       desc: 'Full disclosure of sourcing & production.' },
    { icon: <Sparkles   className="w-6 h-6" />, title: 'Continuous Innovation',      desc: 'Relentless pursuit of better solutions.' },
  ];

  const stats = [
    { end: 45,  suffix: '%', label: 'Carbon Reduction'      },
    { end: 120, suffix: '+', label: 'Local Businesses'      },
    { end: 5.2, suffix: 'K', label: 'Eco-Users', decimals: 1 },
    { end: 87,  suffix: '%', label: 'Sustainability Score'  },
  ];

  const timeline = [
    { year: '2022', title: 'The Spark',        description: 'Initial idea born at a local farmers’ market.' },
    { year: '2023', title: 'Development',      description: 'MVP built & first partners joined.', isLeft: true },
    { year: '2024', title: 'Official Launch',  description: 'Nation-wide roll-out connecting shoppers & brands.' },
    { year: '2025', title: 'Growing Impact',   description: 'Community & partner network expanding fast.', isLeft: true },
  ];

  return (
    <section ref={ref} id="about" className="relative overflow-hidden pt-20 md:pt-24 lg:pt-28">
      <SustainabilityBackground />
      <div className="absolute inset-0 -z-30 bg-gradient-to-br from-gray-50 to-gray-100 dark:bg-transparent" />

      <div className="hero-content text-center max-w-4xl mx-auto px-4 mb-20">
        <h1 className="text-4xl sm:text-5xl md:text-6xl font-display font-bold bg-gradient-to-r from-primary-300 via-neutral-800 dark:via-white to-accent-300 bg-clip-text text-transparent mb-6">
          Our Journey to Revolutionize Shopping
        </h1>
        <p className="text-lg sm:text-xl text-neutral-600 dark:text-neutral-300 mb-8 max-w-3xl mx-auto">
          DealOpia sprang from one simple question: <em>why isn’t finding ethical, sustainable
          deals as easy as any other purchase?</em>
        </p>
        <a href="#our-story" className="bg-primary-500 hover:bg-primary-600 text-white px-6 sm:px-8 py-3 rounded-full font-medium transition-colors inline-block">
          Discover the Story
        </a>
      </div>

      <section id="our-story" className="story-section py-16 md:py-20 bg-neutral-100/80 dark:bg-neutral-950/50 backdrop-blur-sm">
        <div className="story-content max-w-3xl mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-8 text-neutral-900 dark:text-white">
            The Story Behind DealOpia
          </h2>
          <div className="bg-white/60 dark:bg-neutral-900/40 backdrop-blur-sm rounded-2xl p-6 md:p-8 border border-neutral-200 dark:border-neutral-800/50 space-y-6 text-neutral-700 dark:text-neutral-300">
            <p>It started with a clash between my sustainable values and the convenience of typical e-commerce.</p>
            <p>At a 2022 farmers’ market I heard artisans share their eco-friendly practices yet struggle online — the spark for DealOpia.</p>
            <p>Our mission: make ethical shopping effortless for consumers and prosperous for responsible businesses.</p>
          </div>
        </div>
      </section>

      <section className="timeline-section py-16 md:py-20">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-12">Our Journey</h2>
          <div className="relative">
            <div className="absolute hidden md:block left-1/2 -translate-x-1/2 h-full w-1 bg-primary-300/30 dark:bg-primary-500/20" />
            <div className="space-y-12 md:space-y-24">
              {timeline.map((t, i) => <TimelineItem key={i} {...t} />)}
            </div>
          </div>
        </div>
      </section>

      <section className="values-section py-16 md:py-20 bg-neutral-100/80 dark:bg-neutral-950/50 backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <h2 className="text-3xl md:text-4xl font-display font-bold text-center mb-12">Our Core Values</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            {coreValues.map((v, i) => (
              <div key={i} className="value-card bg-white/60 dark:bg-neutral-900/40 backdrop-blur-sm rounded-2xl p-6 border border-neutral-200 dark:border-neutral-800/50 hover:shadow-lg hover:shadow-primary-500/10 transition">
                <div className="bg-primary-100 dark:bg-primary-500/10 w-12 h-12 rounded-xl flex items-center justify-center mb-4 text-primary-600 dark:text-primary-400">
                  {v.icon}
                </div>
                <h3 className="text-xl font-display font-semibold mb-3">{v.title}</h3>
                <p className="text-neutral-600 dark:text-neutral-300">{v.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="impact-stats" className="py-16 md:py-20">
        <div className="max-w-3xl mx-auto bg-white/70 dark:bg-neutral-900/60 backdrop-blur-sm rounded-2xl p-6 md:p-8 border border-neutral-200 dark:border-neutral-800/50 mx-4 sm:mx-auto">
          <h3 className="text-2xl font-display font-bold text-center mb-8">Our Impact</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 text-center">
            {stats.map((s, i) => (
              <div key={i}>
                <div className="text-primary-500 dark:text-primary-400 font-display font-bold text-3xl sm:text-4xl mb-2">
                  {statsVisible ? <CountUp end={s.end} decimals={s.decimals} /> : 0}
                  {s.suffix}
                </div>
                <p className="text-neutral-700 dark:text-neutral-300 text-sm">{s.label}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="features-section py-16 md:py-20 bg-gray-50/80 dark:bg-transparent backdrop-blur-sm">
        <div className="container mx-auto px-4">
          <h3 className="text-2xl md:text-3xl font-display font-bold text-center mb-10">
            Our <span className="text-primary-600 dark:text-primary-400">Sustainability</span> Principles
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            {principles.map(({ icon: Icon, title, desc }, i) => (
              <div key={i} className="feature-card bg-white/70 dark:bg-neutral-900/60 backdrop-blur-sm rounded-2xl p-6 border border-gray-200 dark:border-neutral-800/50 hover:border-primary-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-primary-500/10">
                <div className="bg-primary-500/15 w-14 h-14 rounded-xl flex items-center justify-center mb-4">
                  <Icon className="w-7 h-7 text-primary-500 dark:text-primary-400" />
                </div>
                <h4 className="text-xl font-display font-semibold mb-3">{title}</h4>
                <p className="text-neutral-700 dark:text-neutral-300">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="quote-container py-16 md:py-20">
        <div className="max-w-4xl mx-auto text-center px-4">
          <svg className="w-12 h-12 mx-auto mb-4 text-primary-500 dark:text-primary-400 opacity-50" viewBox="0 0 24 24" fill="currentColor">
            <path d="M14.017 21v-7.391c0-5.704 3.731-9.57 8.983-10.609l.995 2.151c-2.432.917-3.995 3.638-3.995 5.849h4v10h-9.983zm-14.017 0v-7.391c0-5.704 3.748-9.57 9-10.609l.996 2.151c-2.433.917-3.996 3.638-3.996 5.849h3.983v10h-9.983z" />
          </svg>
          <p className="text-xl sm:text-2xl md:text-3xl font-display font-medium text-neutral-900 dark:text-white mb-6 leading-relaxed">
            "The greatest threat to our planet is the belief that someone else will save it."
          </p>
          <div className="flex items-center justify-center">
            <div className="h-px w-12 bg-primary-500/30 mr-4" />
            <p className="text-primary-600 dark:text-primary-400 font-semibold">DealOpia Philosophy</p>
            <div className="h-px w-12 bg-primary-500/30 ml-4" />
          </div>
        </div>
      </section>
    </section>
  );
};

export default AboutSection;
