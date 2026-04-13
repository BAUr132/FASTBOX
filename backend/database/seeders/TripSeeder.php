<?php

namespace Database\Seeders;

use App\Models\Trip;
use App\Models\User;
use Illuminate\Database\Seeder;
use Illuminate\Support\Facades\DB;

class TripSeeder extends Seeder
{
    public function run(): void
    {
        DB::statement('SET FOREIGN_KEY_CHECKS=0;');
        Trip::truncate();
        DB::statement('SET FOREIGN_KEY_CHECKS=1;');

        // Нам нужен хотя бы один пользователь для user_id (водитель)
        $user = User::first() ?: User::create([
            'name' => 'Александр (Водитель)',
            'email' => 'driver@fastbox.kz',
            'password' => bcrypt('password'),
            'role' => 'courier',
            'kyc_status' => 'verified'
        ]);

        $trips = [
            [
                'user_id' => $user->id,
                'from_city' => 'Костанай',
                'to_city' => 'Астана',
                'departure_date' => now()->addDays(1)->setTime(8, 0),
                'price_per_kg' => 500,
                'status' => 'active',
                'transport_details' => 'Легковой автомобиль, багажник свободен'
            ],
            [
                'user_id' => $user->id,
                'from_city' => 'Костанай',
                'to_city' => 'Рудный',
                'departure_date' => now()->addHours(5),
                'price_per_kg' => 200,
                'status' => 'active',
                'transport_details' => 'Минивэн'
            ],
            [
                'user_id' => $user->id,
                'from_city' => 'Рудный',
                'to_city' => 'Костанай',
                'departure_date' => now()->addHours(8),
                'price_per_kg' => 200,
                'status' => 'active',
                'transport_details' => 'Грузовой отсек'
            ]
        ];

        foreach ($trips as $trip) {
            Trip::create($trip);
        }
    }
}
