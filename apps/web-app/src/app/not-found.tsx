// Global fallback 404 — rendered when no locale can be determined (e.g. a
// request to /unknown-path that never matched the [locale] segment).
// Intentionally dependency-free: no Layout wrapper, no next-intl, no Clerk.
// Uses inline styles so it works even if Tailwind hasn't loaded.

export default function NotFound(): React.JSX.Element {
  return (
    <main
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        fontFamily: 'system-ui, sans-serif',
        textAlign: 'center',
        padding: '1.5rem',
        background: '#ffffff',
        color: '#0f172a',
      }}
    >
      <p
        style={{
          fontSize: '0.75rem',
          fontWeight: 600,
          letterSpacing: '0.1em',
          textTransform: 'uppercase',
          color: '#94a3b8',
          margin: 0,
        }}
      >
        404
      </p>

      <h1
        style={{
          marginTop: '1rem',
          fontSize: '2rem',
          fontWeight: 600,
          letterSpacing: '-0.02em',
          lineHeight: 1.2,
        }}
      >
        Page not found
      </h1>

      <p
        style={{
          marginTop: '0.75rem',
          fontSize: '0.875rem',
          lineHeight: 1.6,
          color: '#64748b',
          maxWidth: '24rem',
        }}
      >
        The page you&apos;re looking for doesn&apos;t exist or may have been moved.
      </p>

      <a
        href="/"
        style={{
          marginTop: '2rem',
          display: 'inline-flex',
          alignItems: 'center',
          height: '2.5rem',
          padding: '0 1.25rem',
          borderRadius: '0.375rem',
          background: '#6366f1',
          color: '#ffffff',
          fontSize: '0.875rem',
          fontWeight: 500,
          textDecoration: 'none',
        }}
      >
        Go home
      </a>
    </main>
  );
}
