"""Server-side i18n — locale negotiation, formatters, bidi, catalog.

Every user-facing surface (email, push, PDF report, translatable API messages) MUST
pick a locale via :func:`negotiate_locale` rather than reading ``Accept-Language``
directly.  This keeps the supported-locale set in one place and guarantees graceful
fallback.
"""

from .negotiation import SUPPORTED_LOCALES, Locale, negotiate_locale, is_rtl
from .formatters import format_date, format_number, format_number_clinical
from .catalog import get_message
from .package_catalog import (
    CatalogStatus,
    is_clinical_key,
    is_locale_releasable,
    releasable_locales,
    resolve_clinical_message,
    verify_catalog_parity,
)

__all__ = [
    "Locale",
    "SUPPORTED_LOCALES",
    "negotiate_locale",
    "is_rtl",
    "format_date",
    "format_number",
    "format_number_clinical",
    "get_message",
    "CatalogStatus",
    "is_clinical_key",
    "is_locale_releasable",
    "releasable_locales",
    "resolve_clinical_message",
    "verify_catalog_parity",
]
