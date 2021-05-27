import gettext
import os.path
from contextvars import ContextVar
from glob import glob

LOCALE_DIR = 'boribay/locales'
DEFAULT_LOCALE = 'en_US'

current_locale: ContextVar[str] = ContextVar('i18n')
current_locale.set(DEFAULT_LOCALE)

locales = frozenset(
    map(
        os.path.basename,
        filter(os.path.isdir, glob(os.path.join(__file__, LOCALE_DIR, '*'))),
    )
)

_translations = {
    locale: gettext.translation(
        'boribay', os.path.join(__file__, LOCALE_DIR), [locale]
    ) for locale in locales
}

# Since the bot is already written in english.
_translations['en_US'] = gettext.NullTranslations()
locales = locales | {'en_US'}


def load_translation(*args, **kwargs) -> str:
    if not _translations:
        return gettext.gettext(*args, **kwargs)

    locale = current_locale.get()
    return _translations.get(
        locale, _translations[DEFAULT_LOCALE]
    ).gettext(*args, **kwargs)


_ = load_translation
