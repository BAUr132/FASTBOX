<?php

namespace Database\Seeders;

use App\Models\User;
use App\Models\Category;
use App\Models\Shop;
use App\Models\Product;
use Illuminate\Database\Seeder;

class DatabaseSeeder extends Seeder
{
    public function run(): void
    {
        // 1. Categories
        $catBurgers = Category::create(['name' => 'Бургеры', 'icon' => 'fa-hamburger']);
        $catSushi = Category::create(['name' => 'Суши', 'icon' => 'fa-fish']);
        $catPharmacy = Category::create(['name' => 'Аптеки', 'icon' => 'fa-pills']);
        $catGroceries = Category::create(['name' => 'Продукты', 'icon' => 'fa-shopping-cart']);

        // 2. Shops
        $shop1 = Shop::create([
            'category_id' => $catBurgers->id,
            'name' => 'Burger House',
            'description' => 'Фастфуд • Бургеры',
            'address' => 'ул. Тауелсиздик, 12',
            'lat' => 53.2144,
            'lng' => 63.6246
        ]);

        $shop2 = Shop::create([
            'category_id' => $catSushi->id,
            'name' => 'Суши Мастер',
            'description' => 'Японская кухня • Роллы',
            'address' => 'пр. Абая, 45',
            'lat' => 53.2198,
            'lng' => 63.6354
        ]);

        // 3. Products for Shop 1
        Product::create(['shop_id' => $shop1->id, 'name' => 'Чизбургер Классик', 'price' => 1500, 'description' => 'Котлета из говядины, сыр чеддер, соус', 'image' => '🍔']);
        Product::create(['shop_id' => $shop1->id, 'name' => 'Двойной Смэш Бургер', 'price' => 2200, 'description' => 'Две котлеты, бекон, халапеньо', 'image' => '🍔']);
        Product::create(['shop_id' => $shop1->id, 'name' => 'Картофель Фри', 'price' => 800, 'description' => 'Хрустящая картошка', 'image' => '🍟']);

        // 4. Products for Shop 2
        Product::create(['shop_id' => $shop2->id, 'name' => 'Ролл Филадельфия', 'price' => 2500, 'description' => 'Лосось, сливочный сыр, огурец', 'image' => '🍣']);
        
        // 5. Test User
        User::updateOrCreate(
            ['email' => 'test@example.com'],
            ['name' => 'Test User', 'password' => bcrypt('password'), 'kyc_status' => 'verified']
        );
    }
}
