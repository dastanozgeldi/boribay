import random
lowercase_letters = 'abcdefghijklmnopqrstuvwxyz'
uppercase_letters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
digits = '0123456789'
additional_chars = '!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'


def generate_password(length: int, uppercase: bool = False, digit: bool = False, chars: bool = False):
    password = ''
    for _ in range(length):
        if uppercase is True and digit is False and chars is False:
            password += random.choice((lowercase_letters + uppercase_letters))

        if uppercase is True and digit is True and chars is False:
            password += random.choice((lowercase_letters + uppercase_letters + digits))

        if uppercase is False and digit is True and chars is True:
            password += random.choice((lowercase_letters + digits + additional_chars))

        if uppercase is False and digit is False and chars is True:
            password += random.choice((lowercase_letters + additional_chars))

        if uppercase is True and digit is True and chars is True:
            password += random.choice((lowercase_letters + uppercase_letters + digits + additional_chars))

        else:
            password += random.choice(lowercase_letters)

    return password


print(generate_password(30, True, True, True))
