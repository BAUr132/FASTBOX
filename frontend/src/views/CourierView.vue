<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useCartStore } from '../store/useCart';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const cartStore = useCartStore();

const fromAddress = ref('');
const toAddress = ref('');
const packageType = ref('1');
const estimatedPrice = ref(0);
const isCalculating = ref(false);
const isVerified = ref(true);

const kostanayStreets = [
  'ул. Абая', 'ул. Баймагамбетова', 'ул. Алтынсарина', 'ул. Тауелсиздик',
  'пр. Кобланды Батыра', 'ул. Каирбекова', 'ул. Бородина', 'ул. Гоголя',
  'ул. Павлова', 'ул. Майлина', 'ул. Чкалова', 'ул. Карбышева'
];

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

const confirmOrder = async () => {
  const tg = window.Telegram?.WebApp;
  const orderData = {
    type: 'courier',
    status: 'new',
    pickup_address: fromAddress.value,
    delivery_address: toAddress.value,
    delivery_fee: estimatedPrice.value,
    package_details: `Тип: ${packageType.value}`,
    payment_method: 'cash'
  };

  try {
    if (tg) tg.MainButton.showProgress();
    await api.post('/orders', orderData);

    if (tg) {
      tg.MainButton.hideProgress();
      tg.MainButton.hide();
      tg.showAlert(`✅ Заказ успешно создан! Курьер уже в пути. Вы можете отслеживать его в профиле.`);
    } else {
      alert(`✅ Заказ создан! Доставка: ${estimatedPrice.value} ₸. Переходим в профиль.`);
    }
    emit('navigate', 'profile');
  } catch (e) {
    console.error('Courier order backend failed:', e);
    if (tg) {
       tg.MainButton.hideProgress();
       tg.showAlert('Ошибка: не удалось создать заказ. Попробуйте еще раз.');
    }
  }
};
</script>

<template>
  <div id="screen-courier" class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 pt-4 px-4 pb-4 shadow-sm sticky top-0 z-30 flex items-center gap-4 border-b border-transparent dark:border-gray-700">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">Вызов курьера</h2>
    </header>

    <div class="p-6">
      <div class="bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl p-6 border border-gray-100 dark:border-gray-700">
        <form @submit.prevent="confirmOrder" class="space-y-6">
          <div>
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <i class="fas fa-map-marker-alt text-blue-600"></i> Откуда забрать (А)
            </label>
            <input v-model="fromAddress" list="streets" @input="calculatePrice" type="text" placeholder="ул. Абая, 150" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <div>
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <i class="fas fa-flag-checkered text-yellow-500"></i> Куда привезти (Б)
            </label>
            <input v-model="toAddress" list="streets" @input="calculatePrice" type="text" placeholder="ул. Баймагамбетова, 3" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 outline-none focus:ring-2 focus:ring-blue-500">
          </div>

          <datalist id="streets">
            <option v-for="street in kostanayStreets" :key="street" :value="street"></option>
          </datalist>
          
          <div>
            <label class="block text-sm font-bold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-2">
              <i class="fas fa-box text-gray-400"></i> Тип посылки
            </label>
            <select v-model="packageType" class="w-full bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-white border border-gray-200 dark:border-gray-600 rounded-2xl p-4 outline-none appearance-none">
              <option value="1">📦 Стандарт (до 5 кг)</option>
              <option value="0.8">📄 Документы / Ключи</option>
              <option value="1.5">🐘 Тяжелый груз (до 20 кг)</option>
            </select>
          </div>

          <div v-if="fromAddress && toAddress" class="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-2xl border border-blue-100 dark:border-blue-800" :class="{'animate-pulse': isCalculating}">
            <div class="flex justify-between items-center">
              <span class="text-blue-600 dark:text-blue-400 font-bold">Цена:</span>
              <span class="text-2xl font-black text-blue-700 dark:text-blue-300">{{ estimatedPrice }} ₸</span>
            </div>
          </div>

          <button type="submit" class="w-full bg-blue-600 text-white font-bold text-lg py-4 rounded-2xl shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
            <span>Вызвать курьера</span>
            <i class="fas fa-motorcycle"></i>
          </button>
        </form>
      </div>
    </div>
  </div>
</template>