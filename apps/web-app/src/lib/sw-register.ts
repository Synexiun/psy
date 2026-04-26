'use client';

export function registerSW(): void {
  if (process.env.NODE_ENV !== 'production') return;
  if (typeof window === 'undefined') return;
  if (!navigator.serviceWorker) return;

  const doRegister = () => {
    navigator.serviceWorker.register('/sw.js').catch((err) => {
      console.error('SW registration failed:', err);
    });
  };

  if (document.readyState === 'complete') {
    doRegister();
  } else {
    window.addEventListener('load', doRegister, { once: true });
  }
}
