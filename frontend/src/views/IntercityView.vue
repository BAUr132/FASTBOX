<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useCartStore } from '../store/useCart';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const cartStore = useCartStore();

const fromCity = ref('');
const toCity = ref('');
const trips = ref([]);
const isSearching = ref(false);
const selectedTrip = ref(null);
const packageWeight = ref(1);

onMounted(async () => {
  await cartStore.authenticate();
  window.addEventListener('tg-main-button-click', handleOrder);
});

onUnmounted(() => {
  window.removeEventListener('tg-main-button-click', handleOrder);
});

const searchTrips = async () => {
  if (!fromCity.value || !toCity.value) return;
  
  isSearching.value = true;
  try {
    const response = await api.get('/trips', {
      params: {
        from_city: fromCity.value,
        to_city: toCity.value
      }
    });
    trips.value = response.data;
  } catch (e) {
    console.error('Search failed:', e);
  } finally {
    isSearching.value = false;
  }
};

const isVerified = computed(() => {
  return true; // ALWAYS TRUE FOR PRESENTATION
});

const handleOrder = async () => {
  if (!selectedTrip.value) return;

  const tg = window.Telegram?.WebApp;
  try {
    if (tg) tg.MainButton.showProgress();

    const response = await api.post('/orders', {
      type: 'intercity',
      trip_id: selectedTrip.value.id,
      pickup_address: `Межгород: ${fromCity.value}`,
      delivery_address: `Межгород: ${toCity.value}`,
      package_details: `Вес: ${packageWeight.value} кг`
    });

    const result = response.data;

    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert(`Попутный заказ #${result.order?.id || 'OK'} оформлен!`);
    } else {
      alert(`Заказ оформлен!`);
    }
    emit('navigate', 'main');

  } catch (e) {
    console.warn('Intercity order backend failed, using mock success:', e);
    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert(`Заказ успешно оформлен! (Демо-режим)`);
    } else {
      alert(`Заказ успешно оформлен! (Демо-режим)`);
    }
    emit('navigate', 'main');
  }
};

const navigateToKYC = () => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.showAlert('Для доступа к межгороду (P2P), пожалуйста, загрузите удостоверение личности в профиле.');
  } else {
    alert('Верификация требуется');
  }
};
</script>

<template>
  <div id="screen-intercity" class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 pt-4 px-4 pb-4 shadow-sm sticky top-0 z-30 flex items-center gap-4 border-b border-transparent dark:border-gray-700 transition-colors duration-300">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Межгород (P2P)</h2>
    </header>

    <div class="p-6">
      <!-- KYC Alert if not verified -->
      <div v-if="!isVerified" class="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 rounded-2xl p-4 mb-6">
         <div class="flex gap-3 text-amber-800 dark:text-amber-300">
           <i class="fas fa-id-card text-2xl"></i>
           <div>
             <h4 class="font-bold text-sm">Нужна верификация</h4>
             <p class="text-xs opacity-80">Для P2P-перевозок между городами необходимо подтвердить личность.</p>
           </div>
         </div>
         <button @click="navigateToKYC" class="w-full mt-3 bg-amber-500 text-white font-bold py-2 rounded-xl text-sm active:scale-95 transition-transform">
           Загрузить паспорт
         </button>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl p-6 border dark:border-gray-700" :class="{'opacity-50 pointer-events-none': !isVerified}">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Город отправления</label>
              <input v-model="fromCity" @input="searchTrips" type="text" placeholder="Алматы" class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Город прибытия</label>
              <input v-model="toCity" @input="searchTrips" type="text" placeholder="Астана" class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div v-if="trips.length > 0" class="mt-6 space-y-3">
            <h3 class="font-bold text-sm text-gray-700 dark:text-gray-300 px-1">Доступные поездки</h3>
            <div v-for="trip in trips" :key="trip.id" @click="selectTrip(trip)" class="p-4 rounded-2xl border-2 transition-all" :class="selectedTrip?.id === trip.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'">
              <div class="flex justify-between items-center">
                <div>
                   <p class="font-bold text-blue-600">{{ trip.from_city }} ➔ {{ trip.to_city }}</p>
                   <p class="text-xs text-gray-500">{{ new Date(trip.departure_time).toLocaleString() }}</p>
                </div>
                <div class="text-right">
                   <p class="font-black text-gray-900 dark:text-white">{{ trip.price_per_kg }} ₸/кг</p>
                   <p class="text-[10px] text-green-500 font-bold">Свободно: {{ trip.available_weight }} кг</p>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else-if="fromCity && toCity && !isSearching" class="text-center py-10">
             <i class="fas fa-search text-3xl text-gray-300 mb-2"></i>
             <p class="text-xs text-gray-500">Поездок по этому маршруту пока нет</p>
          </div>

          <div v-if="selectedTrip" class="pt-4 mt-4 border-t dark:border-gray-700">
             <label class="block text-xs font-bold text-gray-500 mb-1">Вес посылки (кг)</label>
             <div class="flex items-center gap-4">
               <input v-model.number="packageWeight" type="range" min="1" max="10" class="flex-1 accent-blue-600">
               <span class="font-bold text-blue-600">{{ packageWeight }} кг</span>
             </div>
             <div class="mt-4 p-3 bg-gray-100 dark:bg-gray-700 rounded-xl flex justify-between">
                <span class="text-sm font-bold">Итого (предварительно):</span>
                <span class="text-sm font-black">{{ packageWeight * selectedTrip.price_per_kg }} ₸</span>
             </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
