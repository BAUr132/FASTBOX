<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;

class KYCController extends Controller
{
    /**
     * Upload ID card for verification.
     */
    public function uploadID(Request $request): JsonResponse
    {
        $request->validate([
            'id_card' => 'required|image|mimes:jpg,jpeg,png|max:5120', // Max 5MB
        ]);

        $user = $request->user();

        if ($request->hasFile('id_card')) {
            // Save to private storage (not publicly accessible)
            $path = $request->file('id_card')->store('private/kyc', 'local');

            // Update user record with path and set status to pending
            $user->update([
                'id_card_photo' => $path, // Assuming this column exists, if not it will be ignored by $fillable
                'kyc_status' => 'pending'
            ]);

            return response()->json([
                'message' => 'Document uploaded successfully. Verification is pending.',
                'status' => 'pending'
            ]);
        }

        return response()->json(['error' => 'No file provided'], 400);
    }

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
            'user' => $user
        ]);
    }
}
