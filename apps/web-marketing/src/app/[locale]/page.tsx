import { useTranslations } from 'next-intl';
import { setRequestLocale } from 'next-intl/server';
import { buildButtonClasses } from '@disciplineos/design-system/primitives/web-utils';

// ---------------------------------------------------------------------------
// Entry point — Next.js 15 App Router page (server component)
// ---------------------------------------------------------------------------

export default function MarketingHomePage({
  params,
}: {
  params: Promise<{ locale: string }>;
}): React.JSX.Element {
  return <HomeContent paramsPromise={params} />;
}

async function HomeContent({
  paramsPromise,
}: {
  paramsPromise: Promise<{ locale: string }>;
}) {
  const { locale } = await paramsPromise;
  setRequestLocale(locale);
  return <HomeInner locale={locale} />;
}

// ---------------------------------------------------------------------------
// Inline SVG icons — no external deps, tree-shaken at build time
// ---------------------------------------------------------------------------

function AppleIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M18.71 19.5c-.83 1.24-1.71 2.45-3.05 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z" />
    </svg>
  );
}

function AndroidIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="currentColor"
      aria-hidden="true"
    >
      <path d="M17.523 15.341a.498.498 0 01-.499-.499v-4.95a.499.499 0 01.999 0v4.95a.498.498 0 01-.5.499m-11.046 0a.498.498 0 01-.499-.499v-4.95a.499.499 0 01.999 0v4.95a.499.499 0 01-.5.499M7.21 6.244l-.98-1.696a.199.199 0 00-.274-.073.2.2 0 00-.073.274l.993 1.72A6.356 6.356 0 0012 5.13a6.358 6.358 0 005.124 1.339l.993-1.72a.2.2 0 00-.073-.274.199.199 0 00-.274.073L16.79 6.244A6.378 6.378 0 0012 5.13a6.376 6.376 0 00-4.79 1.114M9.5 9a.5.5 0 110-1 .5.5 0 010 1m5 0a.5.5 0 110-1 .5.5 0 010 1M5.5 7.5h13A1.5 1.5 0 0120 9v7.5a1.5 1.5 0 01-1.5 1.5h-1v2.5a1 1 0 01-2 0V18h-7v2.5a1 1 0 01-2 0V18h-1A1.5 1.5 0 014 16.5V9A1.5 1.5 0 015.5 7.5z" />
    </svg>
  );
}

function MenuIcon() {
  return (
    <svg
      width="24"
      height="24"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <line x1="3" y1="6" x2="21" y2="6" />
      <line x1="3" y1="12" x2="21" y2="12" />
      <line x1="3" y1="18" x2="21" y2="18" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg
      width="16"
      height="16"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.5"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      className="shrink-0 text-[hsl(217,91%,52%)]"
    >
      <polyline points="20 6 9 17 4 12" />
    </svg>
  );
}

// ---------------------------------------------------------------------------
// Top Navigation
// ---------------------------------------------------------------------------

function TopNav() {
  return (
    <header className="sticky top-0 z-50 border-b border-[hsl(220,14%,93%)] bg-white shadow-sm">
      <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-3">
        {/* Logo */}
        <a href="/" className="flex flex-col leading-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[hsl(217,91%,52%)] focus-visible:ring-offset-2 rounded-sm">
          <span className="text-lg font-semibold text-[hsl(222,47%,11%)]">Discipline OS</span>
          <span className="text-[11px] text-[hsl(215,16%,57%)] font-normal tracking-wide">
            Close the loop on urges
          </span>
        </a>

        {/* Desktop nav links */}
        <nav aria-label="Primary navigation" className="hidden md:flex items-center gap-6">
          <a
            href="#how-it-works"
            className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
          >
            How it works
          </a>
          <a
            href="#features"
            className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
          >
            Features
          </a>
          <a
            href="#pricing"
            className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
          >
            Pricing
          </a>
          <a
            href="#safety"
            className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
          >
            Safety
          </a>
        </nav>

        {/* CTA + mobile hamburger */}
        <div className="flex items-center gap-3">
          <a
            href="#download"
            className={`${buildButtonClasses('primary', 'sm')} hidden md:inline-flex`}
          >
            Get early access
          </a>
          {/* Mobile hamburger — CSS-only placeholder; JS accordion can be layered in later */}
          <button
            type="button"
            aria-label="Open navigation menu"
            className="flex items-center justify-center md:hidden rounded-md p-1.5 text-[hsl(215,16%,47%)] hover:bg-[hsl(220,14%,96%)] transition-colors"
          >
            <MenuIcon />
          </button>
        </div>
      </div>
    </header>
  );
}

