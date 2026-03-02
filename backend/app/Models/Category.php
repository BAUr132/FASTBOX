<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Category extends Model
{
    protected $fillable = ['name', 'icon'];

    public function shops(): HasMany
    {
        return $this->hasMany(Shop::class);
    }
}
