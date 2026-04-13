# Use PHP 8.3 FPM
FROM php:8.3-fpm

# Set working directory
WORKDIR /var/www

# Install system dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    libpng-dev \
    libjpeg62-turbo-dev \
    libfreetype6-dev \
    locales \
    zip \
    unzip \
    git \
    curl \
    libonig-dev \
    libxml2-dev \
    libzip-dev

# Clear cache
RUN apt-get clean && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-install pdo_mysql mbstring exif pcntl bcmath gd zip

# Get latest Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Copy project files
COPY . /var/www

# Install PHP dependencies
RUN composer install --no-dev --optimize-autoloader

# Copy Nginx config
COPY ./nginx-railway.conf /etc/nginx/sites-available/default
RUN ln -sf /etc/nginx/sites-available/default /etc/nginx/sites-enabled/default

# Permissions
RUN chown -R www-data:www-data /var/www/storage /var/www/bootstrap/cache

# Expose port (Railway dynamic port)
EXPOSE 80

# Start script
CMD service nginx start && php-fpm
