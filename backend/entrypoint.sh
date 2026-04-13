#!/bin/sh
set -e

echo "--- FASTBOX MVP DEPLOY (SQLite) ---"

# Создаем базу данных
mkdir -p /var/www/database
touch /var/www/database/database.sqlite
chown -R www-data:www-data /var/www/database
chmod -R 775 /var/www/database

export DB_CONNECTION=sqlite
export DB_DATABASE=/var/www/database/database.sqlite

# Очистка и миграции
php artisan config:clear
echo "Running migrations & seeding..."
php artisan migrate --force
php artisan db:seed --force

# Запуск PHP-FPM
echo "Starting PHP-FPM..."
php-fpm -D

# Даем время на создание сокета и ставим права
sleep 2
chmod 666 /var/run/php-fpm.sock

echo "Starting Nginx..."
nginx -g "daemon off;"
