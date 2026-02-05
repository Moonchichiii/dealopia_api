import { useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import gsap from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { Github, Tag } from 'lucide-react';

import Privacy from '@/components/layout/Privacy';
import Terms from '@/components/layout/Terms';

gsap.registerPlugin(ScrollTrigger);

const useFooterAnimation = (footerRef: React.RefObject<HTMLElement>) => {
  useEffect(() => {
    const ctx = gsap.context(() => {
      const footerItems = footerRef.current?.querySelectorAll('.footer-item');

      if (footerItems) {
        gsap.set(footerItems, { opacity: 0 });
        gsap.to(footerItems, {
          opacity: 1,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: footerRef.current,
            start: 'top bottom-=100',
            toggleActions: 'play none none reverse'
          }
        });
      }
    });

    return () => ctx.revert();
  }, [footerRef]);
};

type FooterLinkProps = {
  to: string;
  label: string;
  component?: React.ReactNode;
};

// Updated FooterLink for dark mode support
const FooterLink = ({ to, label, component }: FooterLinkProps) => (
  <li>
    {component ? (
      <Link to={to} className="text-neutral-500 dark:text-neutral-400 hover:text-primary-500 dark:hover:text-white transition-colors">
        {label}
      </Link>
    ) : (
      <Link to={to} className="text-neutral-500 dark:text-neutral-400 hover:text-primary-500 dark:hover:text-white transition-colors">
        {label}
      </Link>
    )}
  </li>
);

type FooterSectionProps = {
  title: string;
  links: FooterLinkProps[];
};

// Updated FooterSection for dark mode support
const FooterSection = ({ title, links }: FooterSectionProps) => (
  <div className="footer-item">
    <h3 className="font-display font-semibold text-neutral-900 dark:text-white mb-4">{title}</h3>
    <ul className="space-y-2">
      {links.map((link) => (
        <FooterLink key={link.to} {...link} />
      ))}
    </ul>
  </div>
);

// Updated Footer component for dark mode support
const Footer: React.FC = () => {
  const footerRef = useRef<HTMLElement>(null);
  useFooterAnimation(footerRef);

  const companyLinks = [
    { to: "/about", label: "About Us" },
    { to: "/privacy", label: "Privacy Policy", component: <Privacy /> },
    { to: "/terms", label: "Terms of Service", component: <Terms /> }
  ];

  const supportLinks = [
    { to: "/faq", label: "FAQ" },
    { to: "/contact", label: "Contact Us" },
    { to: "/help", label: "Help Center" }
  ];

  return (
    <footer
      ref={footerRef}
      // Updated background and border for dark mode
      className="border-t border-neutral-200 dark:border-neutral-800/50 bg-neutral-50/50 dark:bg-neutral-950/50 backdrop-blur-xl"
      style={{ minHeight: '350px' }}
    >
      <div className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div className="footer-item">
            <Link to="/" className="flex items-center space-x-2 mb-4">
              {/* Logo styling remains consistent across themes */}
              <div className="bg-primary-500/10 p-2 rounded-xl">
                <Tag className="w-6 h-6 text-primary-500 dark:text-primary-400" />
              </div>
              <span className="text-xl font-display font-bold bg-gradient-to-r from-primary-500 to-accent-500 dark:from-primary-400 dark:to-accent-400 text-transparent bg-clip-text inline-block">
                DealOpia
              </span>
            </Link>
            {/* Updated text color for dark mode */}
            <p className="text-neutral-600 dark:text-neutral-400 text-sm">
              Discover the best local deals while supporting sustainable shopping practices.
            </p>
          </div>

          <FooterSection title="Company" links={companyLinks} />
          <FooterSection title="Support" links={supportLinks} />

          <div className="footer-item">
            {/* Updated heading color for dark mode */}
            <h3 className="font-display font-semibold text-neutral-900 dark:text-white mb-4">Follow Us</h3>
            <div className="flex space-x-4">
              <a
                href="https://github.com"
                target="_blank"
                rel="noopener noreferrer"
                // Updated link color for dark mode
                className="text-neutral-500 dark:text-neutral-400 hover:text-primary-500 dark:hover:text-white transition-colors"
              >
                <Github size={24} />
              </a>

            </div>
          </div>
        </div>

        {/* Updated copyright section for dark mode */}
        <div className="footer-item mt-12 pt-8 border-t border-neutral-200 dark:border-neutral-800/50 text-center text-neutral-500 dark:text-neutral-400 text-sm">
          <p>© {new Date().getFullYear()} DealOpia. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;