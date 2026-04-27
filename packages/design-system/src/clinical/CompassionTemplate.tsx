'use client';
/**
 * CompassionTemplate — compassion-first relapse companion renderer.
 *
 * RULE #4 (CLAUDE.md): Text is sourced from shared-rules/relapse_templates.json
 * and rendered VERBATIM. No string interpolation, no user-supplied substitution.
 * Any template change requires clinical QA sign-off.
 *
 * Typography: Fraunces variable font with SOFT axis at 60 (warmer register) per
 * the design spec §3.1. Applied via inline fontVariationSettings.
 */

import * as React from 'react';

export interface CompassionTemplateProps {
  /** The template text from relapse_templates.json. Rendered verbatim — no interpolation. */
  text: string;
  /** Template id for data-testid (e.g. 'compassion-001') */
  templateId?: string;
  /** Additional className on root */
  className?: string;
}

export function CompassionTemplate({
  text,
  templateId,
  className,
}: CompassionTemplateProps): React.ReactElement {
  return (
    <div
      className={['text-center px-6 py-8', className].filter(Boolean).join(' ')}
      data-testid="compassion-template"
      data-template-id={templateId}
    >
      <p
        className="text-xl leading-relaxed text-ink-primary"
        style={{ fontFamily: 'Fraunces, serif', fontVariationSettings: "'SOFT' 60, 'WONK' 0" }}
      >
        {text}
      </p>
    </div>
  );
}
