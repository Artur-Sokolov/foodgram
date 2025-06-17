from django.conf import settings
from django.core.mail import send_mail


def send_confirmation_code(user):
    """
    Отправка простого PIN‑кода на e‑mail.
    Код хранится в user.confirmation_code.
    """
    # тема письма
    subject = 'Ваш код подтверждения для YaMDb'
    message = (
        f'Здравствуйте, {user.username}! Ваш код подтверждения:'
    )

    # отправляем письмо
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
