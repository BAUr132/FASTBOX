<?php

use App\Http\Controllers\Api\ShopController;
use App\Http\Controllers\Api\AuthController;
use App\Http\Controllers\Api\OrderController;
use App\Http\Controllers\Api\TripController;
use App\Http\Controllers\Api\KYCController;
use App\Http\Controllers\Api\ProfileController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

/*
|--------------------------------------------------------------------------
| API Routes
|--------------------------------------------------------------------------
*/

Route::get('/user', function (Request $request) {
    return $request->user();
})->middleware('auth:sanctum');

// Shop & Menu Endpoints
Route::get('/categories', [ShopController::class, 'categories']);
Route::get('/shops', [ShopController::class, 'shops']);
Route::get('/shops/{id}/menu', [ShopController::class, 'menu']);

// Auth
Route::post('/auth/telegram', [AuthController::class, 'login']);
Route::post('/auth/guest', [AuthController::class, 'guestLogin']);

// Authenticated Routes
Route::middleware('auth:sanctum')->group(function () {
    // Orders
    Route::get('/orders', [OrderController::class, 'index']);
    Route::post('/orders', [OrderController::class, 'store']);
    Route::post('/orders/{id}/accept', [OrderController::class, 'accept']);
    Route::post('/orders/{id}/complete', [OrderController::class, 'complete']);
    
    // Intercity Trips
    Route::get('/trips', [TripController::class, 'index']);
    Route::post('/trips', [TripController::class, 'store']);
    
    // KYC Verification
    Route::post('/kyc/upload', [KYCController::class, 'uploadID']);
    Route::post('/kyc/verify', [ProfileController::class, 'verify']);
});
