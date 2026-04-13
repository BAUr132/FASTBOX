#!/bin/sh

# Выполняем миграции (создание таблиц)
echo "Running migrations..."
php artisan migrate --force

# Загружаем демо-данные (магазины, меню), если база пуста
echo "Seeding database..."
php artisan db:seed --force

# Запускаем PHP-FPM в фоновом режиме
echo "Starting PHP-FPM..."
php-fpm -D

# Запускаем Nginx в основном режиме (держит контейнер активным)
echo "Starting Nginx..."
nginx -g "daemon off;"
