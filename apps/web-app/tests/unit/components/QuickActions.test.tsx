/**
 * Unit tests for QuickActions.
 *
 * QuickActions renders 4 action tiles — Check in, Coping tool, Journal, Crisis help —
 * each linking to the locale-prefixed path. The Crisis help link must always be
 * present and must target the /crisis path (CLAUDE.md Rule 1: crisis path must be
 * reachable). All links must have accessible labels.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QuickActions } from '@/components/QuickActions';

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('QuickActions', () => {
  // --- Render all 4 actions -------------------------------------------------

  it('renders 4 quick action links', () => {
    render(<QuickActions locale="en" />);
    const links = screen.getAllByRole('link');
    expect(links.length).toBe(4);
  });

  it('renders "Check in" action', () => {
    render(<QuickActions locale="en" />);
    expect(screen.getByText('Check in')).toBeInTheDocument();
  });

  it('renders "Coping tool" action', () => {
    render(<QuickActions locale="en" />);
    expect(screen.getByText('Coping tool')).toBeInTheDocument();
  });

  it('renders "Journal" action', () => {
    render(<QuickActions locale="en" />);
    expect(screen.getByText('Journal')).toBeInTheDocument();
  });

  it('renders "Crisis help" action', () => {
    render(<QuickActions locale="en" />);
    expect(screen.getByText('Crisis help')).toBeInTheDocument();
  });

  // --- Locale-prefixed hrefs ------------------------------------------------

  it('check-in link targets /{locale}/check-in', () => {
    render(<QuickActions locale="en" />);
    const link = screen.getByRole('link', { name: /check in/i });
    expect(link).toHaveAttribute('href', '/en/check-in');
  });

  it('coping tool link targets /{locale}/tools', () => {
    render(<QuickActions locale="en" />);
    const link = screen.getByRole('link', { name: /coping tool/i });
    expect(link).toHaveAttribute('href', '/en/tools');
  });

  it('journal link targets /{locale}/journal', () => {
    render(<QuickActions locale="en" />);
    const link = screen.getByRole('link', { name: /journal/i });
    expect(link).toHaveAttribute('href', '/en/journal');
  });

  it('crisis help link targets /{locale}/crisis (CLAUDE.md Rule 1)', () => {
    render(<QuickActions locale="en" />);
    const link = screen.getByRole('link', { name: /crisis help/i });
    expect(link).toHaveAttribute('href', '/en/crisis');
  });

  // --- Locale propagation ---------------------------------------------------

  it('uses the supplied locale prefix — "fr"', () => {
    render(<QuickActions locale="fr" />);
    const links = screen.getAllByRole('link');
    const hrefs = links.map((l) => l.getAttribute('href') ?? '');
    expect(hrefs.every((href) => href.startsWith('/fr/'))).toBe(true);
  });

  it('uses the supplied locale prefix — "ar"', () => {
    render(<QuickActions locale="ar" />);
    const crisisLink = screen.getByRole('link', { name: /crisis/i });
    expect(crisisLink).toHaveAttribute('href', '/ar/crisis');
  });

  // --- Accessibility --------------------------------------------------------

  it('renders a section with aria-labelledby pointing to the quick-actions heading', () => {
    const { container } = render(<QuickActions locale="en" />);
    const section = container.querySelector('section[aria-labelledby="quick-actions"]');
    expect(section).not.toBeNull();
  });

  it('action descriptions are visible', () => {
    render(<QuickActions locale="en" />);
    expect(screen.getByText('Log how you feel right now')).toBeInTheDocument();
    expect(screen.getByText('Get support now')).toBeInTheDocument();
  });
});
