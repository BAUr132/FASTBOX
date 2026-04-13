<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '../store/useAuth';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const authStore = useAuthStore();
const orders = ref([]);
const loading = ref(false);

const fetchMyCourierOrders = async () => {
  loading.value = true;
  try {
    const response = await api.get('/orders');
    const all = Array.isArray(response.data) ? response.data : Object.values(response.data);
    // Берем только те, где я — курьер и которые в работе
    orders.value = all.filter(o => o.courier_id === authStore.user?.id && o.status !== 'completed');
  } catch (error) {
    console.warn('Failed to fetch courier orders:', error);
  } finally {
    loading.value = false;
  }
};

const completeOrder = async (orderId) => {
  try {
    await api.post(`/orders/${orderId}/complete`);
    window.Telegram?.WebApp?.showAlert('✅ Доставка успешно завершена!');
    fetchMyCourierOrders();
  } catch (error) {
    console.error(error);
  }
};

onMounted(() => {
  fetchMyCourierOrders();
});

const getStatusLabel = (status) => {
  const map = { 'accepted': 'Принят вами', 'delivering': 'В пути (доставка)' };
  return map[status] || status;
};
</script>

<template>
  <div class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-green-600 p-4 shadow-lg flex items-center gap-4 sticky top-0 z-30 text-white">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold text-white">Кабинет Курьера</h2>
    </header>

    <div class="p-6 space-y-6">
      <!-- Courier Stats Card -->
      <div class="bg-gradient-to-br from-green-500 to-green-700 rounded-3xl p-6 text-white shadow-xl">
        <div class="flex items-center gap-4 mb-4">
           <div class="w-14 h-14 bg-white/20 rounded-full flex items-center justify-center text-2xl font-bold">
             {{ authStore.user?.name?.[0] }}
           </div>
           <div>
             <p class="text-sm opacity-80 uppercase font-bold">Ваш статус</p>
             <h3 class="text-xl font-black">Курьер: Активен ✅</h3>
           </div>
        </div>
        <button @click="authStore.toggleCourierMode(); emit('navigate', 'profile')" class="w-full bg-white text-green-700 font-bold py-3 rounded-xl active:scale-95 transition">
           Выйти из режима курьера
        </button>
      </div>

      <div class="space-y-4">
        <h3 class="text-lg font-bold px-1 text-gray-900 dark:text-white">Мои доставки</h3>
        
        <div v-if="loading" class="text-center py-10 opacity-50">
           <i class="fas fa-circle-notch animate-spin text-2xl text-green-600"></i>
        </div>
        
        <div v-else-if="orders.length === 0" class="bg-white dark:bg-gray-800 rounded-3xl p-10 text-center border border-dashed border-gray-200 dark:border-gray-700">
           <p class="text-gray-500 dark:text-gray-400 text-sm">У вас пока нет активных доставок</p>
           <button @click="emit('navigate', 'courier_orders')" class="mt-4 text-green-600 font-bold">Найти заказы рядом ➜</button>
        </div>

        <div v-else v-for="order in orders" :key="order.id" class="bg-white dark:bg-gray-800 p-5 rounded-3xl shadow-sm border border-green-100 dark:border-green-900">
           <div class="flex justify-between items-start mb-3">
             <span class="font-black text-gray-900 dark:text-white">Заказ №{{ order.id }}</span>
             <span class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-[10px] font-black uppercase">
               {{ getStatusLabel(order.status) }}
             </span>
           </div>

           <div class="space-y-1 mb-4">
              <p class="text-[11px] text-gray-500"><i class="fas fa-map-marker-alt mr-1"></i> {{ order.pickup_address }}</p>
              <p class="text-[11px] text-gray-500"><i class="fas fa-flag-checkered mr-1"></i> {{ order.delivery_address }}</p>
           </div>

           <div class="pt-3 border-t dark:border-gray-700">
              <div v-if="order.status === 'accepted'" class="text-[10px] text-amber-600 font-bold text-center bg-amber-50 p-2 rounded-lg border border-amber-200 mb-2">
                 Ожидание подтверждения от клиента (QR)
              </div>
              <button v-if="order.status === 'delivering'" 
                      @click="completeOrder(order.id)"
                      class="w-full bg-green-600 text-white font-black py-4 rounded-xl shadow-lg active:scale-95 transition">
                 ЗАВЕРШИТЬ ДОСТАВКУ
              </button>
              <div class="flex justify-between items-center mt-2">
                 <span class="text-[10px] text-gray-400">Доход за заказ:</span>
                 <span class="font-black text-green-600">{{ order.delivery_fee }} ₸</span>
              </div>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>