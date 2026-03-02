<script setup>
import { useCartStore } from '../store/useCart';

const emit = defineEmits(['navigate']);
const cartStore = useCartStore();

const checkout = () => {
  if (cartStore.items.length > 0) {
    alert('Заказ оформлен! Сумма: ' + cartStore.total + ' ₸');
    cartStore.clearCart();
    emit('navigate', 'main');
  }
};
</script>

<template>
  <div id="screen-cart" class="screen screen-fade-in bg-gray-50 dark:bg-gray-900 min-h-screen">
    <header class="sticky top-0 bg-white dark:bg-gray-800 z-30 pt-4 px-4 pb-4 shadow-sm border-b dark:border-gray-700 transition-colors duration-300">
      <div class="flex items-center gap-4">
        <button @click="emit('navigate', 'menu')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Корзина</h2>
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
        <div class="space-y-3 mb-6">
          <div v-for="item in cartStore.items" :key="item.id" class="bg-white dark:bg-gray-800 p-4 rounded-xl flex justify-between items-center shadow-sm border border-gray-100 dark:border-gray-700">
            <div class="flex gap-3 items-center">
               <div class="text-2xl">{{ item.img }}</div>
               <div>
                 <h4 class="font-bold text-sm text-gray-900 dark:text-white">{{ item.name }}</h4>
                 <p class="text-xs text-gray-500">{{ item.price }} ₸</p>
               </div>
            </div>
            <div class="flex items-center gap-3">
              <button @click="cartStore.updateQty(item.id, -1)" class="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-blue-600 font-bold">-</button>
              <span class="font-bold text-gray-900 dark:text-white">{{ item.qty }}</span>
              <button @click="cartStore.updateQty(item.id, 1)" class="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-blue-600 font-bold">+</button>
            </div>
          </div>
        </div>
        
        <div class="bg-white dark:bg-gray-800 rounded-2xl p-4 shadow-sm border border-gray-100 dark:border-gray-700 mb-6">
          <div class="flex justify-between text-gray-500 dark:text-gray-400 mb-2">
            <span>Товары:</span>
            <span>{{ cartStore.subtotal }} ₸</span>
          </div>
          <div class="flex justify-between text-gray-500 dark:text-gray-400 mb-4">
            <span>Доставка (FastBox):</span>
            <span>{{ cartStore.deliveryFee }} ₸</span>
          </div>
          <div class="flex justify-between text-xl font-bold text-gray-900 dark:text-white border-t dark:border-gray-700 pt-4">
            <span>Итого:</span>
            <span class="text-blue-600">{{ cartStore.total }} ₸</span>
          </div>
        </div>

        <button @click="checkout" class="w-full bg-blue-600 text-white font-bold font-heading text-lg py-4 rounded-2xl shadow-lg hover:bg-blue-700 transition active:scale-[0.98]">
          Оформить заказ
        </button>
      </div>
    </div>
  </div>
</template>
