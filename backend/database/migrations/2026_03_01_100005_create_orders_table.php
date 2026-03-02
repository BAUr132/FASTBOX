<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->onDelete('cascade'); // Customer
            $table->foreignId('courier_id')->nullable()->constrained('users')->onDelete('set null'); // Assigned Courier (if local)
            $table->foreignId('trip_id')->nullable()->constrained('trips')->onDelete('set null'); // Assigned Intercity Trip (if P2P)
            
            $table->enum('type', ['shop', 'courier', 'intercity']);
            $table->enum('status', ['new', 'accepted', 'delivering', 'completed', 'cancelled'])->default('new');
            
            // Addresses & Coordinates
            $table->string('pickup_address')->nullable();
            $table->decimal('pickup_lat', 10, 8)->nullable();
            $table->decimal('pickup_lng', 11, 8)->nullable();
            
            $table->string('delivery_address')->nullable();
            $table->decimal('delivery_lat', 10, 8)->nullable();
            $table->decimal('delivery_lng', 11, 8)->nullable();
            
            // Financials
            $table->decimal('total_price', 10, 2)->default(0); // Subtotal for items
            $table->decimal('delivery_fee', 10, 2)->default(0); // Calculated delivery fee
            
            $table->text('package_details')->nullable(); // For courier/intercity
            
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('orders');
    }
};
