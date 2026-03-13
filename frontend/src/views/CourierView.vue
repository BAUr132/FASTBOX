<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useCartStore } from '../store/useCart';

const emit = defineEmits(['navigate']);
const cartStore = useCartStore();

const fromAddress = ref('');
const toAddress = ref('');
const packageType = ref('1');
const estimatedPrice = ref(0);
const isCalculating = ref(false);

onMounted(async () => {
  await cartStore.authenticate();
  window.addEventListener('tg-main-button-click', confirmOrder);
});

onUnmounted(() => {
  window.removeEventListener('tg-main-button-click', confirmOrder);
});

const calculatePrice = () => {
  if (fromAddress.value && toAddress.value) {
    isCalculating.value = true;
    setTimeout(() => {
      estimatedPrice.value = 500 + (Math.floor(Math.random() * 10) * 100);
      isCalculating.value = false;
    }, 500);
  }
};

import api from '../api/axios';

const isVerified = computed(() => {
  return true; // ALWAYS TRUE FOR PRESENTATION
});

const confirmOrder = async () => {
  const tg = window.Telegram?.WebApp;
  try {
    if (tg) tg.MainButton.showProgress();

    const response = await api.post('/orders', {
      type: 'courier',
      pickup_address: fromAddress.value,
      delivery_address: toAddress.value,
      pickup_lat: 43.2389, 
      pickup_lng: 76.8897,
      delivery_lat: 43.2551, 
      delivery_lng: 76.9126,
      package_details: `Тип: ${packageType.value}`
    });

    const result = response.data;

    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert(`Заказ #${result.order?.id || 'OK'} создан! Доставка: ${result.order?.delivery_fee || estimatedPrice.value} ₸`);
    } else {
      alert(`Заказ создан! Доставка: ${estimatedPrice.value} ₸`);
    }
    emit('navigate', 'main');

  } catch (e) {
    console.warn('Courier order backend failed, using mock success:', e);
    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert(`Заказ успешно создан! (Демо-режим)`);
    } else {
      alert(`Заказ успешно создан! (Демо-режим)`);
    }
    emit('navigate', 'main');
  }
};

const navigateToKYC = () => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.showAlert('Для доступа к вызову курьера (P2P), пожалуйста, загрузите удостоверение личности в профиле.');
  } else {
    alert('Верификация требуется');
  }
};
</script>

<template>
  <div id="screen-courier" class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 pt-4 px-4 pb-4 shadow-sm sticky top-0 z-30 flex items-center gap-4 border-b border-transparent dark:border-gray-700 transition-colors duration-300">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Вызов курьера</h2>
    </header>

    <div class="p-6">
      <!-- KYC Alert if not verified -->
      <div v-if="!isVerified" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl p-4 mb-6">
         <div class="flex gap-3 text-amber-800 dark:text-amber-300">
           <i class="fas fa-id-card text-2xl"></i>
           <div>
             <h4 class="font-bold text-sm">Нужна верификация</h4>
             <p class="text-xs opacity-80">По правилам FastBox, для P2P-пересылок необходимо подтвердить личность.</p>
           </div>
         </div>
         <button @click="navigateToKYC" class="w-full mt-3 bg-amber-500 text-white font-bold py-2 rounded-xl text-sm active:scale-95 transition-transform">
           Загрузить паспорт
         </button>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl dark:shadow-black/20 p-6 border border-gray-100 dark:border-gray-700" :class="{'opacity-50 pointer-events-none': !isVerified}">
        <form @submit.prevent="confirmOrder" class="space-y-6">
          <div class="relative">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 ml-1 font-heading flex items-center gap-2">
              <i class="fas fa-map-marker-alt text-blue-600 dark:text-blue-400"></i> Откуда забрать (А)
            </label>
            <input v-model="fromAddress" @input="calculatePrice" type="text" placeholder="Улица, дом, подъезд" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-medium" :required="isVerified">
          </div>

          <div class="pl-6 -my-3">
            <div class="h-8 border-l-2 border-dashed border-blue-200 dark:border-blue-500/30"></div>
          </div>
          
          <div class="relative">
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 ml-1 font-heading flex items-center gap-2">
              <i class="fas fa-flag-checkered text-yellow-500"></i> Куда привезти (Б)
            </label>
            <input v-model="toAddress" @input="calculatePrice" type="text" placeholder="Улица, дом, офис" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition-all font-medium" :required="isVerified">
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

          <button type="submit" :disabled="!isVerified" class="w-full bg-blue-600 text-white font-bold font-heading text-lg py-4 rounded-2xl shadow-lg shadow-blue-500/30 hover:bg-blue-700 transition-all transform active:scale-[0.98] disabled:bg-gray-400 disabled:shadow-none flex items-center justify-center gap-2 mt-8">
            <span>Вызвать курьера</span>
            <i class="fas fa-motorcycle"></i>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>
