<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '../store/useAuth';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const authStore = useAuthStore();
const availableOrdersCount = ref(0);

const navigateTo = (screen) => {
  emit('navigate', screen);
};

const fetchCount = async () => {
  if (authStore.isCourierMode) {
    try {
      const response = await api.get('/orders');
      availableOrdersCount.value = response.data.filter(o => o.status === 'new').length;
    } catch (e) {
      console.error(e);
    }
  }
};

onMounted(() => {
  fetchCount();
  // Telegram Web App initialization
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready();
    window.Telegram.WebApp.expand();
  }
});
</script>

<template>
  <div id="screen-main" class="screen screen-fade-in">
    <header class="hero-pattern pt-8 pb-12 px-6 rounded-b-[2.5rem] shadow-xl relative overflow-hidden dark:bg-blue-800">
      <div class="absolute bg-blue-400 w-64 h-64 rounded-full filter blur-3xl opacity-20 -top-20 -right-20 pointer-events-none"></div>
      <div class="relative z-10">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-2">
            <div class="w-10 h-10 bg-white/20 backdrop-blur-sm text-white rounded-xl flex items-center justify-center text-lg shadow-sm">
              <i class="fas fa-box-open"></i>
            </div>
            <span class="font-bold text-xl text-white tracking-tight font-heading">FastBox</span>
          </div>
        </div>
        <h1 class="text-3xl font-extrabold text-white leading-tight">Что доставим <br> сегодня?</h1>
      </div>
    </header>

    <div class="px-6 -mt-6 relative z-20 space-y-4 pb-10">
      <!-- Courier Dashboard -->
      <div v-if="authStore.isCourierMode" class="bg-gradient-to-br from-green-500 to-green-600 p-6 rounded-3xl shadow-xl text-white">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-xl font-bold">Панель курьера</h3>
          <span class="bg-white/20 px-3 py-1 rounded-full text-xs font-bold">Активен</span>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div class="bg-white/10 p-4 rounded-2xl backdrop-blur-sm">
             <p class="text-[10px] opacity-80 uppercase font-bold mb-1">Доступно заказов</p>
             <p class="text-2xl font-black">{{ availableOrdersCount }}</p>
          </div>
          <div @click="navigateTo('profile')" class="bg-white/10 p-4 rounded-2xl backdrop-blur-sm flex items-center justify-center cursor-pointer active:scale-95 transition">
             <p class="text-xs font-bold">Выключить</p>
          </div>
        </div>
        <button @click="navigateTo('courier_orders')" class="w-full mt-4 bg-white text-green-600 font-bold py-3 rounded-xl shadow-lg active:scale-[0.98] transition">
          Смотреть заказы рядом
        </button>
      </div>

      <!-- Shops Section -->
      <div v-if="!authStore.isCourierMode" @click="navigateTo('shops')" class="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-[0_10px_30px_-10px_rgba(0,0,0,0.1)] dark:shadow-black/50 flex items-center gap-6 cursor-pointer active:scale-[0.98] transition-transform border border-gray-100 dark:border-gray-700">
        <div class="w-16 h-16 bg-blue-100 dark:bg-blue-900/50 text-blue-600 dark:text-blue-400 rounded-2xl flex items-center justify-center text-3xl shadow-sm">
          <i class="fas fa-shopping-bag"></i>
        </div>
        <div>
          <h3 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Из магазинов</h3>
          <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">Еда, продукты, лекарства</p>
        </div>
        <div class="ml-auto text-gray-300 dark:text-gray-600">
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>

      <!-- Courier Section -->
      <div v-if="!authStore.isCourierMode" @click="navigateTo('courier')" class="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-[0_10px_30px_-10px_rgba(0,0,0,0.1)] dark:shadow-black/50 flex items-center gap-6 cursor-pointer active:scale-[0.98] transition-transform border border-gray-100 dark:border-gray-700">
        <div class="w-16 h-16 bg-yellow-100 dark:bg-yellow-900/50 text-yellow-600 dark:text-yellow-500 rounded-2xl flex items-center justify-center text-3xl shadow-sm">
          <i class="fas fa-motorcycle"></i>
        </div>
        <div>
          <h3 class="text-xl font-bold font-heading text-gray-900 dark:text-white">От двери до двери</h3>
          <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">Вызвать курьера</p>
        </div>
        <div class="ml-auto text-gray-300 dark:text-gray-600">
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>

      <!-- Intercity Section (Intercity) -->
      <div v-if="!authStore.isCourierMode" @click="navigateTo('intercity')" class="bg-white dark:bg-gray-800 p-6 rounded-3xl shadow-[0_10px_30px_-10px_rgba(0,0,0,0.1)] dark:shadow-black/50 flex items-center gap-6 cursor-pointer active:scale-[0.98] transition-transform border border-gray-100 dark:border-gray-700">
        <div class="w-16 h-16 bg-green-100 dark:bg-green-900/50 text-green-600 dark:text-green-500 rounded-2xl flex items-center justify-center text-3xl shadow-sm">
          <i class="fas fa-truck-moving"></i>
        </div>
        <div>
          <h3 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Межгород P2P</h3>
          <p class="text-gray-500 dark:text-gray-400 text-sm mt-1">Передать посылку с попутчиком</p>
        </div>
        <div class="ml-auto text-gray-300 dark:text-gray-600">
          <i class="fas fa-chevron-right"></i>
        </div>
      </div>
    </div>
  </div>
</template>
