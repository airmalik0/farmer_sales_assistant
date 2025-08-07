#!/bin/bash

# Скрипт для получения SSL сертификатов для autodealer.quasar79.com

set -e

domains=(autodealer.quasar79.com)
rsa_key_size=4096
data_path="./certbot"

# Читаем email из .env файла
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    email="$LETSENCRYPT_EMAIL"
else
    email="maik.yuldashev2004@gmail.com"
fi

if [ -d "$data_path" ]; then
  read -p "Существующие данные найдены для $domains. Продолжить и пересоздать? (y/N) " decision
  if [ "$decision" != "Y" ] && [ "$decision" != "y" ]; then
    exit
  fi
fi

if [ ! -e "$data_path/conf/options-ssl-nginx.conf" ] || [ ! -e "$data_path/conf/ssl-dhparams.pem" ]; then
  echo "### Скачивание рекомендованных параметров TLS ..."
  mkdir -p "$data_path/conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot-nginx/certbot_nginx/_internal/tls_configs/options-ssl-nginx.conf > "$data_path/conf/options-ssl-nginx.conf"
  curl -s https://raw.githubusercontent.com/certbot/certbot/master/certbot/certbot/ssl-dhparams.pem > "$data_path/conf/ssl-dhparams.pem"
  echo
fi

echo "### Создание dummy сертификата для $domains ..."
path="/etc/letsencrypt/live/$domains"
mkdir -p "$data_path/conf/live/$domains"
docker-compose run --rm --entrypoint "\
  mkdir -p '$path' && \
  openssl req -x509 -nodes -newkey rsa:$rsa_key_size -days 1\
    -keyout '$path/privkey.pem' \
    -out '$path/fullchain.pem' \
    -subj '/CN=localhost'" certbot
echo

echo "### Запуск nginx с временной конфигурацией ..."
docker-compose up --force-recreate -d nginx
echo

echo "### Удаление dummy сертификата для $domains ..."
docker-compose run --rm --entrypoint "\
  rm -Rf /etc/letsencrypt/live/$domains && \
  rm -Rf /etc/letsencrypt/archive/$domains && \
  rm -Rf /etc/letsencrypt/renewal/$domains.conf" certbot
echo

echo "### Запрос Let's Encrypt сертификата для $domains ..."
# Присоединение к существующей сети nginx
domain_args=""
for domain in "${domains[@]}"; do
  domain_args="$domain_args -d $domain"
done

# Выберите подходящий email аргумент
case "$email" in
  "") email_arg="--register-unsafely-without-email" ;;
  *) email_arg="--email $email" ;;
esac

# Включите staging mode если тестируете
# staging_arg="--staging"

docker-compose run --rm --entrypoint "\
  certbot certonly --webroot -w /var/www/certbot \
    $email_arg \
    $domain_args \
    --rsa-key-size $rsa_key_size \
    --agree-tos \
    --force-renewal" certbot
echo

echo "### Обновление nginx конфигурации на SSL ..."
docker-compose exec nginx cp /etc/nginx/nginx-ssl.conf /etc/nginx/nginx.conf
docker-compose exec nginx nginx -s reload

echo "### SSL сертификаты успешно получены!" 