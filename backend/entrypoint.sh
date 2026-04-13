#!/bin/sh

echo "--- DATABASE CHECK ---"
echo "Connecting to: $DB_HOST (Database: $DB_DATABASE, User: $DB_USERNAME)"
echo "Connection type: $DB_CONNECTION"

# Выполняем миграции
echo "Running migrations..."
php artisan migrate --force

# Загружаем демо-данные
echo "Seeding database..."
php artisan db:seed --force

echo "Starting PHP-FPM..."
php-fpm -D

echo "Starting Nginx..."
nginx -g "daemon off;"
