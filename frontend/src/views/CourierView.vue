<script setup>
import { ref, computed } from 'vue';

const emit = defineEmits(['navigate']);

const fromAddress = ref('');
const toAddress = ref('');
const packageType = ref('1');
const estimatedPrice = ref(0);
const isCalculating = ref(false);

const navigateBack = () => {
  emit('navigate', 'main');
};

const calculatePrice = () => {
  // Simple local calculation for UI feedback before API call
  // In a real scenario, we'd send lat/lng to our backend
  if (fromAddress.value && toAddress.value) {
    isCalculating.value = true;
    // Mock calculation
    setTimeout(() => {
      estimatedPrice.value = 500 + (Math.floor(Math.random() * 10) * 100);
      isCalculating.value = false;
    }, 500);
  }
};

const confirmOrder = () => {
  alert(`Заказ оформлен! От: ${fromAddress.value} До: ${toAddress.value}. Цена: ${estimatedPrice.value} ₸`);
};
</script>

<template>
  <div id="screen-courier" class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 pt-4 px-4 pb-4 shadow-sm sticky top-0 z-30 flex items-center gap-4 border-b border-transparent dark:border-gray-700 transition-colors duration-300">
      <button @click="navigateBack" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Вызов курьера</h2>
    </header>

    <div class="p-6">
      <div class="bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl dark:shadow-black/20 p-6 border border-gray-100 dark:border-gray-700">
        <form @submit.prevent="confirmOrder" class="space-y-6">
          <div class="relative">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 ml-1 font-heading flex items-center gap-2">
              <i class="fas fa-map-marker-alt text-blue-600 dark:text-blue-400"></i> Откуда забрать (А)
            </label>
            <input v-model="fromAddress" @input="calculatePrice" type="text" placeholder="Улица, дом, подъезд" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-medium" required>
          </div>

          <div class="pl-6 -my-3">
            <div class="h-8 border-l-2 border-dashed border-blue-200 dark:border-blue-500/30"></div>
          </div>
          
          <div class="relative">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 ml-1 font-heading flex items-center gap-2">
              <i class="fas fa-flag-checkered text-yellow-500"></i> Куда привезти (Б)
            </label>
            <input v-model="toAddress" @input="calculatePrice" type="text" placeholder="Улица, дом, офис" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-medium" required>
          </div>
          
          <div class="pt-4">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 ml-1 font-heading flex items-center gap-2">
              <i class="fas fa-box text-gray-400 dark:text-gray-500"></i> Тип посылки
            </label>
            <select v-model="packageType" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 focus:ring-2 focus:ring-blue-500 outline-none transition-all font-medium appearance-none">
              <option value="1">📦 Стандарт (до 5 кг)</option>
              <option value="0.8">📄 Документы / Ключи</option>
              <option value="1.5">🐘 Тяжелый груз (до 20 кг)</option>
            </select>
          </div>

          <!-- Price Display -->
          <div v-if="fromAddress && toAddress" class="mt-6 p-4 bg-blue-50 dark:bg-blue-900/30 rounded-2xl border border-blue-100 dark:border-blue-800" :class="{'animate-pulse': isCalculating}">
            <div class="flex justify-between items-center">
              <span class="text-blue-600 dark:text-blue-400 font-bold">Предварительная цена:</span>
              <span class="text-2xl font-black text-blue-700 dark:text-blue-300">{{ estimatedPrice }} ₸</span>
            </div>
          </div>

          <button type="submit" class="w-full bg-blue-600 text-white font-bold font-heading text-lg py-4 rounded-2xl shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all transform active:scale-[0.98] flex items-center justify-center gap-2 mt-8">
            <span>Вызвать курьера</span>
            <i class="fas fa-motorcycle"></i>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
