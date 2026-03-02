<?php

namespace App\Services;

class TelegramService
{
    protected string $botToken;

    public function __construct()
    {
        $this->botToken = config('services.telegram.bot_token', '');
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
