<script setup>
import { ref, onMounted } from 'vue';
import { useAuthStore } from '../store/useAuth';
import { useCartStore } from '../store/useCart';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const authStore = useAuthStore();
const cartStore = useCartStore();
const orders = ref([]);
const loading = ref(false);
const isUploading = ref(false);

const fetchOrders = async () => {
  loading.value = true;
  try {
    const response = await api.get('/orders');
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    // Объединяем реальные и моки для истории
    orders.value = [...mockOrders.reverse(), ...response.data];
  } catch (error) {
    console.warn('Failed to fetch orders, using mocks:', error);
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    orders.value = mockOrders.reverse();
  } finally {
    loading.value = false;
  }
};

const completeOrder = async (orderId) => {
  const tg = window.Telegram?.WebApp;
  try {
    // ЗАКОММЕНТИРОВАНО: await api.post(`/orders/${orderId}/complete`);
    
    // Мокаем завершение в localStorage
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    const order = mockOrders.find(o => o.id === orderId);
    if (order) order.status = 'completed';
    localStorage.setItem('fb_mock_orders', JSON.stringify(mockOrders));

    if (tg) tg.showAlert('Заказ успешно завершен!');
    else alert('Заказ завершен!');
    fetchOrders(); 
  } catch (error) {
    console.warn('Complete backend failed, using mock:', error);
    const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
    const order = mockOrders.find(o => o.id === orderId);
    if (order) order.status = 'completed';
    localStorage.setItem('fb_mock_orders', JSON.stringify(mockOrders));
    
    if (tg) tg.showAlert('Заказ успешно завершен!');
    fetchOrders();
  }
};

const simulateKYCUpload = async () => {
  isUploading.value = true;
  const tg = window.Telegram?.WebApp;
  
  // MOCK VERIFICATION for Presentation
  setTimeout(() => {
    authStore.user.kyc_status = 'verified';
    localStorage.setItem('fb_user', JSON.stringify(authStore.user));
    
    if (tg) {
      tg.showAlert('Успешно верифицировано!');
    } else {
      alert('Успешно верифицировано!');
    }
    isUploading.value = false;
  }, 1000);
};

onMounted(() => {
  fetchOrders();
});

const getStatusLabel = (status) => {
  const map = {
    'new': 'Новый',
    'accepted': 'В пути',
    'delivering': 'Доставка',
    'completed': 'Выполнен',
    'cancelled': 'Отменен'
  };
  return map[status] || status;
};

const getStatusClass = (status) => {
  switch(status) {
    case 'new': return 'bg-blue-100 text-blue-700';
    case 'accepted': return 'bg-amber-100 text-amber-700';
    case 'completed': return 'bg-green-100 text-green-700';
    case 'cancelled': return 'bg-red-100 text-red-700';
    default: return 'bg-gray-100 text-gray-700';
  }
};
</script>

