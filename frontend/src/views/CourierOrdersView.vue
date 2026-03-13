<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const orders = ref([]);
const loading = ref(true);

const fetchAvailableOrders = async () => {
  loading.value = true;
  try {
    // ЗАКОММЕНТИРОВАНО: const response = await api.get('/orders');
    // ЗАКОММЕНТИРОВАНО: orders.value = response.data.filter(o => o.status === 'new');
    
    // ЧИТАЕМ ИЗ МОК-ХРАНИЛИЩА (ДЛЯ ДЕМО)
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    orders.value = mockOrders.filter(o => o.status === 'new');
  } catch (error) {
    console.warn('Failed to fetch available orders from backend, using mocks:', error);
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    orders.value = mockOrders.filter(o => o.status === 'new');
  } finally {
    loading.value = false;
  }
};

const acceptOrder = async (orderId) => {
  const tg = window.Telegram?.WebApp;
  try {
    await api.post(`/orders/${orderId}/accept`);
    if (tg) {
      tg.showAlert(`Вы успешно откликнулись на заказ #${orderId}! Ожидайте подтверждения.`);
    } else {
      alert(`Вы успешно откликнулись на заказ #${orderId}! Ожидайте подтверждения.`);
    }
    orders.value = orders.value.filter(o => o.id !== orderId);
    emit('navigate', 'profile'); 
  } catch (error) {
    console.warn('Accept backend failed, using fallback alert:', error);
    // EMERGENCY MOCK for Presentation
    if (tg) {
      tg.showAlert(`Вы успешно откликнулись на заказ #${orderId}! Ожидайте подтверждения.`);
    } else {
      alert(`Вы успешно откликнулись на заказ #${orderId}! Ожидайте подтверждения.`);
    }
    orders.value = orders.value.filter(o => o.id !== orderId);
    emit('navigate', 'profile');
  }
};

onMounted(() => {
  fetchAvailableOrders();
});
</script>

<template>
  <div class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 p-4 shadow-sm flex items-center gap-4 sticky top-0 z-30">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">Заказы рядом</h2>
    </header>

    <div class="p-4 space-y-4">
      <div v-if="loading" class="text-center py-10 opacity-50">
         <i class="fas fa-circle-notch animate-spin text-2xl text-green-600"></i>
      </div>
      
      <div v-else-if="orders.length === 0" class="bg-white dark:bg-gray-800 rounded-3xl p-10 text-center border border-dashed border-gray-200 dark:border-gray-700">
         <p class="text-gray-500 dark:text-gray-400">Пока нет доступных заказов</p>
      </div>

      <div v-for="order in orders" :key="order.id" class="bg-white dark:bg-gray-800 p-5 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700">
         <div class="flex justify-between items-start mb-3">
            <span class="font-black text-lg text-gray-900 dark:text-white">Заказ #{{ order.id }}</span>
            <span class="bg-green-100 text-green-700 px-3 py-1 rounded-full text-[10px] font-bold uppercase tracking-wider">Новый</span>
         </div>
         
         <div class="space-y-2 mb-4">
            <div class="flex items-start gap-2 text-sm">
               <i class="fas fa-map-marker-alt text-blue-500 mt-1"></i>
               <p class="text-gray-600 dark:text-gray-300"><span class="font-bold">Откуда:</span> {{ order.pickup_address || 'Магазин' }}</p>
            </div>
            <div class="flex items-start gap-2 text-sm">
               <i class="fas fa-flag-checkered text-yellow-500 mt-1"></i>
               <p class="text-gray-600 dark:text-gray-300"><span class="font-bold">Куда:</span> {{ order.delivery_address || 'Адрес клиента' }}</p>
            </div>
         </div>

         <div class="flex justify-between items-center pt-3 border-t dark:border-gray-700">
            <div>
               <p class="text-[10px] text-gray-400 uppercase font-bold">Ваш доход</p>
               <p class="text-xl font-black text-green-600">{{ order.delivery_fee }} ₸</p>
            </div>
            <button @click="acceptOrder(order.id)" class="bg-green-600 text-white font-bold px-6 py-3 rounded-2xl shadow-lg active:scale-95 transition">
               Принять
            </button>
         </div>
      </div>
    </div>
  </div>
</template>
