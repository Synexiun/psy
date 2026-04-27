/**
 * Library stubs — psychoeducational content categories and articles.
 *
 * Pure data module — no 'use client' directive, no React/browser APIs.
 * Follows the same pattern as check-in.ts.
 *
 * In Phase 5 this will be replaced by a backend API call.
 */

export interface LibraryArticle {
  slug: string;
  categorySlug: string;
  titleKey: string;       // i18n key suffix, e.g. 'urgeSurfing'
  excerptKey: string;
  bodyKey: string;
  readingTimeMin: number; // Latin digit, not a clinical score
}

export interface LibraryCategory {
  slug: string;
  titleKey: string;       // i18n key suffix
  descriptionKey: string;
  articleCount: number;
  articles: LibraryArticle[];
}

export type LibraryStubs = {
  categories: LibraryCategory[];
};

export const libraryStubs: LibraryStubs = {
  categories: [
    {
      slug: 'understanding-addiction',
      titleKey: 'understandingAddiction',
      descriptionKey: 'understandingAddictionDesc',
      articleCount: 3,
      articles: [
        {
          slug: 'how-it-works',
          categorySlug: 'understanding-addiction',
          titleKey: 'howItWorks',
          excerptKey: 'howItWorksExcerpt',
          bodyKey: 'howItWorksBody',
          readingTimeMin: 5,
        },
        {
          slug: 'assessments-explained',
          categorySlug: 'understanding-addiction',
          titleKey: 'assessmentsExplained',
          excerptKey: 'assessmentsExplainedExcerpt',
          bodyKey: 'assessmentsExplainedBody',
          readingTimeMin: 4,
        },
        {
          slug: 'after-a-lapse',
          categorySlug: 'understanding-addiction',
          titleKey: 'afterALapse',
          excerptKey: 'afterALapseExcerpt',
          bodyKey: 'afterALapseBody',
          readingTimeMin: 6,
        },
      ],
    },
    {
      slug: 'cbt-skills',
      titleKey: 'cbtSkills',
      descriptionKey: 'cbtSkillsDesc',
      articleCount: 3,
      articles: [
        {
          slug: 'urge-surfing',
          categorySlug: 'cbt-skills',
          titleKey: 'urgeSurfing',
          excerptKey: 'urgeSurfingExcerpt',
          bodyKey: 'urgeSurfingBody',
          readingTimeMin: 4,
        },
        {
          slug: 'cognitive-defusion',
          categorySlug: 'cbt-skills',
          titleKey: 'cognitiveDefusion',
          excerptKey: 'cognitiveDefusionExcerpt',
          bodyKey: 'cognitiveDefusionBody',
          readingTimeMin: 5,
        },
        {
          slug: 'implementation-intentions',
          categorySlug: 'cbt-skills',
          titleKey: 'implementationIntentions',
          excerptKey: 'implementationIntentionsExcerpt',
          bodyKey: 'implementationIntentionsBody',
          readingTimeMin: 5,
        },
      ],
    },
    {
      slug: 'mindfulness-basics',
      titleKey: 'mindfulnessBasics',
      descriptionKey: 'mindfulnessBasicsDesc',
      articleCount: 3,
      articles: [
        {
          slug: 'box-breathing',
          categorySlug: 'mindfulness-basics',
          titleKey: 'boxBreathing',
          excerptKey: 'boxBreathingExcerpt',
          bodyKey: 'boxBreathingBody',
          readingTimeMin: 3,
        },
        {
          slug: 'body-scan',
          categorySlug: 'mindfulness-basics',
          titleKey: 'bodyScan',
          excerptKey: 'bodyScanExcerpt',
          bodyKey: 'bodyScanBody',
          readingTimeMin: 5,
        },
        {
          slug: 'self-compassion',
          categorySlug: 'mindfulness-basics',
          titleKey: 'selfCompassion',
          excerptKey: 'selfCompassionExcerpt',
          bodyKey: 'selfCompassionBody',
          readingTimeMin: 6,
        },
      ],
    },
    {
      slug: 'sleep-recovery',
      titleKey: 'sleepRecovery',
      descriptionKey: 'sleepRecoveryDesc',
      articleCount: 2,
      articles: [
        {
          slug: 'getting-started',
          categorySlug: 'sleep-recovery',
          titleKey: 'gettingStarted',
          excerptKey: 'gettingStartedExcerpt',
          bodyKey: 'gettingStartedBody',
          readingTimeMin: 4,
        },
        {
          slug: 'tipp-technique',
          categorySlug: 'sleep-recovery',
          titleKey: 'tippTechnique',
          excerptKey: 'tippTechniqueExcerpt',
          bodyKey: 'tippTechniqueBody',
          readingTimeMin: 5,
        },
      ],
    },
    {
      slug: 'crisis-safety',
      titleKey: 'crisisSafety',
      descriptionKey: 'crisisSafetyDesc',
      articleCount: 2,
      articles: [
        {
          slug: 'contact-a-human',
          categorySlug: 'crisis-safety',
          titleKey: 'contactAHuman',
          excerptKey: 'contactAHumanExcerpt',
          bodyKey: 'contactAHumanBody',
          readingTimeMin: 3,
        },
        {
          slug: 'safety-resources',
          categorySlug: 'crisis-safety',
          titleKey: 'safetyResources',
          excerptKey: 'safetyResourcesExcerpt',
          bodyKey: 'safetyResourcesBody',
          readingTimeMin: 4,
        },
      ],
    },
  ],
};
