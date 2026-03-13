<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
    {
        // Check if column exists before renaming
        if (Schema::hasColumn('users', 'verification_status')) {
            Schema::table('users', function (Blueprint $table) {
                $table->renameColumn('verification_status', 'kyc_status_old');
            });
            
            Schema::table('users', function (Blueprint $table) {
                $table->string('kyc_status')->default('none')->after('kyc_status_old');
            });
            
            // Sync values if needed in a real app, but for MVP we just drop old
            Schema::table('users', function (Blueprint $table) {
                $table->dropColumn('kyc_status_old');
            });
        }
    }

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::table('users', function (Blueprint $table) {
            $table->renameColumn('kyc_status', 'verification_status');
        });
    }
};
