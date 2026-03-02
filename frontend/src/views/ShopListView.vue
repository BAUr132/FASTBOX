<script setup>
import { ref, onMounted } from 'vue';

const emit = defineEmits(['navigate', 'selectShop']);

const shops = ref([
  { id: 'burger_house', name: 'Burger House', address: 'ул. Тауелсиздик, 12', type: 'Фастфуд • Бургеры', category: 'burgers', rating: '4.8', icon: 'fa-hamburger', color: 'from-orange-400 to-red-500' },
  { id: 'sushi_master', name: 'Суши Мастер', address: 'пр. Абая, 45', type: 'Японская кухня • Роллы', category: 'sushi', rating: '4.6', icon: 'fa-fish', color: 'from-red-400 to-pink-500' },
  { id: 'pharmacy_plus', name: 'Аптека "Здоровье"', address: 'ул. Каирбекова, 67', type: 'Медикаменты • Витамины', category: 'pharmacy', rating: '4.9', icon: 'fa-pills', color: 'from-green-400 to-teal-500' },
  { id: 'supermarket', name: 'ТД ЦУМ (Продукты)', address: 'ул. Аль-Фараби, 65', type: 'Продукты • Напитки', category: 'groceries', rating: '4.7', icon: 'fa-shopping-cart', color: 'from-blue-400 to-indigo-500' }
]);

const currentCategory = ref('all');
const filteredShops = ref([]);

const filterShops = (category) => {
  currentCategory.value = category;
  if (category === 'all') {
    filteredShops.value = shops.value;
  } else {
    filteredShops.value = shops.value.filter(s => s.category === category);
  }
};

const openShop = (shop) => {
  emit('selectShop', shop);
  emit('navigate', 'menu');
};

onMounted(() => {
  filterShops('all');
});
</script>

<template>
  <div id="screen-shops" class="screen screen-fade-in bg-white dark:bg-gray-900 min-h-screen">
    <header class="sticky top-0 bg-white dark:bg-gray-800 z-30 pt-4 px-4 pb-2 shadow-sm border-b border-transparent dark:border-gray-700 transition-colors duration-300">
      <div class="flex items-center justify-between mb-4">
        <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="text-center">
          <p class="text-xs text-gray-400 font-bold uppercase tracking-wider">Доставка на</p>
          <div class="flex items-center justify-center gap-1 font-heading font-bold text-gray-900 dark:text-white cursor-pointer">
            <span>пр. Абая, 34</span>
            <i class="fas fa-chevron-down text-xs text-blue-600 dark:text-blue-400"></i>
          </div>
        </div>
        <button class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300">
          <i class="fas fa-search"></i>
        </button>
      </div>

      <div class="flex space-x-2 overflow-x-auto no-scrollbar pb-2">
        <button @click="filterShops('all')" :class="currentCategory === 'all' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" class="px-6 py-2.5 rounded-full text-sm font-semibold font-heading shadow-md whitespace-nowrap transition-colors">Все</button>
        <button @click="filterShops('burgers')" :class="currentCategory === 'burgers' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" class="px-6 py-2.5 rounded-full text-sm font-semibold font-heading whitespace-nowrap transition-colors">🍔 Бургеры</button>
        <button @click="filterShops('sushi')" :class="currentCategory === 'sushi' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" class="px-6 py-2.5 rounded-full text-sm font-semibold font-heading whitespace-nowrap transition-colors">🍣 Суши</button>
        <button @click="filterShops('groceries')" :class="currentCategory === 'groceries' ? 'bg-blue-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" class="px-6 py-2.5 rounded-full text-sm font-semibold font-heading whitespace-nowrap transition-colors">🛒 Продукты</button>
      </div>
    </header>
    
    <div class="p-4">
      <div v-for="shop in filteredShops" :key="shop.id" @click="openShop(shop)" class="group mb-6 cursor-pointer active:scale-[0.98] transition-transform">
        <div class="relative h-48 rounded-3xl overflow-hidden shadow-lg mb-3">
          <div :class="['absolute inset-0 bg-gradient-to-br', shop.color]" class="flex items-center justify-center">
            <i :class="['fas', shop.icon]" class="text-white text-6xl opacity-80"></i>
          </div>
          <div class="absolute bottom-3 right-3 bg-white/90 dark:bg-gray-800/90 px-3 py-1.5 rounded-xl text-xs font-bold dark:text-white">
            <i class="fas fa-map-marker-alt text-blue-600"></i> {{ shop.address }}
          </div>
        </div>
        <div class="px-2 flex justify-between">
          <div>
            <h4 class="text-xl font-bold text-gray-900 dark:text-white">{{ shop.name }}</h4>
            <p class="text-gray-500 dark:text-gray-400 text-sm">{{ shop.type }}</p>
          </div>
          <div class="text-sm font-bold bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white h-fit px-2 py-1 rounded-lg">⭐ {{ shop.rating }}</div>
        </div>
      </div>
    </div>
  </div>
</template>
