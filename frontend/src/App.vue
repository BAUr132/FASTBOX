<script setup>
import { ref, onMounted, watch } from 'vue';
import HomeView from './views/HomeView.vue';
import CourierView from './views/CourierView.vue';
import ShopListView from './views/ShopListView.vue';
import MenuView from './views/MenuView.vue';
import CartView from './views/CartView.vue';
import ProfileView from './views/ProfileView.vue';
import CourierProfileView from './views/CourierProfileView.vue';
import IntercityView from './views/IntercityView.vue';
import CourierOrdersView from './views/CourierOrdersView.vue';
import { useCartStore } from './store/useCart';
import { useAuthStore } from './store/useAuth';
import logo from './assets/logo.png';

const currentScreen = ref('main');
const selectedShop = ref(null);
const cartStore = useCartStore();
const authStore = useAuthStore();

const guestName = ref('');
const guestPhone = ref('');

const handleNavigation = (screen) => {
  currentScreen.value = screen;
  window.scrollTo(0, 0);
};

const handleSelectShop = (shop) => {
  selectedShop.value = shop;
};

const setupMainButton = () => {
  if (window.Telegram?.WebApp?.MainButton) {
    const tg = window.Telegram.WebApp;
    
    if (cartStore.cartCount > 0 && ['main', 'shops', 'menu'].includes(currentScreen.value)) {
      tg.MainButton.text = "Корзина (" + cartStore.cartCount + ")";
      tg.MainButton.show();
    } else if (currentScreen.value === 'cart') {
      tg.MainButton.text = "Оформить заказ";
      tg.MainButton.show();
    } else if (currentScreen.value === 'courier') {
      tg.MainButton.text = "Вызвать курьера";
      tg.MainButton.show();
    } else if (currentScreen.value === 'intercity') {
      tg.MainButton.text = "Оформить попутку";
      tg.MainButton.show();
    } else {
      tg.MainButton.hide();
    }
  }
};

watch(() => [cartStore.cartCount, currentScreen.value], () => {
  setupMainButton();
}, { deep: true, immediate: true });

onMounted(async () => {
  if (window.Telegram?.WebApp) {
    const tg = window.Telegram.WebApp;
    tg.ready();
    tg.expand();
    
    if (tg.colorScheme) {
      document.documentElement.classList.toggle('dark', tg.colorScheme === 'dark');
    }

    tg.MainButton?.onClick(() => {
      if (['main', 'shops', 'menu'].includes(currentScreen.value)) {
        handleNavigation('cart');
      } else if (['cart', 'courier', 'intercity'].includes(currentScreen.value) || currentScreen.value === 'intercity') {
        // Мы будем слушать это событие в компонентах
        window.dispatchEvent(new CustomEvent('tg-main-button-click'));
      }
    });

    // Try Telegram Auth
    if (tg.initData) {
      await authStore.authenticateTelegram();
    }
  }
});

const login = () => {
  if (guestName.value.trim() && guestPhone.value.trim()) {
    authStore.loginAsGuest(guestName.value, guestPhone.value);
  }
};
</script>

<template>
  <div class="min-h-screen bg-gray-50 dark:bg-gray-900 text-gray-800 dark:text-gray-200 overflow-x-hidden transition-colors duration-300">
    
    <!-- Auth Screen for Browser -->
    <div v-if="!authStore.isAuthenticated && !authStore.isTelegram" class="min-h-screen flex items-center justify-center p-6 bg-blue-600">
       <div class="bg-white dark:bg-gray-800 p-8 rounded-[2.5rem] w-full max-w-md shadow-2xl">
          <div class="flex justify-center mb-6">
            <img :src="logo" alt="FastBox Logo" class="h-16 w-auto">
          </div>
          <p class="text-gray-500 text-center mb-8">Введите ваше имя для входа</p>
          
          <input v-model="guestName" type="text" placeholder="Имя Фамилия" class="w-full p-4 rounded-2xl bg-gray-50 dark:bg-gray-700 border-none mb-4 outline-none focus:ring-2 focus:ring-blue-500 transition-all">
          <input v-model="guestPhone" type="tel" placeholder="+7 (707) 000-00-00 (опционально)" class="w-full p-4 rounded-2xl bg-gray-50 dark:bg-gray-700 border-none mb-6 outline-none focus:ring-2 focus:ring-blue-500 transition-all">
          <button @click="login" :disabled="!guestName" class="w-full bg-blue-600 disabled:opacity-50 text-white font-bold py-4 rounded-2xl shadow-lg active:scale-95 transition-all">
            Войти в систему
          </button>
       </div>
    </div>

    <!-- Main App -->
    <div v-else>
      <!-- Fixed Header with Profile -->
      <header v-if="currentScreen === 'main'" class="p-4 flex justify-between items-center bg-white dark:bg-gray-800 shadow-sm transition-colors duration-300">
        <div class="flex items-center">
           <img :src="logo" alt="FastBox" class="h-8 w-auto">
        </div>
        <button @click="handleNavigation('profile')" class="w-10 h-10 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-blue-600">
           <i class="fas fa-user"></i>
        </button>
      </header>

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

        <div v-else-if="currentScreen === 'profile'" key="profile">
          <CourierProfileView v-if="authStore.isCourierMode" @navigate="handleNavigation" />
          <ProfileView v-else @navigate="handleNavigation" />
        </div>

        <div v-else-if="currentScreen === 'intercity'" key="intercity">
          <IntercityView @navigate="handleNavigation" />
        </div>

        <div v-else-if="currentScreen === 'courier_orders'" key="courier_orders">
          <CourierOrdersView @navigate="handleNavigation" />
        </div>
      </transition>
    </div>
  </div>
</template>

<style>
.fade-enter-active,
.fade-leave-active {
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}

.fade-enter-from {
  opacity: 0;
  transform: translateX(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.no-scrollbar::-webkit-scrollbar {
  display: none;
}
.no-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

.screen-fade-in {
  animation: screenIn 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@keyframes screenIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Custom font styles to mimic Telegram */
body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  -webkit-tap-highlight-color: transparent;
}
</style>
