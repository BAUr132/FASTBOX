<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;

class TelegramService
{
    protected string $botToken;

    public function __construct()
    {
        $this->botToken = config('services.telegram.bot_token', '');
    }

    /**
     * Send a message to a specific Telegram chat.
     */
    public function sendMessage(int|string $chatId, string $text): bool
    {
        if (empty($this->botToken)) return false;

        try {
            $response = Http::timeout(5)->post("https://api.telegram.org/bot{$this->botToken}/sendMessage", [
                'chat_id' => $chatId,
                'text' => $text,
                'parse_mode' => 'HTML'
            ]);

            return $response->successful();
        } catch (\Exception $e) {
            \Log::error('Telegram notification failed: ' . $e->getMessage());
            return false;
        }
    }

    /**
     * Validate initData from Telegram.
     */
    public function validateInitData(string $initData): ?array
    {
        if (empty($this->botToken)) {
            return null;
        }

        parse_str($initData, $data);

        if (!isset($data['hash'])) {
            return null;
        }

        $hash = $data['hash'];
        unset($data['hash']);

        $dataCheckArr = [];
        foreach ($data as $key => $value) {
            $dataCheckArr[] = $key . '=' . $value;
        }

        sort($dataCheckArr);
        $dataCheckString = implode("\n", $dataCheckArr);

        $secretKey = hash_hmac('sha256', $this->botToken, 'WebAppData', true);
        $calculatedHash = bin2hex(hash_hmac('sha256', $dataCheckString, $secretKey, true));

        if (hash_equals($calculatedHash, $hash)) {
            return json_decode($data['user'], true);
        }

        return null;
    }
}
