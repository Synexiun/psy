"""Server-side message catalog for emails, push notifications, PDF labels.

Web and mobile surfaces have their own catalogs (see ``packages/i18n-catalog``).
This catalog is deliberately smaller — only server-generated copy lives here.
"""

from __future__ import annotations

from .negotiation import DEFAULT_LOCALE, Locale

# In production, catalogs are loaded at startup from files under
# services/api/data/locale/<locale>.json and frozen into immutable dicts.
# This in-module stub is the compile-time source of truth for key shapes.
_CATALOG: dict[Locale, dict[str, str]] = {
    "en": {
        "email.reset.subject": "Reset your Discipline OS password",
        "push.check_in.title": "A gentle check-in",
        "pdf.report.title": "Discipline OS — Clinical summary",
        "safety.t4.headline": "You are not alone.",
    },
    "fr": {
        "email.reset.subject": "Réinitialiser votre mot de passe Discipline OS",
        "push.check_in.title": "Un petit bilan",
        "pdf.report.title": "Discipline OS — Résumé clinique",
        "safety.t4.headline": "Vous n'êtes pas seul·e.",
    },
    "ar": {
        "email.reset.subject": "إعادة تعيين كلمة مرور Discipline OS",
        "push.check_in.title": "تسجيل وضعيّة خفيف",
        "pdf.report.title": "Discipline OS — ملخّص سريري",
        "safety.t4.headline": "أنت لست وحدك.",
    },
    "fa": {
        "email.reset.subject": "بازنشانی گذرواژه‌ی Discipline OS",
        "push.check_in.title": "یک وضعیت‌سنجی کوتاه",
        "pdf.report.title": "Discipline OS — خلاصه‌ی بالینی",
        "safety.t4.headline": "شما تنها نیستید.",
    },
}


def get_message(key: str, locale: Locale) -> str:
    """Return the translated message, falling back to English, then to the key itself.

    We never raise for a missing key — a missing translation must not break an email
    send or a push notification.  The key-as-fallback surfaces the gap loudly in QA.
    """
    for candidate in (locale, DEFAULT_LOCALE):
        lookup = _CATALOG.get(candidate, {})
        if key in lookup:
            return lookup[key]
    return key


__all__ = ["get_message"]
