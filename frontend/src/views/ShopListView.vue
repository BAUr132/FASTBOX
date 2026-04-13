<script setup>
import { ref, onMounted } from 'vue';
import api from '../api/axios';
import logo from '../assets/logo.png';

const emit = defineEmits(['navigate', 'selectShop']);

const shops = ref([]);
const categories = ref([]);
const currentCategoryId = ref('all');
const loading = ref(true);

const fetchShops = async () => {
  loading.value = true;
  try {
    const params = {};
    if (currentCategoryId.value && currentCategoryId.value !== 'all') {
      params.category_id = currentCategoryId.value;
    }
    const response = await api.get('/shops', { params });
    shops.value = response.data;
  } catch (error) {
    console.error('Failed to fetch shops:', error);
  } finally {
    loading.value = false;
  }
};

const fetchCategories = async () => {
  try {
    const response = await api.get('/categories');
    categories.value = response.data;
  } catch (error) {
    console.error('Failed to fetch categories:', error);
  }
};

const filterShops = (catId) => {
  currentCategoryId.value = catId;
  fetchShops();
};

const openShop = (shop) => {
  emit('selectShop', shop);
  emit('navigate', 'menu');
};

const getShopColor = (shop) => {
  const categoryName = shop.category?.name?.toLowerCase() || '';
  if (categoryName.includes('бургер')) return 'from-orange-400 to-red-500';
  if (categoryName.includes('суши')) return 'from-red-400 to-pink-500';
  if (categoryName.includes('аптека')) return 'from-green-400 to-teal-500';
  if (categoryName.includes('продукт')) return 'from-blue-400 to-indigo-500';
  if (categoryName.includes('магазин') || categoryName.includes('цум')) return 'from-purple-400 to-indigo-600';
  return 'from-blue-400 to-blue-600';
};

onMounted(() => {
  fetchCategories();
  fetchShops();
});
</script>

<template>
  <div id="screen-shops" class="screen screen-fade-in bg-gray-50 dark:bg-gray-900 min-h-screen pb-10 transition-colors duration-300">
    <header class="sticky top-0 bg-white/80 dark:bg-gray-800/80 backdrop-blur-md z-30 pt-4 px-4 pb-4 shadow-sm border-b border-gray-100 dark:border-gray-700 transition-colors duration-300">
      <div class="flex items-center justify-between mb-4">
        <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
          <i class="fas fa-arrow-left"></i>
        </button>
        <div class="text-center">
          <p class="text-[10px] text-gray-400 font-black uppercase tracking-widest mb-0.5">Доставка на</p>
          <div class="flex items-center justify-center gap-1 font-heading font-black text-sm text-gray-900 dark:text-white cursor-pointer">
            <span>пр. Абая, 34</span>
            <i class="fas fa-chevron-down text-[10px] text-blue-600 dark:text-blue-400"></i>
          </div>
        </div>
        <button class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300">
          <i class="fas fa-search"></i>
        </button>
      </div>

      <div class="flex space-x-2 overflow-x-auto no-scrollbar py-1">
        <button @click="filterShops('all')" 
                :class="currentCategoryId === 'all' ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" 
                class="px-5 py-2 rounded-2xl text-xs font-black font-heading whitespace-nowrap transition-all active:scale-95">
          Все
        </button>
        <button v-for="cat in categories" :key="cat.id" 
                @click="filterShops(cat.id)" 
                :class="currentCategoryId === cat.id ? 'bg-blue-600 text-white shadow-lg shadow-blue-500/30' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'" 
                class="px-5 py-2 rounded-2xl text-xs font-black font-heading whitespace-nowrap transition-all active:scale-95">
          {{ cat.name }}
        </button>
      </div>
    </header>
    
    <div class="p-6">
      <div v-if="loading" class="space-y-8">
         <div v-for="n in 3" :key="n" class="animate-pulse">
            <div class="h-44 bg-gray-200 dark:bg-gray-800 rounded-[2.5rem] mb-4"></div>
            <div class="px-2">
              <div class="h-6 bg-gray-200 dark:bg-gray-800 rounded-xl w-1/2 mb-2"></div>
              <div class="h-4 bg-gray-200 dark:bg-gray-800 rounded-lg w-3/4"></div>
            </div>
         </div>
      </div>

      <div v-else v-for="shop in shops" :key="shop.id" @click="openShop(shop)" class="group mb-8 cursor-pointer active:scale-[0.98] transition-all">
        <div class="relative h-44 rounded-[2.5rem] overflow-hidden shadow-xl dark:shadow-black/40 mb-4 border border-white/20 dark:border-gray-700/50">
          <div :class="['absolute inset-0 bg-gradient-to-br', getShopColor(shop)]" class="flex items-center justify-center text-white text-7xl opacity-90 transition-transform group-hover:scale-110 duration-500">
            <i :class="['fas', shop.category?.icon || 'fa-store']" class="drop-shadow-2xl"></i>
          </div>
          <div class="absolute bottom-4 left-4 right-4 flex justify-between items-end">
            <div class="bg-black/20 backdrop-blur-md px-3 py-1.5 rounded-xl text-[10px] font-black text-white border border-white/10">
              <i class="fas fa-map-marker-alt mr-1 text-blue-400"></i> {{ shop.address }}
            </div>
            <div class="bg-white dark:bg-gray-800 px-3 py-1.5 rounded-xl text-xs font-black text-gray-900 dark:text-white shadow-lg border border-gray-100 dark:border-gray-700">
              ⭐ 4.8
            </div>
          </div>
        </div>
        <div class="px-4">
          <h4 class="text-xl font-black text-gray-900 dark:text-white mb-1 tracking-tight">{{ shop.name }}</h4>
          <p class="text-gray-500 dark:text-gray-400 text-xs font-medium">{{ shop.description }}</p>
        </div>
      </div>
    </div>
  </div>
</template>
