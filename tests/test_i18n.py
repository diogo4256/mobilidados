"""Message catalogues (``locales/<lang>.toml``): every language has every key, with the same placeholders."""

import string
import typing

from streetfit.config import Lang
from streetfit.i18n import messages


def test_every_message_exists_in_every_language_with_the_same_placeholders():
    def fields(s: str) -> set[str]:
        return {f for _, f, _, _ in string.Formatter().parse(s) if f}

    en = messages("en")
    for lang in typing.get_args(Lang):
        other = messages(lang)
        assert other.keys() == en.keys(), f"{lang}: keys differ from en"
        assert all(fields(other[k]) == fields(en[k]) for k in en), f"{lang}: placeholders differ from en"
