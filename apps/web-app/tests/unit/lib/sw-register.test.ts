import { describe, it, expect, vi, afterEach } from 'vitest';

describe('registerSW', () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllEnvs();
    vi.resetModules();
  });

  it('does nothing outside production', async () => {
    // NODE_ENV=test in Vitest — not production
    const addEventListenerSpy = vi.spyOn(window, 'addEventListener');
    const { registerSW } = await import('@/lib/sw-register');
    registerSW();
    expect(addEventListenerSpy).not.toHaveBeenCalled();
  });

  it('does nothing when serviceWorker is not supported', async () => {
    // Simulate production but no SW support
    vi.stubEnv('NODE_ENV', 'production');
    const origSW = Object.getOwnPropertyDescriptor(navigator, 'serviceWorker');
    Object.defineProperty(navigator, 'serviceWorker', { value: undefined, configurable: true });

    const { registerSW } = await import('@/lib/sw-register');
    registerSW(); // should not throw

    if (origSW) {
      Object.defineProperty(navigator, 'serviceWorker', origSW);
    }
  });

  it('registers /sw.js immediately when readyState is complete', async () => {
    vi.stubEnv('NODE_ENV', 'production');
    const registerMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: registerMock },
      configurable: true,
    });
    Object.defineProperty(document, 'readyState', {
      value: 'complete',
      configurable: true,
      writable: true,
    });

    const { registerSW } = await import('@/lib/sw-register');
    registerSW();

    expect(registerMock).toHaveBeenCalledWith('/sw.js');
  });

  it('defers registration via load event when readyState is not complete', async () => {
    vi.stubEnv('NODE_ENV', 'production');
    const registerMock = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(navigator, 'serviceWorker', {
      value: { register: registerMock },
      configurable: true,
    });
    Object.defineProperty(document, 'readyState', {
      value: 'loading',
      configurable: true,
      writable: true,
    });

    const { registerSW } = await import('@/lib/sw-register');
    registerSW();

    // register should NOT have been called synchronously
    expect(registerMock).not.toHaveBeenCalled();

    // fire the load event to trigger the deferred registration
    window.dispatchEvent(new Event('load'));

    expect(registerMock).toHaveBeenCalledWith('/sw.js');
  });
});
