<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

class OrderController extends Controller
{
    /**
     * Create a new order (Shop, Courier, or Intercity).
     */
    public function store(Request $request): JsonResponse
    {
        $validated = $request->validate([
            'type' => 'required|in:shop,courier,intercity',
            'pickup_address' => 'nullable|string',
            'pickup_lat' => 'nullable|numeric',
            'pickup_lng' => 'nullable|numeric',
            'delivery_address' => 'nullable|string',
            'delivery_lat' => 'nullable|numeric',
            'delivery_lng' => 'nullable|numeric',
            'items' => 'required_if:type,shop|array',
            'items.*.product_id' => 'required_with:items|exists:products,id',
            'items.*.quantity' => 'required_with:items|integer|min:1',
            'package_details' => 'nullable|string',
            'trip_id' => 'nullable|exists:trips,id',
        ]);

        return DB::transaction(function () use ($request, $validated) {
            $user = $request->user();
            $order = new Order();
            $order->user_id = $user->id;
            $order->type = $validated['type'];
            $order->status = 'new';
            $order->pickup_address = $validated['pickup_address'] ?? null;
            $order->pickup_lat = $validated['pickup_lat'] ?? null;
            $order->pickup_lng = $validated['pickup_lng'] ?? null;
            $order->delivery_address = $validated['delivery_address'] ?? null;
            $order->delivery_lat = $validated['delivery_lat'] ?? null;
            $order->delivery_lng = $validated['delivery_lng'] ?? null;
            $order->package_details = $validated['package_details'] ?? null;
            $order->trip_id = $validated['trip_id'] ?? null;

            if ($validated['type'] === 'shop') {
                $totalPrice = 0;
                $order->save(); // Save first to get ID

                foreach ($validated['items'] as $item) {
                    $product = Product::find($item['product_id']);
                    $price = $product->price * $item['quantity'];
                    $totalPrice += $price;

                    OrderItem::create([
                        'order_id' => $order->id,
                        'product_id' => $product->id,
                        'quantity' => $item['quantity'],
                        'price' => $product->price,
                    ]);
                }
                $order->total_price = $totalPrice;
                $order->delivery_fee = 500; // Fixed flat fee for shop delivery in MVP
                $order->save();
            } 
            elseif ($validated['type'] === 'courier') {
                // Calculate fee based on distance (Haversine formula)
                $distance = $this->calculateDistance(
                    $validated['pickup_lat'], $validated['pickup_lng'],
                    $validated['delivery_lat'], $validated['delivery_lng']
                );
                
                // Base price 500 + 100 per km
                $order->delivery_fee = 500 + (round($distance) * 100);
                $order->save();
            }
            else {
                $order->save();
            }

            return response()->json([
                'message' => 'Order created successfully',
                'order' => $order->load('items.product'),
            ], 201);
        });
    }

    /**
     * Simple Haversine implementation to calculate distance in km.
     */
    private function calculateDistance($lat1, $lng1, $lat2, $lng2)
    {
        $earthRadius = 6371; // km
        $dLat = deg2rad($lat2 - $lat1);
        $dLng = deg2rad($lng2 - $lng1);
        
        $a = sin($dLat/2) * sin($dLat/2) +
             cos(deg2rad($lat1)) * cos(deg2rad($lat2)) *
             sin($dLng/2) * sin($dLng/2);
        $c = 2 * atan2(sqrt($a), sqrt(1-$a));
        
        return $earthRadius * $c;
    }

    /**
     * List user orders.
     */
    public function index(Request $request): JsonResponse
    {
        $orders = Order::where('user_id', $request->user()->id)
            ->with(['items.product', 'trip'])
            ->latest()
            ->get();
            
        return response()->json($orders);
    }
}
