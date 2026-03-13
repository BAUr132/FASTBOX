<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useCartStore } from '../store/useCart';

const emit = defineEmits(['navigate']);
const cartStore = useCartStore();
const paymentMethod = ref('card');
const isSubmitting = ref(false);

onMounted(() => {
  window.addEventListener('tg-main-button-click', checkout);
});

onUnmounted(() => {
  window.removeEventListener('tg-main-button-click', checkout);
});

const checkout = async () => {
  if (cartStore.items.length > 0 && !isSubmitting.value) {
    const tg = window.Telegram?.WebApp;
    isSubmitting.value = true;
    
    try {
      if (tg) tg.MainButton.showProgress();
      
      const result = await cartStore.checkout(paymentMethod.value);
      
      if (tg) {
        tg.MainButton.hideProgress();
        tg.showAlert('Заказ №' + result.order.id + ' успешно оформлен! Оплата: ' + (paymentMethod.value === 'card' ? 'Картой' : 'Наличными'));
      } else {
        alert('Заказ успешно оформлен! Способ оплаты: ' + (paymentMethod.value === 'card' ? 'Картой' : 'Наличными'));
      }
      
      emit('navigate', 'main');
    } catch (error) {
      if (tg) {
        tg.MainButton.hideProgress();
        tg.showAlert('Ошибка: ' + error.message);
      } else {
        alert('Ошибка: ' + error.message);
      }
    } finally {
      isSubmitting.value = false;
    }
  }
};
</script>

<template>
  <div id="screen-cart" class="screen screen-fade-in bg-gray-50 dark:bg-gray-900 min-h-screen pb-10">
    <header class="sticky top-0 bg-white dark:bg-gray-800 z-30 pt-4 px-4 pb-4 shadow-sm border-b dark:border-gray-700 transition-colors duration-300">
      <div class="flex items-center gap-4">
        <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Оформление</h2>
      </div>
    </header>

    <div class="p-4">
      <div v-if="cartStore.items.length === 0" class="text-center py-20">
        <div class="w-20 h-20 bg-gray-100 dark:bg-gray-800 rounded-full flex items-center justify-center text-3xl mx-auto mb-4 text-gray-400">
          <i class="fas fa-shopping-basket"></i>
        </div>
        <h3 class="text-lg font-bold text-gray-900 dark:text-white">Корзина пуста</h3>
        <p class="text-gray-500 dark:text-gray-400 mt-2">Добавьте что-нибудь из меню</p>
        <button @click="emit('navigate', 'shops')" class="mt-6 text-blue-600 font-bold">Перейти в магазины</button>
      </div>

      <div v-else>
        <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">Ваш заказ</h3>
        <div class="space-y-3 mb-6">
          <div v-for="item in cartStore.items" :key="item.id" class="bg-white dark:bg-gray-800 p-4 rounded-2xl flex justify-between items-center shadow-sm border border-gray-100 dark:border-gray-700">
            <div class="flex gap-3 items-center">
               <div class="text-2xl w-12 h-12 bg-gray-50 dark:bg-gray-700 rounded-xl flex items-center justify-center">{{ item.image || '📦' }}</div>
               <div>
                 <h4 class="font-bold text-sm text-gray-900 dark:text-white">{{ item.name }}</h4>
                 <p class="text-xs text-blue-600 font-bold">{{ Math.round(item.price) }} ₸</p>
               </div>
            </div>
            <div class="flex items-center gap-3 bg-gray-100 dark:bg-gray-700 px-3 py-1.5 rounded-full">
              <button @click="cartStore.updateQty(item.id, -1)" class="text-gray-500 hover:text-blue-600 font-bold px-1">
                <i class="fas fa-minus text-[10px]"></i>
              </button>
              <span class="font-bold text-sm min-w-[20px] text-center text-gray-900 dark:text-white">{{ item.qty }}</span>
              <button @click="cartStore.updateQty(item.id, 1)" class="text-gray-500 hover:text-blue-600 font-bold px-1">
                <i class="fas fa-plus text-[10px]"></i>
              </button>
            </div>
          </div>
        </div>

        <h3 class="text-sm font-bold text-gray-400 uppercase tracking-wider mb-3 px-1">Способ оплаты</h3>
        <div class="grid grid-cols-2 gap-3 mb-6">
           <button @click="paymentMethod = 'card'" :class="paymentMethod === 'card' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-500'" class="p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all active:scale-95">
             <i class="fas fa-credit-card text-xl"></i>
             <span class="text-xs font-bold">Картой</span>
           </button>
           <button @click="paymentMethod = 'cash'" :class="paymentMethod === 'cash' ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20 text-blue-600' : 'border-gray-100 dark:border-gray-700 bg-white dark:bg-gray-800 text-gray-500'" class="p-4 rounded-2xl border-2 flex flex-col items-center gap-2 transition-all active:scale-95">
             <i class="fas fa-money-bill-wave text-xl"></i>
             <span class="text-xs font-bold">Наличными</span>
           </button>
        </div>
        
        <div class="bg-white dark:bg-gray-800 rounded-3xl p-5 shadow-sm border border-gray-100 dark:border-gray-700 mb-6 space-y-3">
          <div class="flex justify-between text-sm text-gray-500 dark:text-gray-400">
            <span>Сумма:</span>
            <span class="font-bold text-gray-900 dark:text-white">{{ cartStore.subtotal }} ₸</span>
          </div>
          <div class="flex justify-between text-sm text-gray-500 dark:text-gray-400 pb-3 border-b dark:border-gray-700">
            <span>Доставка:</span>
            <span class="font-bold text-gray-900 dark:text-white">{{ cartStore.deliveryFee }} ₸</span>
          </div>
          <div class="flex justify-between text-lg font-black text-gray-900 dark:text-white pt-1">
            <span>К оплате:</span>
            <span class="text-blue-600">{{ cartStore.total }} ₸</span>
          </div>
        </div>

        <button @click="checkout" :disabled="isSubmitting" class="w-full bg-blue-600 text-white font-bold font-heading text-lg py-4 rounded-2xl shadow-xl shadow-blue-500/20 hover:bg-blue-700 transition active:scale-[0.98] flex items-center justify-center gap-3">
          <i v-if="isSubmitting" class="fas fa-spinner animate-spin"></i>
          <span>{{ isSubmitting ? 'Оформление...' : 'Заказать за ' + cartStore.total + ' ₸' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
