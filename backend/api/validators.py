import re

from django.conf import settings
from django.core.exceptions import ValidationError

#from datetime import date



def validate_username(username):
    """Проверка валидности имени пользователя."""
    invalid_chars = set(re.findall(r'[^\w.@+-]', username))
    if invalid_chars:
        chars = ''.join(sorted(invalid_chars))
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы: {chars}'
        )
    if username == settings.USER_ME_URL_SEGMENT:
        raise ValidationError(
            f'Имя пользователя "{username}" запрещено.'
        )
    return username
