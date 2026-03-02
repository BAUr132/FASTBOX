<script setup>
import { ref, onMounted } from 'vue';
import HomeView from './views/HomeView.vue';
import CourierView from './views/CourierView.vue';
import ShopListView from './views/ShopListView.vue';
import MenuView from './views/MenuView.vue';
import CartView from './views/CartView.vue';

const currentScreen = ref('main');
const selectedShop = ref(null);

const handleNavigation = (screen) => {
  currentScreen.value = screen;
  window.scrollTo(0, 0);
};

const handleSelectShop = (shop) => {
  selectedShop.value = shop;
};

onMounted(() => {
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    document.documentElement.classList.toggle('dark', tg.colorScheme === 'dark');
  }
});
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 overflow-x-hidden transition-colors duration-300">
    <transition name="fade" mode="out-in">
      <div v-if="currentScreen === 'main'" key="main">
        <HomeView @navigate="handleNavigation" />
      </div>
      
      <div v-else-if="currentScreen === 'shops'" key="shops">
        <ShopListView @navigate="handleNavigation" @selectShop="handleSelectShop" />
      </div>

      <div v-else-if="currentScreen === 'menu'" key="menu">
        <MenuView :shop="selectedShop" @navigate="handleNavigation" />
      </div>

      <div v-else-if="currentScreen === 'cart'" key="cart">
        <CartView @navigate="handleNavigation" />
      </div>

      <div v-else-if="currentScreen === 'courier'" key="courier">
        <CourierView @navigate="handleNavigation" />
      </div>

      <div v-else-if="currentScreen === 'intercity'" key="intercity" class="p-6 text-center">
        <button @click="handleNavigation('main')" class="bg-gray-200 dark:bg-gray-700 p-2 rounded mb-4">Назад</button>
        <h2 class="text-2xl font-bold">Экран межгорода (Скоро)</h2>
      </div>
    </transition>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.screen-fade-in {
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
</style>
