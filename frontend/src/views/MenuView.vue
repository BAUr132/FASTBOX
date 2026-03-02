<script setup>
import { ref, computed, onMounted } from 'vue';
import { useCartStore } from '../store/useCart';

const props = defineProps(['shop']);
const emit = defineEmits(['navigate']);
const cartStore = useCartStore();

const allItems = {
  'burger_house': [
    { id: 'b1', name: 'Чизбургер Классик', desc: 'Котлета из говядины, сыр чеддер, соус', price: 1500, img: '🍔' },
    { id: 'b2', name: 'Двойной Смэш Бургер', desc: 'Две котлеты, бекон, халапеньо', price: 2200, img: '🍔' },
    { id: 'b3', name: 'Картофель Фри', desc: 'Хрустящая картошка, стандартная порция', price: 800, img: '🍟' }
  ],
  'sushi_master': [
    { id: 'sm1', name: 'Ролл Филадельфия', desc: 'Лосось, сливочный сыр, огурец', price: 2500, img: '🍣' },
    { id: 'sm2', name: 'Ролл Калифорния', desc: 'Краб, авокадо, тобико', price: 2200, img: '🍱' }
  ],
  'pharmacy_plus': [
    { id: 'p1', name: 'Парацетамол 500мг', desc: 'Жаропонижающее, 10 таблеток', price: 350, img: '💊' },
    { id: 'p4', name: 'ТераФлю', desc: 'Порошок от простуды, 4 пакетика', price: 2800, img: '☕' }
  ],
  'supermarket': [
    { id: 's1', name: 'Хлеб белый нарезной', desc: 'Свежая выпечка', price: 200, img: '🍞' },
    { id: 's2', name: 'Молоко 3.2%', desc: 'Домашнее, 1 литр', price: 650, img: '🥛' }
  ]
};

const menuItems = computed(() => {
  return props.shop ? (allItems[props.shop.id] || []) : [];
});

const getItemQty = (id) => {
  const item = cartStore.items.find(i => i.id === id);
  return item ? item.qty : 0;
};
</script>

<template>
  <div id="screen-menu" class="screen screen-fade-in bg-gray-50 dark:bg-gray-900 min-h-screen pb-24">
    <header class="sticky top-0 bg-white dark:bg-gray-800 z-30 pt-4 px-4 pb-4 shadow-sm border-b dark:border-gray-700 transition-colors duration-300">
      <div class="flex items-center gap-4">
        <button @click="emit('navigate', 'shops')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <h2 class="text-lg font-bold font-heading text-gray-900 dark:text-white">{{ shop?.name || 'Меню' }}</h2>
      </div>
    </header>

    <div class="p-4 space-y-4">
      <div v-for="item in menuItems" :key="item.id" class="bg-white dark:bg-gray-800 p-4 rounded-2xl flex gap-4 border border-gray-100 dark:border-gray-700 shadow-sm">
        <div class="text-4xl flex items-center justify-center w-16 h-16 bg-gray-50 dark:bg-gray-700 rounded-xl">
          {{ item.img }}
        </div>
        <div class="flex-grow">
          <h4 class="font-bold text-gray-900 dark:text-white">{{ item.name }}</h4>
          <p class="text-xs text-gray-500 dark:text-gray-400 mt-1">{{ item.desc }}</p>
          <div class="flex justify-between items-center mt-3">
            <span class="font-bold text-blue-600 dark:text-blue-400">{{ item.price }} ₸</span>
            
            <div v-if="getItemQty(item.id) > 0" class="flex items-center gap-3 bg-blue-600 text-white rounded-full px-3 py-1">
              <button @click="cartStore.updateQty(item.id, -1)" class="w-6 h-6 flex items-center justify-center font-bold">-</button>
              <span class="font-bold text-sm">{{ getItemQty(item.id) }}</span>
              <button @click="cartStore.updateQty(item.id, 1)" class="w-6 h-6 flex items-center justify-center font-bold">+</button>
            </div>
            <button v-else @click="cartStore.addToCart(item)" class="bg-blue-600 text-white w-10 h-10 rounded-full flex items-center justify-center shadow-md shadow-blue-500/20 active:scale-90 transition-transform">
              <i class="fas fa-plus"></i>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Floating Cart Button -->
    <div v-if="cartStore.cartCount > 0" @click="emit('navigate', 'cart')" class="fixed bottom-6 inset-x-6 z-50 cursor-pointer active:scale-95 transition-transform">
      <div class="bg-blue-600 dark:bg-blue-700 text-white rounded-2xl p-4 shadow-2xl flex justify-between items-center border border-blue-500">
        <div class="flex items-center gap-3">
          <div class="bg-white text-blue-600 w-8 h-8 rounded-full flex items-center justify-center font-bold text-sm">{{ cartStore.cartCount }}</div>
          <span class="font-bold">Корзина</span>
        </div>
        <div class="font-bold text-lg">{{ cartStore.subtotal }} ₸</div>
      </div>
    </div>
  </div>
</template>
