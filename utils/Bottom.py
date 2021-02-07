# Python 3.9+ required.
# https://github.com/bottom-software-foundation/bottom-py

CHARACTER_VALUES = {
    200: "🫂",
    50: "💖",
    10: "✨",
    5: "🥺",
    1: ",",
    0: "❤️"
}

SECTION_SEPERATOR = '👉👈'


def to_bottom(text: str) -> str:
    out = bytearray()

    for char in text.encode():
        while char != 0:
            for value, emoji in CHARACTER_VALUES.items():
                if char >= value:
                    char -= value
                    out += emoji.encode()
                    break

        out += SECTION_SEPERATOR.encode()

    return out.decode('utf-8')


def from_bottom(text: str) -> str:
    out = bytearray()
    text = text.strip().removesuffix(SECTION_SEPERATOR)

    if not all(c in CHARACTER_VALUES.values() for c in text.replace(SECTION_SEPERATOR, '')):
        raise TypeError(f'Invalid bottom text: {text}')

    for char in text.split(SECTION_SEPERATOR):
        rev_mapping = {v: k for k, v in CHARACTER_VALUES.items()}

        sub = 0
        for emoji in char:
            sub += rev_mapping[emoji]

        out += sub.to_bytes(1, 'big')

    return out.decode()
