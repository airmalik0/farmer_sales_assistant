#!/bin/bash

# Скрипт для обновления SSL сертификатов

set -e

echo "### Обновление SSL сертификатов..."
docker-compose run --rm certbot renew

echo "### Перезагрузка nginx..."
docker-compose exec nginx nginx -s reload

echo "### SSL сертификаты успешно обновлены!" 