<template>
  <div class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 p-4 shadow-sm flex items-center gap-4 sticky top-0 z-30 transition-colors duration-300">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold text-gray-900 dark:text-white">Личный кабинет</h2>
    </header>

    <div class="p-6 space-y-6">
      <!-- User Info -->
      <div class="bg-white dark:bg-gray-800 rounded-3xl p-6 shadow-sm border border-gray-100 dark:border-gray-700 flex items-center gap-4 transition-colors duration-300">
        <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center text-white text-2xl font-bold shadow-lg shadow-blue-500/20">
          {{ authStore.user?.name?.[0] || 'U' }}
        </div>
        <div>
          <h3 class="text-xl font-bold text-gray-900 dark:text-white">{{ authStore.user?.name || 'Гость' }}</h3>
          <p class="text-sm font-medium" :class="authStore.user?.kyc_status === 'verified' ? 'text-green-500' : 'text-amber-500'">
            {{ authStore.user?.kyc_status === 'verified' ? 'Верифицирован ✅' : 'Требуется проверка ⚠️' }}
          </p>
        </div>
      </div>

      <!-- KYC Upload Section -->
      <div v-if="authStore.user?.kyc_status !== 'verified'" class="bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800 rounded-3xl p-6 transition-colors duration-300">
         <h4 class="font-bold text-blue-800 dark:text-blue-300 mb-2">Верификация личности</h4>
         <p class="text-xs text-blue-600 dark:text-blue-400 mb-4">Для доступа к услугам вызова курьера и межгорода (P2P) необходимо загрузить удостоверение личности.</p>
         
         <button @click="simulateKYCUpload" :disabled="isUploading" class="w-full bg-blue-600 text-white font-bold py-3 rounded-2xl shadow-lg active:scale-95 transition-all flex items-center justify-center gap-2">
           <i v-if="isUploading" class="fas fa-spinner animate-spin"></i>
           <i v-else class="fas fa-upload"></i>
           <span>{{ isUploading ? 'Загрузка...' : 'Загрузить паспорт' }}</span>
         </button>
      </div>

      <!-- Quick Actions -->
      <div class="grid grid-cols-2 gap-4">
         <button @click="authStore.toggleCourierMode" :class="authStore.isCourierMode ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-400 border-green-200 dark:border-green-800' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 border-transparent'" class="p-4 rounded-2xl border flex flex-col items-center gap-2 font-bold transition">
           <i class="fas fa-motorcycle text-xl"></i>
           <span class="text-xs">{{ authStore.isCourierMode ? 'Режим Курьера: ВКЛ' : 'Стать Курьером' }}</span>
         </button>
         <button v-if="!authStore.isTelegram" @click="authStore.logout(); emit('navigate', 'main')" class="p-4 rounded-2xl bg-red-50 dark:bg-red-900/20 text-red-600 dark:text-red-400 border border-red-100 dark:border-red-800 flex flex-col items-center gap-2 font-bold transition">
           <i class="fas fa-sign-out-alt text-xl"></i>
           <span class="text-xs">Выйти</span>
         </button>
      </div>

      <!-- Orders List -->
      <div class="space-y-4">
        <h3 class="text-lg font-bold px-1 text-gray-900 dark:text-white">История и Доставки</h3>
        
        <div v-if="loading" class="text-center py-10 opacity-50 flex flex-col items-center gap-2">
           <i class="fas fa-circle-notch animate-spin text-2xl text-blue-600"></i>
        </div>
        
        <div v-else-if="orders.length === 0" class="bg-white dark:bg-gray-800 rounded-3xl p-10 text-center border border-dashed border-gray-200 dark:border-gray-700">
           <p class="text-gray-500 dark:text-gray-400 text-sm">Здесь пока ничего нет</p>
        </div>

        <div v-else v-for="order in orders" :key="order.id" class="bg-white dark:bg-gray-800 p-5 rounded-3xl shadow-sm border border-gray-100 dark:border-gray-700">
           <div class="flex justify-between items-start mb-3">
             <div>
                <span class="font-black text-gray-900 dark:text-white">№{{ order.id }}</span>
                <p class="text-[10px] text-gray-400 uppercase font-black">{{ order.type === 'shop' ? 'Магазин' : (order.type === 'intercity' ? 'Межгород' : 'Курьер') }}</p>
             </div>
             <span class="px-3 py-1 rounded-full text-[10px] font-black uppercase" :class="getStatusClass(order.status)">
               {{ getStatusLabel(order.status) }}
             </span>
           </div>

           <div v-if="order.pickup_address || order.delivery_address" class="space-y-1 mb-4">
              <p v-if="order.pickup_address" class="text-[11px] text-gray-500 truncate"><i class="fas fa-map-marker-alt mr-1"></i> {{ order.pickup_address }}</p>
              <p v-if="order.delivery_address" class="text-[11px] text-gray-500 truncate"><i class="fas fa-flag-checkered mr-1"></i> {{ order.delivery_address }}</p>
           </div>

           <div class="flex justify-between items-center pt-3 border-t dark:border-gray-700">
              <span class="font-black text-blue-600 dark:text-blue-400">{{ order.total_price || order.delivery_fee }} ₸</span>
              
              <!-- Action for Courier -->
              <button v-if="order.status === 'accepted' && authStore.user && order.courier_id === authStore.user.id" 
                      @click="completeOrder(order.id)"
                      class="bg-green-600 text-white text-[10px] font-black uppercase px-4 py-2 rounded-xl active:scale-95 transition">
                 Завершить
              </button>
           </div>
        </div>
      </div>
    </div>
  </div>
</template>
