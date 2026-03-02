<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Trip;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class TripController extends Controller
{
    /**
     * Search for available trips between cities.
     */
    public function index(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'from_city' => 'required|string',
            'to_city' => 'required|string',
            'date' => 'nullable|date',
        ]);

        $query = Trip::where('from_city', $validated['from_city'])
            ->where('to_city', $validated['to_city'])
            ->where('status', 'active');

        if (!empty($validated['date'])) {
            $query->whereDate('departure_time', $validated['date']);
        }

        $trips = $query->with('user')->get();

        return response()->json($trips);
    }

    /**
     * Create a new trip (for crowd-shipping drivers).
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'from_city' => 'required|string',
            'to_city' => 'required|string',
            'departure_time' => 'required|date',
            'available_weight' => 'required|numeric|min:1',
            'price_per_kg' => 'required|numeric|min:0',
        ]);

        $trip = Trip::create([
            'user_id' => $request->user()->id,
            'from_city' => $validated['from_city'],
            'to_city' => $validated['to_city'],
            'departure_time' => $validated['departure_time'],
            'available_weight' => $validated['available_weight'],
            'price_per_kg' => $validated['price_per_kg'],
            'status' => 'active',
        ]);

        return response()->json([
            'message' => 'Trip created successfully',
            'trip' => $trip
        ], 201);
    }
}
