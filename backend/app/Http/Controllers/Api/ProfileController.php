<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class ProfileController extends Controller
{
    /**
     * Instantly verify user for MVP/Demo purposes.
     */
    public function verify(Request $request): JsonResponse
    {
        $user = $request->user();
        
        $user->update([
            'kyc_status' => 'verified'
        ]);

        return response()->json([
            'message' => 'Identity verified successfully',
            'status' => 'verified',
            'user' => $user
        ], 200);
    }
}
