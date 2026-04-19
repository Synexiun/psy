import { getRequestConfig } from 'next-intl/server';
import { hasLocale } from 'next-intl';
import { loadCatalog } from '@disciplineos/i18n-catalog';
import { routing } from './routing';

export default getRequestConfig(async ({ requestLocale }) => {
  const requested = await requestLocale;
  const locale = hasLocale(routing.locales, requested) ? requested : routing.defaultLocale;
  const messages = await loadCatalog(locale);
  return { locale, messages };
});
