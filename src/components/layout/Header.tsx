import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Home, BookOpen, Sparkles, Menu, X, Sun, Moon } from 'lucide-react';

const leftItems = [
  { label: 'Home', href: '/', icon: Home },
  { label: 'How it works', href: '/how-it-works', icon: BookOpen },
];

const rightItems = [
  { label: 'Story', href: '/story', icon: Sparkles },
  { label: 'AI extract', href: '/extract', icon: Sparkles },
];

const NavLink = ({ href, icon: Icon, label }: { href: string; icon: React.ComponentType<{ className?: string }>; label: string }) => (
  <Link
    to={href}
    className="group flex items-center gap-1.5 text-sm font-medium text-emerald-900/70 hover:text-emerald-900 transition-colors whitespace-nowrap"
  >
    <Icon className="w-4 h-4 opacity-70 group-hover:opacity-100" />
    <span>{label}</span>
  </Link>
);

export function Header() {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  return (
    <>
      <header className="fixed top-0 inset-x-0 z-50 h-16 flex px-0">
        {/* Left Side Bar */}
        <div className="flex-1 h-10 bg-peach-50 relative min-w-0">
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <line x1="0" y1="39.5" x2="100%" y2="39.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
            <line x1="0" y1="36.5" x2="100%" y2="36.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
          </svg>
        </div>

        {/* Notch Container */}
        <div className="flex h-16 relative z-10 shrink-0 -ml-px">
          {/* Left Slice */}
          <div className="w-[50px] h-full relative shrink-0">
            <div className="absolute inset-0 bg-peach-50" style={{ clipPath: "path('M0 0 H50 V64 C25 64 25 40 0 40 Z')" }} />
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 50 64">
              <path d="M0 39.5 C25 39.5 25 63.5 50 63.5" fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
              <path d="M0 36.5 C25 36.5 25 60.5 50 60.5" fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
            </svg>
          </div>

          {/* Center Slice */}
          <div className="flex-1 h-full relative min-w-0 -ml-px">
            <div className="absolute inset-0 bg-peach-50">
              <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="none">
                <line x1="0" y1="63.5" x2="100%" y2="63.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
                <line x1="0" y1="60.5" x2="100%" y2="60.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
              </svg>
            </div>

            <div className="relative w-full h-full flex items-end justify-between pb-2 px-4 md:px-8">
              {/* Desktop Left Nav */}
              <nav className="hidden md:flex gap-8 mb-1 shrink-0">
                {leftItems.map((item) => (
                  <NavLink key={item.label} {...item} />
                ))}
              </nav>

              {/* Mobile Menu Button */}
              <button
                className="md:hidden mb-1 p-1 text-emerald-900/70 hover:text-emerald-900 transition-colors"
                onClick={() => setIsOpen((o) => !o)}
                aria-label="Toggle menu"
              >
                {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>

              {/* Logo */}
              <div className="flex justify-center shrink-0 mx-2 md:mx-4 mt-1">
                <Link to="/" className="flex items-center justify-center group">
                  <span className="font-display text-xl font-extrabold text-emerald-800 hover:scale-105 transition-transform">
                    Mzima
                  </span>
                </Link>
              </div>

              {/* Desktop Right Nav */}
              <nav className="hidden md:flex gap-6 items-center shrink-0">
                {rightItems.map((item) => (
                  <NavLink key={item.label} {...item} />
                ))}
                <div className="flex gap-4 pl-4 border-l border-emerald-900/10 shrink-0 items-center">
                  <button
                    type="button"
                    className="flex items-center justify-center w-9 h-9 rounded-full hover:bg-emerald-900/5 transition-colors text-emerald-900/70 hover:text-emerald-900"
                    aria-label="Theme toggle"
                    onClick={() => {
                      document.documentElement.classList.toggle('dark');
                    }}
                  >
                    {mounted ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                  </button>
                  <Link to="/login" className="text-sm font-medium text-emerald-900/70 hover:text-emerald-900 transition-colors whitespace-nowrap">
                    Log in
                  </Link>
                  <Link
                    to="/sign-up"
                    className="px-3 py-1.5 text-sm font-medium text-white bg-emerald-900 rounded-2xl hover:bg-emerald-800 transition-colors shadow-sm shadow-emerald-900/10 whitespace-nowrap"
                  >
                    Sign up
                  </Link>
                </div>
              </nav>

              {/* Mobile Right Actions */}
              <div className="md:hidden flex items-center gap-2 mb-1">
                <button
                  type="button"
                  className="flex items-center justify-center w-9 h-9 rounded-full hover:bg-emerald-900/5 transition-colors text-emerald-900/70 hover:text-emerald-900"
                  aria-label="Theme toggle"
                >
                  <Sun className="w-5 h-5" />
                </button>
              </div>
            </div>
          </div>

          {/* Right Slice */}
          <div className="w-[50px] h-full relative shrink-0 -ml-px">
            <div className="absolute inset-0 bg-peach-50" style={{ clipPath: "path('M0 0 H50 V40 C25 40 25 64 0 64 Z')" }} />
            <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 50 64">
              <path d="M0 63.5 C25 63.5 25 39.5 50 39.5" fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
              <path d="M0 60.5 C25 60.5 25 36.5 50 36.5" fill="none" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
            </svg>
          </div>
        </div>

        {/* Right Side Bar */}
        <div className="flex-1 h-10 bg-peach-50 relative min-w-0 -ml-px">
          <svg className="absolute inset-0 w-full h-full" preserveAspectRatio="none">
            <line x1="0" y1="39.5" x2="100%" y2="39.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
            <line x1="0" y1="36.5" x2="100%" y2="36.5" stroke="currentColor" strokeOpacity={0.05} strokeWidth={0.5} className="text-emerald-900" />
          </svg>
        </div>
      </header>

      {/* Mobile Menu */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-x-0 top-16 z-40 bg-peach-50 border-b border-emerald-900/5 p-4 md:hidden shadow-lg"
          >
            <nav className="flex flex-col gap-2">
              {[...leftItems, ...rightItems].map((item) => (
                <Link
                  key={item.label}
                  to={item.href}
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-emerald-900/5 transition-colors"
                  onClick={() => setIsOpen(false)}
                >
                  <item.icon className="w-5 h-5 opacity-70" />
                  <span className="font-medium text-emerald-900/90">{item.label}</span>
                </Link>
              ))}
              <div className="h-px bg-emerald-900/10 my-2" />
              <div className="flex flex-col gap-2">
                <Link
                  to="/login"
                  className="flex items-center gap-3 p-3 rounded-lg hover:bg-emerald-900/5 transition-colors font-medium text-emerald-900/90"
                  onClick={() => setIsOpen(false)}
                >
                  Log in
                </Link>
                <Link
                  to="/sign-up"
                  className="flex items-center justify-center gap-2 p-3 rounded-lg bg-emerald-900 text-white font-medium mt-2"
                  onClick={() => setIsOpen(false)}
                >
                  Sign up
                </Link>
              </div>
            </nav>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}