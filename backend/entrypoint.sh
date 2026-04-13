#!/bin/sh

# Создаем файл базы данных SQLite, если его нет
mkdir -p /var/www/database
touch /var/www/database/database.sqlite
chmod -R 777 /var/www/database

echo "--- USING SQLITE FOR DEMO ---"

# Принудительно устанавливаем переменные для SQLite
export DB_CONNECTION=sqlite
export DB_DATABASE=/var/www/database/database.sqlite

# Очистка конфига
php artisan config:clear

# Миграции и сиды
echo "Running migrations..."
php artisan migrate --force
echo "Seeding database..."
php artisan db:seed --force

echo "Starting PHP-FPM..."
php-fpm -D

echo "Starting Nginx..."
nginx -g "daemon off;"
