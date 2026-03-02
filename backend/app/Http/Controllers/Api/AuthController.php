<?php

namespace App\Http\Controllers\Api;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Services\TelegramService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class AuthController extends Controller
{
    public function __construct(protected TelegramService $telegram) {}

    public function login(Request $request): JsonResponse
    {
        $initData = $request->input('initData');

        if (!$initData) {
            return response()->json(['error' => 'No initData provided'], 400);
        }

        $telegramUser = $this->telegram->validateInitData($initData);

        if (!$telegramUser) {
            return response()->json(['error' => 'Invalid initData'], 401);
        }

        $user = User::updateOrCreate(
            ['telegram_id' => $telegramUser['id']],
            ['name' => $telegramUser['first_name'] . ' ' . ($telegramUser['last_name'] ?? '')]
        );

        $token = $user->createToken('telegram_auth')->plainTextToken;

        return response()->json([
            'user' => $user,
            'token' => $token
        ]);
    }
}
