<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Product;
use App\Models\Shop;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\Hash;
use Illuminate\Support\Facades\DB;

class FastBoxSeeder extends Seeder
{
    public function run(): void
    {
        // Полная очистка перед сидингом
        DB::statement('SET FOREIGN_KEY_CHECKS=0;');
        Product::truncate();
        Shop::truncate();
        Category::truncate();
        DB::statement('SET FOREIGN_KEY_CHECKS=1;');

        // 1. Категории с иконками из app.js
        $categoriesData = [
            'burgers' => ['name' => '🍔 Бургеры', 'icon' => 'fa-hamburger'],
            'sushi' => ['name' => '🍣 Суши', 'icon' => 'fa-fish'],
            'pharmacy' => ['name' => '💊 Аптеки', 'icon' => 'fa-pills'],
            'groceries' => ['name' => '🛒 Продукты', 'icon' => 'fa-shopping-cart'],
        ];

        $categoryModels = [];
        foreach ($categoriesData as $key => $data) {
            $categoryModels[$key] = Category::create($data);
        }

        // 2. Магазины и товары (полный перенос из WebstormProjects/FastBox/app.js)
        $shopsData = [
            [
                'category_key' => 'burgers',
                'name' => 'Burger House',
                'address' => 'ул. Тауелсиздик, 12',
                'lat' => 53.2144,
                'lng' => 63.6246,
                'description' => 'Фастфуд • Бургеры',
                'rating' => '4.8',
                'items' => [
                    ['name' => 'Чизбургер Классик', 'price' => 1500, 'desc' => 'Котлета из говядины, сыр чеддер, соус', 'img' => '🍔'],
                    ['name' => 'Двойной Смэш Бургер', 'price' => 2200, 'desc' => 'Две котлеты, бекон, халапеньо', 'img' => '🍔'],
                    ['name' => 'Картофель Фри', 'price' => 800, 'desc' => 'Хрустящая картошка, стандартная порция', 'img' => '🍟'],
                ]
            ],
            [
                'category_key' => 'sushi',
                'name' => 'Суши Мастер',
                'address' => 'пр. Абая, 45',
                'lat' => 53.2198,
                'lng' => 63.6354,
                'description' => 'Японская кухня • Роллы',
                'rating' => '4.6',
                'items' => [
                    ['name' => 'Ролл Филадельфия', 'price' => 2500, 'desc' => 'Лосось, сливочный сыр, огурец', 'img' => '🍣'],
                    ['name' => 'Ролл Калифорния', 'price' => 2200, 'desc' => 'Краб, авокадо, тобико', 'img' => '🍱'],
                ]
            ],
            [
                'category_key' => 'pharmacy',
                'name' => 'Аптека "Здоровье"',
                'address' => 'ул. Каирбекова, 67',
                'lat' => 53.2450,
                'lng' => 63.6420,
                'description' => 'Медикаменты • Витамины',
                'rating' => '4.9',
                'items' => [
                    ['name' => 'Парацетамол 500мг', 'price' => 350, 'desc' => 'Жаропонижающее, 10 таблеток', 'img' => '💊'],
                    ['name' => 'ТераФлю', 'price' => 2800, 'desc' => 'Порошок от простуды, 4 пакетика', 'img' => '☕'],
                ]
            ],
            [
                'category_key' => 'groceries',
                'name' => 'ТД ЦУМ (Продукты)',
                'address' => 'ул. Аль-Фараби, 65',
                'lat' => 53.2101,
                'lng' => 63.6285,
                'description' => 'Продукты • Напитки',
                'rating' => '4.7',
                'items' => [
                    ['name' => 'Хлеб белый нарезной', 'price' => 200, 'desc' => 'Свежая выпечка', 'img' => '🍞'],
                    ['name' => 'Молоко 3.2%', 'price' => 650, 'desc' => 'Домашнее, 1 литр', 'img' => '🥛'],
                ]
            ],
        ];

        foreach ($shopsData as $s) {
            $shop = Shop::create([
                'category_id' => $categoryModels[$s['category_key']]->id,
                'name' => $s['name'],
                'address' => $s['address'],
                'lat' => $s['lat'],
                'lng' => $s['lng'],
                'description' => $s['description'],
            ]);

            foreach ($s['items'] as $item) {
                Product::create([
                    'shop_id' => $shop->id,
                    'name' => $item['name'],
                    'price' => $item['price'],
                    'description' => $item['desc'],
                    'image' => $item['img'],
                ]);
            }
        }
    }
}
