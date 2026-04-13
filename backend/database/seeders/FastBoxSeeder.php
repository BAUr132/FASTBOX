<?php

namespace Database\Seeders;

use App\Models\Category;
use App\Models\Product;
use App\Models\Shop;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class FastBoxSeeder extends Seeder
{
    public function run(): void
    {
        DB::statement('SET FOREIGN_KEY_CHECKS=0;');
        Product::truncate();
        Shop::truncate();
        Category::truncate();
        DB::statement('SET FOREIGN_KEY_CHECKS=1;');

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

        $shopsData = [
            [
                'category_key' => 'burgers',
                'name' => 'Бургерная №1',
                'address' => 'Центральный район, 12',
                'lat' => 53.2144,
                'lng' => 63.6246,
                'description' => 'Фастфуд • Сочные бургеры',
                'items' => [
                    ['name' => 'Классический бургер', 'price' => 1500, 'desc' => 'Говяжья котлета, овощи, фирменный соус', 'img' => '🍔'],
                    ['name' => 'Двойной чизбургер', 'price' => 2200, 'desc' => 'Две котлеты, двойной сыр чеддер', 'img' => '🍔'],
                    ['name' => 'Картофель фри', 'price' => 800, 'desc' => 'Хрустящий картофель с солью', 'img' => '🍟'],
                ]
            ],
            [
                'category_key' => 'sushi',
                'name' => 'Суши-бар "Океан"',
                'address' => 'Микрорайон Восток, 45',
                'lat' => 53.2198,
                'lng' => 63.6354,
                'description' => 'Японская кухня • Свежие роллы',
                'items' => [
                    ['name' => 'Ролл Филадельфия', 'price' => 2500, 'desc' => 'Свежий лосось и сливочный сыр', 'img' => '🍣'],
                    ['name' => 'Сет "Ассорти"', 'price' => 5500, 'desc' => 'Набор из 32 популярных роллов', 'img' => '🍱'],
                ]
            ],
            [
                'category_key' => 'pharmacy',
                'name' => 'Аптека "Круглосуточная"',
                'address' => 'пр. Независимости, 67',
                'lat' => 53.2450,
                'lng' => 63.6420,
                'description' => 'Медикаменты • Товары для здоровья',
                'items' => [
                    ['name' => 'Витаминный комплекс', 'price' => 3500, 'desc' => 'Мультивитамины на каждый день', 'img' => '💊'],
                    ['name' => 'Набор первой помощи', 'price' => 2800, 'desc' => 'Всё необходимое в одной коробке', 'img' => '📦'],
                ]
            ],
            [
                'category_key' => 'groceries',
                'name' => 'Торговый Дом "Центр"',
                'address' => 'ул. Главная, 65',
                'lat' => 53.2101,
                'lng' => 63.6285,
                'description' => 'Продукты • Напитки • Бытовая химия',
                'items' => [
                    ['name' => 'Фруктовая корзина', 'price' => 4500, 'desc' => 'Сезонные фрукты, 3кг', 'img' => '🍎'],
                    ['name' => 'Набор продуктов "Базовый"', 'price' => 8500, 'desc' => 'Молоко, хлеб, яйца, крупы', 'img' => '🛒'],
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
