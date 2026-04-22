import { getRequestConfig } from 'next-intl/server';

import { loadCatalog } from '@disciplineos/i18n-catalog';
import type { Locale } from '@disciplineos/i18n-catalog';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale =
    requested && (routing.locales as readonly string[]).includes(requested)
      ? requested
      : routing.defaultLocale;
  const messages = await loadCatalog(locale as Locale);
  return { locale, messages };
});
