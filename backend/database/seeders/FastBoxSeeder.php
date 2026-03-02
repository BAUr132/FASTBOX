<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Product;
use App\Models\Shop;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;

class FastBoxSeeder extends Seeder
{
    public function run(): void
    {
        // Создаем тестового пользователя (клиент и админ)
        User::create([
            'name' => 'Bauyrzhan',
            'email' => 'admin@fastbox.kz',
            'password' => Hash::make('password'),
            'role' => 'admin',
            'verification_status' => 'verified',
        ]);

        // Категории
        $cats = [
            'burgers' => ['name' => '🍔 Бургеры', 'icon' => 'fa-hamburger'],
            'sushi' => ['name' => '🍣 Суши', 'icon' => 'fa-fish'],
            'pharmacy' => ['name' => '💊 Аптеки', 'icon' => 'fa-pills'],
            'groceries' => ['name' => '🛒 Продукты', 'icon' => 'fa-shopping-cart'],
        ];

        $categoryModels = [];
        foreach ($cats as $key => $data) {
            $categoryModels[$key] = Category::create($data);
        }

        // Магазины и товары из твоего app.js
        $shopsData = [
            [
                'cat' => 'burgers',
                'name' => 'Burger House',
                'address' => 'ул. Тауелсиздик, 12',
                'lat' => 53.2144,
                'lng' => 63.6246,
                'desc' => 'Фастфуд • Бургеры',
                'items' => [
                    ['name' => 'Чизбургер Классик', 'price' => 1500, 'desc' => 'Котлета из говядины, сыр чеддер, соус'],
                    ['name' => 'Двойной Смэш Бургер', 'price' => 2200, 'desc' => 'Две котлеты, бекон, халапеньо'],
                    ['name' => 'Картофель Фри', 'price' => 800, 'desc' => 'Хрустящая картошка, стандартная порция'],
                ]
            ],
            [
                'cat' => 'sushi',
                'name' => 'Суши Мастер',
                'address' => 'пр. Абая, 45',
                'lat' => 53.2198,
                'lng' => 63.6354,
                'desc' => 'Японская кухня • Роллы',
                'items' => [
                    ['name' => 'Ролл Филадельфия', 'price' => 2500, 'desc' => 'Лосось, сливочный сыр, огурец'],
                    ['name' => 'Ролл Калифорния', 'price' => 2200, 'desc' => 'Краб, авокадо, тобико'],
                ]
            ],
            [
                'cat' => 'pharmacy',
                'name' => 'Аптека "Здоровье"',
                'address' => 'ул. Каирбекова, 67',
                'lat' => 53.2450,
                'lng' => 63.6420,
                'desc' => 'Медикаменты • Витамины',
                'items' => [
                    ['name' => 'Парацетамол 500мг', 'price' => 350, 'desc' => 'Жаропонижающее, 10 таблеток'],
                    ['name' => 'ТераФлю', 'price' => 2800, 'desc' => 'Порошок от простуды, 4 пакетика'],
                ]
            ],
        ];

        foreach ($shopsData as $s) {
            $shop = Shop::create([
                'category_id' => $categoryModels[$s['cat']]->id,
                'name' => $s['name'],
                'address' => $s['address'],
                'lat' => $s['lat'],
                'lng' => $s['lng'],
                'description' => $s['desc'],
            ]);

            foreach ($s['items'] as $item) {
                Product::create([
                    'shop_id' => $shop->id,
                    'name' => $item['name'],
                    'price' => $item['price'],
                    'description' => $item['desc'],
                ]);
            }
        }
    }
}
