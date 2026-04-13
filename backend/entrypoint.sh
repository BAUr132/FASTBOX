#!/bin/sh

# ПРИНУДИТЕЛЬНО УДАЛЯЕМ .env, чтобы Laravel брал переменные из Railway
if [ -f .env ]; then
    echo "Deleting local .env file to use Railway Variables..."
    rm .env
fi

echo "--- DATABASE CONNECTION CHECK ---"
echo "Host: $DB_HOST"
echo "Database: $DB_DATABASE"
echo "Connection: $DB_CONNECTION"

# Очистка конфига, чтобы новые переменные точно подхватились
php artisan config:clear

echo "Running migrations..."
php artisan migrate --force

echo "Seeding database..."
php artisan db:seed --force

echo "Starting PHP-FPM..."
php-fpm -D

echo "Starting Nginx..."
nginx -g "daemon off;"
