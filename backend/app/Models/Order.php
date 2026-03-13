<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Order extends Model
{
    protected $fillable = [
        'user_id', 
        'courier_id', 
        'trip_id', 
        'type', 
        'status', 
        'payment_method',
        'pickup_address', 
        'pickup_lat',
        'pickup_lng',
        'delivery_address', 
        'delivery_lat',
        'delivery_lng',
        'total_price', 
        'delivery_fee',
        'package_details'
    ];

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function courier(): BelongsTo
    {
        return $this->belongsTo(User::class, 'courier_id');
    }

    public function trip(): BelongsTo
    {
        return $this->belongsTo(Trip::class);
    }

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }
}