// ---------------------------------------------------------------------------
// Hero Section
// ---------------------------------------------------------------------------

function HeroSection({ t }: { t: ReturnType<typeof useTranslations> }) {
  return (
    <section
      aria-labelledby="hero-heading"
      className="relative overflow-hidden bg-white pt-20 pb-24 md:pt-28 md:pb-32"
    >
      {/* Background gradient blob — pure CSS, no img */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 -z-10"
        style={{
          background:
            'radial-gradient(ellipse 80% 60% at 60% -10%, hsl(217,91%,97%) 0%, transparent 70%), radial-gradient(ellipse 40% 40% at 90% 60%, hsl(173,58%,95%) 0%, transparent 60%)',
        }}
      />

      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-12 md:grid-cols-2 md:items-center">
          {/* Copy column */}
          <div className="space-y-6">
            <p className="inline-flex items-center gap-2 rounded-full bg-[hsl(217,91%,96%)] px-3 py-1 text-xs font-semibold uppercase tracking-widest text-[hsl(217,91%,52%)]">
              Evidence-based · Private by design
            </p>

            <h1
              id="hero-heading"
              className="text-4xl font-semibold leading-tight tracking-tight text-[hsl(222,47%,11%)] md:text-5xl md:leading-tight"
            >
              {t('marketing.hero.headline')}
            </h1>

            <p className="max-w-lg text-lg leading-relaxed text-[hsl(215,16%,47%)]">
              Discipline OS detects rising urges and delivers evidence-based interventions in the
              critical 60–180 second window.
            </p>

            {/* Download CTAs */}
            <div
              id="download"
              className="flex flex-wrap gap-3 pt-1"
            >
              <a
                href="https://apps.apple.com"
                className={`${buildButtonClasses('ghost', 'lg')} border border-[hsl(220,14%,83%)] gap-2`}
                rel="noopener noreferrer"
              >
                <AppleIcon />
                Download for iOS
              </a>
              <a
                href="https://play.google.com"
                className={`${buildButtonClasses('ghost', 'lg')} border border-[hsl(220,14%,83%)] gap-2`}
                rel="noopener noreferrer"
              >
                <AndroidIcon />
                Download for Android
              </a>
            </div>

            {/* Social proof */}
            <p className="text-sm text-[hsl(215,16%,57%)]">
              Used by 300+ people in closed beta&nbsp;·&nbsp;
              <span className="font-medium text-[hsl(215,16%,40%)]">4.8★ avg rating</span>
            </p>
          </div>

          {/* Hero image placeholder */}
          <div
            aria-hidden="true"
            className="relative mx-auto w-full max-w-sm md:max-w-none"
          >
            {/* Phone mockup frame */}
            <div
              className="relative mx-auto h-[480px] w-[260px] rounded-[2.5rem] border-4 border-[hsl(220,14%,82%)] bg-white shadow-2xl overflow-hidden"
              role="img"
              aria-label="App screenshot placeholder"
            >
              {/* Screen gradient — simulates app UI */}
              <div
                className="absolute inset-0"
                style={{
                  background:
                    'linear-gradient(160deg, hsl(217,91%,97%) 0%, hsl(217,91%,92%) 40%, hsl(173,58%,94%) 100%)',
                }}
              />
              {/* Notch */}
              <div className="absolute top-3 left-1/2 -translate-x-1/2 h-5 w-20 rounded-full bg-[hsl(220,14%,82%)]" />
              {/* Mock content bars */}
              <div className="absolute top-16 left-6 right-6 space-y-3">
                <div className="h-3 w-2/3 rounded-full bg-[hsl(217,91%,80%)] opacity-70" />
                <div className="h-10 w-full rounded-xl bg-white/60 shadow-sm" />
                <div className="h-10 w-full rounded-xl bg-white/60 shadow-sm" />
                <div className="mt-4 h-24 w-full rounded-2xl bg-white/80 shadow" />
                <div className="h-3 w-1/2 rounded-full bg-[hsl(173,58%,70%)] opacity-70" />
                <div className="h-3 w-3/4 rounded-full bg-[hsl(217,91%,80%)] opacity-60" />
              </div>
              {/* Bottom nav mock */}
              <div className="absolute bottom-0 left-0 right-0 h-16 bg-white/90 border-t border-[hsl(220,14%,90%)] flex items-center justify-around px-6">
                {[1, 2, 3, 4].map((i) => (
                  <div key={i} className="h-5 w-5 rounded-full bg-[hsl(217,91%,85%)]" />
                ))}
              </div>
            </div>
            {/* Floating badge */}
            <div className="absolute -bottom-4 -left-4 rounded-xl bg-white px-4 py-2.5 shadow-lg border border-[hsl(220,14%,90%)]">
              <p className="text-xs font-semibold text-[hsl(173,58%,39%)]">Urge handled ✓</p>
              <p className="text-xs text-[hsl(215,16%,57%)]">Resilience +1</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// How It Works Section
// ---------------------------------------------------------------------------

function HowItWorksSection() {
  const steps = [
    {
      icon: '📡',
      number: '01',
      headline: 'Urge detected',
      description:
        'Biometric signals and self-reports identify rising urge states before they peak.',
    },
    {
      icon: '⚡',
      number: '02',
      headline: 'Intervention delivered',
      description: 'A personalized coping tool arrives in the critical 60-second window.',
    },
    {
      icon: '📈',
      number: '03',
      headline: 'Outcome recorded',
      description: 'Every handled urge strengthens your resilience score.',
    },
  ];

  return (
    <section
      id="how-it-works"
      aria-labelledby="how-works-heading"
      className="bg-[hsl(220,14%,98%)] py-20 md:py-28"
    >
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2
            id="how-works-heading"
            className="text-3xl font-semibold tracking-tight text-[hsl(222,47%,11%)] md:text-4xl"
          >
            Three steps to reclaim control
          </h2>
          <p className="mt-3 text-[hsl(215,16%,47%)]">
            Designed around the neuroscience of the urge-action gap.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-3">
          {steps.map((step) => (
            <div
              key={step.number}
              className="relative rounded-2xl border border-[hsl(220,14%,90%)] bg-white p-8 shadow-sm"
            >
              {/* Step number badge */}
              <span className="inline-flex items-center justify-center rounded-full bg-[hsl(217,91%,96%)] px-2.5 py-0.5 text-xs font-bold text-[hsl(217,91%,52%)] mb-4">
                {step.number}
              </span>
              {/* Icon */}
              <div className="text-3xl mb-3" aria-hidden="true">
                {step.icon}
              </div>
              <h3 className="text-lg font-semibold text-[hsl(222,47%,11%)] mb-2">
                {step.headline}
              </h3>
              <p className="text-[hsl(215,16%,47%)] leading-relaxed">{step.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Features Section
// ---------------------------------------------------------------------------

function FeaturesSection() {
  const features = [
    {
      headline: 'On-device intelligence',
      body: 'State estimation runs locally. Your data never leaves your device for ML inference.',
      icon: '🛡️',
    },
    {
      headline: 'Evidence-based tools',
      body: '25 coping tools validated by clinical research. Not motivational quotes.',
      icon: '🔬',
    },
    {
      headline: 'Resilience streak',
      body: 'Track handled urges — not just clean days. Compassion-first framing.',
      icon: '🌱',
    },
    {
      headline: 'Clinical oversight',
      body: 'Share progress with your clinician. PHI-protected, audit-logged.',
      icon: '🩺',
    },
    {
      headline: 'Crisis-ready',
      body: 'One tap to a crisis line, always. Works offline. No login required.',
      icon: '🆘',
    },
    {
      headline: 'Four languages',
      body: 'English, French, Arabic, Persian. RTL supported natively.',
      icon: '🌐',
    },
  ];

  return (
    <section
      id="features"
      aria-labelledby="features-heading"
      className="bg-white py-20 md:py-28"
    >
      <div className="mx-auto max-w-6xl px-6">
        <div className="mb-12 text-center">
          <h2
            id="features-heading"
            className="text-3xl font-semibold tracking-tight text-[hsl(222,47%,11%)] md:text-4xl"
          >
            Built for the hardest moments
          </h2>
          <p className="mt-3 text-[hsl(215,16%,47%)]">
            Every decision in the product is shaped by clinical evidence and privacy principles.
          </p>
        </div>

        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.headline}
              className="rounded-2xl border border-[hsl(220,14%,90%)] bg-[hsl(220,14%,98%)] p-6 transition-shadow hover:shadow-md"
            >
              <div className="text-2xl mb-3" aria-hidden="true">
                {feature.icon}
              </div>
              <h3 className="text-base font-semibold text-[hsl(222,47%,11%)] mb-1.5">
                {feature.headline}
              </h3>
              <p className="text-sm leading-relaxed text-[hsl(215,16%,47%)]">{feature.body}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Pricing Section
// ---------------------------------------------------------------------------

const FREE_FEATURES = [
  '14-day urge log',
  '5 coping tools',
  'Basic check-ins',
  'Crisis access always free',
];

const PRO_FEATURES = [
  'Unlimited urge log',
  '25 coping tools',
  'Biometric signal (where available)',
  'Clinician sharing',
  'Weekly insight reports',
  '4 languages',
];

function PricingSection({ t }: { t: ReturnType<typeof useTranslations> }) {
  return (
    <section
      id="pricing"
      aria-labelledby="pricing-heading"
      className="bg-[hsl(220,14%,98%)] py-20 md:py-28"
    >
      <div className="mx-auto max-w-4xl px-6">
        <div className="mb-12 text-center">
          <h2
            id="pricing-heading"
            className="text-3xl font-semibold tracking-tight text-[hsl(222,47%,11%)] md:text-4xl"
          >
            {t('marketing.pricing.title')}
          </h2>
          <p className="mt-3 text-[hsl(215,16%,47%)]">
            Crisis access is always free. No exceptions.
          </p>
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Free plan */}
          <div className="rounded-2xl border border-[hsl(220,14%,88%)] bg-white p-8 shadow-sm">
            <p className="text-sm font-semibold uppercase tracking-widest text-[hsl(215,16%,57%)] mb-1">
              {t('marketing.pricing.freeTitle')}
            </p>
            <div className="flex items-baseline gap-1 mt-2 mb-6">
              <span className="text-4xl font-bold text-[hsl(222,47%,11%)]">$0</span>
              <span className="text-[hsl(215,16%,57%)]">/mo</span>
            </div>
            <ul className="space-y-3 mb-8" role="list">
              {FREE_FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-[hsl(215,16%,35%)]">
                  <CheckIcon />
                  {f}
                </li>
              ))}
            </ul>
            <a href="#download" className={`${buildButtonClasses('ghost', 'md')} w-full border border-[hsl(220,14%,83%)]`}>
              Start free
            </a>
          </div>

          {/* Pro plan */}
          <div className="relative rounded-2xl border-2 border-[hsl(217,91%,52%)] bg-white p-8 shadow-md">
            {/* Most popular badge */}
            <span className="absolute -top-3.5 left-1/2 -translate-x-1/2 inline-flex items-center rounded-full bg-[hsl(217,91%,52%)] px-3 py-1 text-xs font-semibold text-white shadow">
              Most popular
            </span>
            <p className="text-sm font-semibold uppercase tracking-widest text-[hsl(217,91%,52%)] mb-1">
              Pro
            </p>
            <div className="flex items-baseline gap-1 mt-2 mb-6">
              <span className="text-4xl font-bold text-[hsl(222,47%,11%)]">$9.99</span>
              <span className="text-[hsl(215,16%,57%)]">/mo</span>
            </div>
            <ul className="space-y-3 mb-8" role="list">
              {PRO_FEATURES.map((f) => (
                <li key={f} className="flex items-start gap-2 text-sm text-[hsl(215,16%,35%)]">
                  <CheckIcon />
                  {f}
                </li>
              ))}
            </ul>
            <a href="#download" className={`${buildButtonClasses('primary', 'md')} w-full`}>
              Start free trial
            </a>
          </div>
        </div>

        {/* Enterprise note */}
        <p className="mt-8 text-center text-sm text-[hsl(215,16%,57%)]">
          Enterprise plans for organizations available.{' '}
          <a
            href="mailto:hello@disciplineos.com"
            className="font-medium text-[hsl(217,91%,52%)] hover:underline"
          >
            Contact us.
          </a>
        </p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Safety Promise Section
// ---------------------------------------------------------------------------

function SafetySection({ t }: { t: ReturnType<typeof useTranslations> }) {
  return (
    <section
      id="safety"
      aria-labelledby="safety-heading"
      className="bg-white py-20 md:py-24"
    >
      <div className="mx-auto max-w-3xl px-6">
        <div className="rounded-2xl border border-[hsl(0,84%,60%)]/20 bg-[hsl(0,84%,97%)] p-10 text-center">
          <div className="text-3xl mb-4" aria-hidden="true">🆘</div>
          <h2
            id="safety-heading"
            className="text-2xl font-semibold text-[hsl(0,84%,30%)] md:text-3xl"
          >
            Crisis support is always free and always on
          </h2>
          <p className="mt-4 leading-relaxed text-[hsl(0,30%,40%)] max-w-xl mx-auto">
            Crisis access is never paywalled, never login-gated, and works with JavaScript
            disabled. It is a static page with direct phone numbers.
          </p>
          <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row sm:justify-center">
            <a
              href="/crisis"
              className={buildButtonClasses('crisis', 'lg')}
              data-analytics-event="crisis_cta_click"
            >
              {t('crisis.cta.primary')}
            </a>
            <a
              href="/crisis"
              className="text-sm font-medium text-[hsl(0,84%,40%)] hover:underline"
            >
              See crisis resources →
            </a>
          </div>
          <p className="mt-6 text-xs text-[hsl(0,30%,55%)]">
            If you are in immediate danger, call your local emergency number (e.g., 911 in the
            US) or go to your nearest emergency room.
          </p>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Footer
// ---------------------------------------------------------------------------

function Footer({ locale }: { locale: string }) {
  const productLinks = [
    { label: 'Features', href: '#features' },
    { label: 'Pricing', href: '#pricing' },
    { label: 'Safety', href: '#safety' },
    { label: 'Blog', href: '/blog' },
  ];

  const companyLinks = [
    { label: 'About', href: '/about' },
    { label: 'Privacy', href: `/${locale}/privacy` },
    { label: 'Terms', href: `/${locale}/terms` },
    { label: 'Contact', href: 'mailto:hello@disciplineos.com' },
  ];

  const locales = [
    { code: 'en', label: 'EN' },
    { code: 'fr', label: 'FR' },
    { code: 'ar', label: 'AR' },
    { code: 'fa', label: 'FA' },
  ];

  return (
    <footer className="border-t border-[hsl(220,14%,90%)] bg-white py-12">
      <div className="mx-auto max-w-6xl px-6">
        <div className="grid gap-8 sm:grid-cols-2 md:grid-cols-4">
          {/* Brand */}
          <div className="sm:col-span-2 md:col-span-2">
            <p className="text-base font-semibold text-[hsl(222,47%,11%)]">Discipline OS</p>
            <p className="mt-1 text-xs text-[hsl(215,16%,57%)]">Close the loop on urges</p>
            <p className="mt-4 max-w-xs text-sm leading-relaxed text-[hsl(215,16%,57%)]">
              A clinical-grade behavioral intervention platform for evidence-based urge management.
            </p>
            {/* Crisis link — always visible per non-negotiable rule */}
            <a
              href="/crisis"
              className="mt-4 inline-flex items-center gap-1.5 text-sm font-medium text-[hsl(0,84%,50%)] hover:underline"
            >
              <span aria-hidden="true">🆘</span> Crisis resources
            </a>
          </div>

          {/* Product links */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-[hsl(215,16%,47%)] mb-4">
              Product
            </p>
            <ul className="space-y-2" role="list">
              {productLinks.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Company links */}
          <div>
            <p className="text-xs font-semibold uppercase tracking-widest text-[hsl(215,16%,47%)] mb-4">
              Company
            </p>
            <ul className="space-y-2" role="list">
              {companyLinks.map((link) => (
                <li key={link.label}>
                  <a
                    href={link.href}
                    className="text-sm text-[hsl(215,16%,47%)] hover:text-[hsl(222,47%,11%)] transition-colors"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="mt-10 flex flex-col items-start justify-between gap-4 border-t border-[hsl(220,14%,93%)] pt-6 sm:flex-row sm:items-center">
          <p className="text-xs text-[hsl(215,16%,57%)]">
            © 2026 Discipline OS. All rights reserved.
          </p>

          {/* Language switcher */}
          <nav aria-label="Language switcher" className="flex items-center gap-1">
            {locales.map((loc, idx) => (
              <span key={loc.code} className="flex items-center">
                {idx > 0 && (
                  <span aria-hidden="true" className="mx-1 text-[hsl(215,16%,75%)] text-xs">
                    |
                  </span>
                )}
                <a
                  href={`/${loc.code}`}
                  aria-label={`Switch to ${loc.label}`}
                  aria-current={loc.code === locale ? 'true' : undefined}
                  className={`text-xs transition-colors ${
                    loc.code === locale
                      ? 'font-semibold text-[hsl(217,91%,52%)]'
                      : 'text-[hsl(215,16%,57%)] hover:text-[hsl(222,47%,11%)]'
                  }`}
                >
                  {loc.label}
                </a>
              </span>
            ))}
          </nav>
        </div>
      </div>
    </footer>
  );
}

// ---------------------------------------------------------------------------
// Page composition
// ---------------------------------------------------------------------------

function HomeInner({ locale }: { locale: string }) {
  const t = useTranslations();

  return (
    <>
      <TopNav />
      <main>
        <HeroSection t={t} />
        <HowItWorksSection />
        <FeaturesSection />
        <PricingSection t={t} />
        <SafetySection t={t} />
      </main>
      <Footer locale={locale} />
    </>
  );
}
