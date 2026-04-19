/**
 * Minimal locale logic for the crisis surface.
 *
 * We do NOT pull in next-intl here. Every runtime dependency is a potential failure mode,
 * and this app must keep working when everything else is broken.
 */

export type CrisisLocale = 'en' | 'fr' | 'ar' | 'fa';

export const SUPPORTED_LOCALES: ReadonlyArray<CrisisLocale> = ['en', 'fr', 'ar', 'fa'];

export const isRtl = (locale: CrisisLocale): boolean => locale === 'ar' || locale === 'fa';

/**
 * Static copy. Kept inline so the page has ZERO dependency on a translation pipeline at runtime.
 * Copy strings here must match the i18n-catalog crisis.* keys; drift is caught in CI.
 */
interface CrisisCopy {
  headline: string;
  body: string;
  callHotline: string;
  callEmergency: string;
  hours: string;
  free: string;
  smsLabel: string;
  webLabel: string;
  orTry: string;
  backToApp: string;
}

export const COPY: Record<CrisisLocale, CrisisCopy> = {
  en: {
    headline: 'You are not alone.',
    body: 'If you are in crisis, please reach out. These numbers are free and confidential.',
    callHotline: 'Call hotline',
    callEmergency: 'Call emergency',
    hours: 'Hours',
    free: 'Free',
    smsLabel: 'Text',
    webLabel: 'Website',
    orTry: 'Or open a coping tool',
    backToApp: 'Back to app',
  },
  fr: {
    headline: "Vous n'êtes pas seul·e.",
    body: "Si vous êtes en crise, demandez de l'aide. Ces numéros sont gratuits et confidentiels.",
    callHotline: "Appeler la ligne d'écoute",
    callEmergency: 'Appeler les urgences',
    hours: 'Horaires',
    free: 'Gratuit',
    smsLabel: 'SMS',
    webLabel: 'Site web',
    orTry: "Ou ouvrez un outil d'adaptation",
    backToApp: "Retour à l'app",
  },
  ar: {
    headline: 'أنت لست وحدك.',
    body: 'إذا كنت تعاني من أزمة، يُرجى طلب المساعدة. هذه الأرقام مجانية وسرّية.',
    callHotline: 'اتصل بخط المساعدة',
    callEmergency: 'اتصل بالطوارئ',
    hours: 'ساعات العمل',
    free: 'مجاني',
    smsLabel: 'رسالة نصية',
    webLabel: 'الموقع الإلكتروني',
    orTry: 'أو افتح أداة مواجهة',
    backToApp: 'العودة إلى التطبيق',
  },
  fa: {
    headline: 'شما تنها نیستید.',
    body: 'اگر در بحران هستید، لطفاً کمک بخواهید. این شماره‌ها رایگان و محرمانه‌اند.',
    callHotline: 'تماس با خط کمک',
    callEmergency: 'تماس با اورژانس',
    hours: 'ساعات کاری',
    free: 'رایگان',
    smsLabel: 'پیامک',
    webLabel: 'وب‌سایت',
    orTry: 'یا یک ابزار مقابله را باز کنید',
    backToApp: 'بازگشت به برنامه',
  },
};

export const isCrisisLocale = (s: string): s is CrisisLocale =>
  (SUPPORTED_LOCALES as ReadonlyArray<string>).includes(s);
