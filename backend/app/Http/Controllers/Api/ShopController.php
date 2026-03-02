<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\Category;
use App\Models\Shop;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ShopController extends Controller
{
    /**
     * Get all categories for filters.
     */
    public function categories(): JsonResponse
    {
        return response()->json(Category::all());
    }

    /**
     * Get shops, optionally filtered by category.
     */
    public function shops(Request $request): JsonResponse
    {
        $query = Shop::with('category');

        if ($request->has('category_id')) {
            $query->where('category_id', $request->category_id);
        }

        return response()->json($query->get());
    }

    /**
     * Get specific shop with its full menu.
     */
    public function menu(int $id): JsonResponse
    {
        $shop = Shop::with('products')->findOrFail($id);
        return response()->json($shop);
    }
}
