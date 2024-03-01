import re

from rest_framework import serializers


def validate_username(value):
    if not re.match(r'^[\w.@+-]+\Z', value):
        raise serializers.ValidationError(
            'Имя пользователя содержит недопустимые символы!')
