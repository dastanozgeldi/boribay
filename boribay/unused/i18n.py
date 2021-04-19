import contextvars
import gettext
import os.path
from glob import glob
from os import getcwd
from typing import Any

BASE = getcwd()
DEFAULT = 'en_US'
LOCALES_DIR = 'locales'

locales = frozenset(
    map(
        os.path.basename,
        filter(os.path.isdir, glob(os.path.join(BASE, LOCALES_DIR, '*'))),
    )
)

translations = {
    locale: gettext.translation(
        'boribay', languages=(locale,), localedir=os.path.join(BASE, LOCALES_DIR)
    ) for locale in locales
}

translations['en_US'] = gettext.NullTranslations()
locales = locales | {'en_US'}


def current_gettext(*args: Any, **kwargs: Any) -> str:
    if not translations:
        return gettext.gettext(*args, **kwargs)

    locale = current_locale.get()
    return translations.get(locale, translations[DEFAULT]).gettext(*args, **kwargs)


current_locale: contextvars.ContextVar[str] = contextvars.ContextVar('i18n')
_ = current_gettext

current_locale.set(DEFAULT)
