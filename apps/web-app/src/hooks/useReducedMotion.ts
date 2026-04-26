'use client';
import { useEffect, useState } from 'react';

export function useReducedMotion(): boolean {
  const [reduced, setReduced] = useState<boolean>(() => {
    if (typeof window === 'undefined') return false;
    const ambientOff = document.documentElement.getAttribute('data-ambient-motion') === 'off';
    const osReduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    return ambientOff || osReduced;
  });

  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const update = () => {
      const ambientOff = document.documentElement.getAttribute('data-ambient-motion') === 'off';
      setReduced(ambientOff || mq.matches);
    };
    mq.addEventListener('change', update);
    const observer = new MutationObserver(update);
    observer.observe(document.documentElement, { attributes: true, attributeFilter: ['data-ambient-motion'] });
    return () => {
      mq.removeEventListener('change', update);
      observer.disconnect();
    };
  }, []);

  return reduced;
}
