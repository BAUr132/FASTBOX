<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Order;
use App\Models\OrderItem;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\DB;

use App\Services\TelegramService;

class OrderController extends Controller
{
    protected TelegramService $telegram;

    public function __construct(TelegramService $telegram)
    {
        $this->telegram = $telegram;
    }

    /**
     * Create a new order (Shop, Courier, or Intercity).
     */
    public function store(Request $request): JsonResponse
    {
        // SIMPLIFIED VALIDATION for MVP
        $validated = $request->validate([
            'type' => 'required|in:shop,courier,intercity',
            'pickup_address' => 'nullable|string',
            'pickup_lat' => 'nullable|numeric',
            'pickup_lng' => 'nullable|numeric',
            'delivery_address' => 'nullable|string',
            'delivery_lat' => 'nullable|numeric',
            'delivery_lng' => 'nullable|numeric',
            'items' => 'nullable|array',
            'package_details' => 'nullable|string',
            'trip_id' => 'nullable',
            'payment_method' => 'nullable',
        ]);

        $result = DB::transaction(function () use ($request, $validated) {
            $user = $request->user();
            
            // REMOVED KYC CHECK FOR MVP

            $order = new Order();
            $order->user_id = $user->id;
            $order->type = $validated['type'];
            $order->status = 'new';
            $order->payment_method = $validated['payment_method'] ?? 'cash';
            $order->pickup_address = $validated['pickup_address'] ?? null;
            $order->pickup_lat = $validated['pickup_lat'] ?? null;
            $order->pickup_lng = $validated['pickup_lng'] ?? null;
            $order->delivery_address = $validated['delivery_address'] ?? null;
            $order->delivery_lat = $validated['delivery_lat'] ?? null;
            $order->delivery_lng = $validated['delivery_lng'] ?? null;
            $order->package_details = $validated['package_details'] ?? null;
            $order->trip_id = $validated['trip_id'] ?? null;

            if ($validated['type'] === 'shop' && !empty($validated['items'])) {
                $totalPrice = 0;
                $order->save(); 

                foreach ($validated['items'] as $item) {
                    $productId = is_numeric($item['product_id']) ? $item['product_id'] : null;
                    $product = $productId ? Product::find($productId) : null;
                    
                    $unitPrice = $product ? $product->price : 1000;
                    $price = $unitPrice * $item['quantity'];
                    $totalPrice += $price;

                    if ($productId) {
                        OrderItem::create([
                            'order_id' => $order->id,
                            'product_id' => $productId,
                            'quantity' => $item['quantity'],
                            'price' => $unitPrice,
                        ]);
                    }
                }
                $order->total_price = $totalPrice;
                $order->delivery_fee = 500;
                $order->save();
            } 
            elseif ($validated['type'] === 'courier') {
                $distance = $this->calculateDistance(
                    $validated['pickup_lat'] ?? 0, $validated['pickup_lng'] ?? 0,
                    $validated['delivery_lat'] ?? 0, $validated['delivery_lng'] ?? 0
                );
                
                $order->delivery_fee = 500 + (round($distance) * 100);
                $order->save();
            }
            else {
                $order->save();
            }

            return $order;
        });

        // Always return success for MVP
        return response()->json([
            'message' => 'Order created successfully',
            'order' => $result,
        ], 200);
    }

    /**
     * Courier accepts an order.
     */
    public function accept(Request $request, $id): JsonResponse
    {
        $order = Order::findOrFail($id);

        if ($order->status !== 'new') {
            return response()->json(['message' => 'Order already taken or unavailable'], 400);
        }

        $order->update([
            'courier_id' => $request->user()->id,
            'status' => 'accepted'
        ]);

        return response()->json([
            'message' => 'Order accepted by courier',
            'order' => $order
        ]);
    }

    /**
     * Courier completes an order.
     */
    public function complete(Request $request, $id): JsonResponse
    {
        $order = Order::where('id', $id)
            ->where('courier_id', $request->user()->id)
            ->firstOrFail();

        $order->update(['status' => 'completed']);

        return response()->json([
            'message' => 'Order completed successfully',
            'order' => $order
        ]);
    }

    /**
     * Confirm order pickup via QR handshake.
     */
    public function confirmViaQr(Request $request, $id): JsonResponse
    {
        $order = Order::findOrFail($id);

        $order->update([
            'status' => 'delivering',
            // 'scanned_at' => now(), // Temporarily commented if column doesn't exist
        ]);

        return response()->json([
            'success' => true,
            'message' => 'Handshake confirmed. Order is in transit.',
            'order' => $order
        ]);
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
     * List user orders (both as a customer and as a courier).
     */
    public function index(Request $request): JsonResponse
    {
        $userId = $request->user()->id;

        $orders = Order::where(function ($query) use ($userId) {
                $query->where('user_id', $userId)
                      ->orWhere('courier_id', $userId);
            })
            ->with(['items.product', 'trip'])
            ->latest()
            ->get();
            
        return response()->json($orders);
    }
}
