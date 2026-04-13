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
        $lat = $request->lat ?? 0;
        $lng = $request->lng ?? 0;

        $query = Trip::with('user')
            ->selectRaw("*, ( 6371 * acos( cos( radians(?) ) * cos( radians(COALESCE(lat, 0)) ) * cos( radians(COALESCE(lng, 0)) - radians(?) ) + sin( radians(?) ) * sin( radians(COALESCE(lat, 0)) ) ) ) AS distance", [$lat, $lng, $lat]);

        if ($request->has('from_city')) {
            $query->where('from_city', 'like', '%' . $request->from_city . '%');
        }

        if ($request->has('to_city')) {
            $query->where('to_city', 'like', '%' . $request->to_city . '%');
        }

        $trips = $query->where('status', 'active')
            ->orderBy('distance')
            ->get();

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
            'departure_date' => 'required|date',
            'price_per_kg' => 'required|numeric|min:0',
            'transport_details' => 'nullable|string',
        ]);

        $trip = Trip::create([
            'user_id' => $request->user()->id,
            'from_city' => $validated['from_city'],
            'to_city' => $validated['to_city'],
            'departure_date' => $validated['departure_date'],
            'price_per_kg' => $validated['price_per_kg'],
            'transport_details' => $validated['transport_details'],
            'status' => 'active',
        ]);

        return response()->json([
            'message' => 'Trip created successfully',
            'trip' => $trip
        ], 201);
    }
}
