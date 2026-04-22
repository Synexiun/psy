"""Server-side i18n — locale negotiation, formatters, bidi, catalog.

Every user-facing surface (email, push, PDF report, translatable API messages) MUST
pick a locale via :func:`negotiate_locale` rather than reading ``Accept-Language``
directly.  This keeps the supported-locale set in one place and guarantees graceful
fallback.
"""

from .catalog import get_message
from .formatters import format_date, format_number, format_number_clinical
from .negotiation import SUPPORTED_LOCALES, Locale, is_rtl, negotiate_locale
from .package_catalog import (
    CatalogStatus,
    is_clinical_key,
    is_locale_releasable,
    releasable_locales,
    resolve_clinical_message,
    verify_catalog_parity,
)

__all__ = [
    "SUPPORTED_LOCALES",
    "CatalogStatus",
    "Locale",
    "format_date",
    "format_number",
    "format_number_clinical",
    "get_message",
    "is_clinical_key",
    "is_locale_releasable",
    "is_rtl",
    "negotiate_locale",
    "releasable_locales",
    "resolve_clinical_message",
    "verify_catalog_parity",
]
