<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue';
import { useAuthStore } from '../store/useAuth';
import { useCartStore } from '../store/useCart';
import api from '../api/axios';

const emit = defineEmits(['navigate']);
const authStore = useAuthStore();
const cartStore = useCartStore();

const fromCity = ref('');
const toCity = ref('');
const trips = ref([]);
const isSearching = ref(false);
const selectedTrip = ref(null);
const packageWeight = ref(1);
const viewMode = ref('find'); // 'find' or 'post'

const fetchTrips = async () => {
  isSearching.value = true;
  try {
    const response = await api.get('/api/trips');
    trips.value = response.data;
  } catch (error) {
    console.error('Error fetching trips:', error);
  } finally {
    isSearching.value = false;
  }
};

const searchTrips = async () => {
  isSearching.value = true;
  try {
    const response = await api.get('/api/trips');
    trips.value = response.data.filter(t => 
      (!fromCity.value || t.from_city.toLowerCase().includes(fromCity.value.toLowerCase())) &&
      (!toCity.value || t.to_city.toLowerCase().includes(toCity.value.toLowerCase()))
    );
  } catch (error) {
    console.error('Error searching trips:', error);
  } finally {
    isSearching.value = false;
  }
};

const selectTrip = (trip) => {
  selectedTrip.value = trip;
  const tg = window.Telegram?.WebApp;
  if (tg) {
    tg.MainButton.text = "Забронировать (" + (packageWeight.value * trip.price_per_kg) + " ₸)";
    tg.MainButton.show();
  }
};

const isVerified = computed(() => authStore.user?.kyc_status === 'verified');

const handleOrder = async () => {
  if (!selectedTrip.value) return;
  const tg = window.Telegram?.WebApp;
  if (tg) tg.MainButton.showProgress();

  try {
    await api.post('/api/orders', {
      type: 'intercity',
      trip_id: selectedTrip.value.id,
      pickup_address: `Межгород: ${selectedTrip.value.from_city}`,
      delivery_address: `Межгород: ${selectedTrip.value.to_city}`,
      package_details: `Вес: ${packageWeight.value} кг`,
      payment_method: 'cash'
    });

    if (tg) {
      tg.MainButton.hideProgress();
      tg.MainButton.hide();
      tg.showAlert(`✅ Место забронировано! Водитель ${selectedTrip.value.driver_name} свяжется с вами. Напоминание: упаковка посылки должна происходить в вашем присутствии!`);
    }
    emit('navigate', 'main');
  } catch (error) {
    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert('Ошибка при бронировании. Попробуйте позже.');
    }
  }
};

const packageDetails = ref('');

const handlePostRequest = async () => {
  const tg = window.Telegram?.WebApp;
  if (tg) tg.MainButton.showProgress();

  try {
    await api.post('/orders', {
      type: 'intercity',
      pickup_address: `Межгород: ${fromCity.value || 'Не указан'}`,
      delivery_address: `Межгород: ${toCity.value || 'Не указан'}`,
      package_details: `${packageDetails.value} (Вес: ${packageWeight.value} кг)`,
      payment_method: 'cash'
    });

    if (tg) {
      tg.MainButton.hideProgress();
      tg.MainButton.hide();
      tg.showAlert("✅ Ваша заявка опубликована! Теперь она видна в вашем личном кабинете.");
    } else {
      alert("✅ Заявка опубликована! Переходим в личный кабинет.");
    }
    // REDIRECT TO PROFILE TO SHOW SUCCESS
    emit('navigate', 'profile');
  } catch (error) {
    console.error('Error posting request:', error);
    if (tg) {
      tg.MainButton.hideProgress();
      tg.showAlert('Ошибка при создании заявки. Проверьте соединение.');
    }
  }
};

onMounted(() => {
  fetchTrips();
  window.addEventListener('tg-main-button-click', () => {
    if (viewMode.value === 'find') handleOrder();
    else handlePostRequest();
  });
});

onUnmounted(() => {
  window.removeEventListener('tg-main-button-click', () => {});
  window.Telegram?.WebApp?.MainButton.hide();
});
</script>

<template>
  <div id="screen-intercity" class="screen screen-fade-in min-h-screen bg-gray-50 dark:bg-gray-900 pb-10">
    <header class="bg-white dark:bg-gray-800 pt-4 px-4 pb-4 shadow-sm sticky top-0 z-30 flex items-center gap-4 border-b border-transparent dark:border-gray-700 transition-colors duration-300">
      <button @click="emit('navigate', 'main')" class="w-10 h-10 bg-gray-100 dark:bg-gray-700 rounded-full flex items-center justify-center text-gray-600 dark:text-gray-300 active:bg-gray-200 dark:active:bg-gray-600 transition">
        <i class="fas fa-arrow-left"></i>
      </button>
      <h2 class="text-xl font-bold font-heading text-gray-900 dark:text-white">Межгород (P2P)</h2>
    </header>

    <div class="p-6">
      <div class="flex bg-gray-100 dark:bg-gray-800 p-1 rounded-2xl mb-6">
        <button @click="viewMode = 'find'" :class="viewMode === 'find' ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600' : 'text-gray-500'" class="flex-1 py-3 rounded-xl font-bold text-sm transition-all">
          Найти водителя
        </button>
        <button @click="viewMode = 'post'" :class="viewMode === 'post' ? 'bg-white dark:bg-gray-700 shadow-sm text-blue-600' : 'text-gray-500'" class="flex-1 py-3 rounded-xl font-bold text-sm transition-all">
          Оставить заявку
        </button>
      </div>

      <div class="bg-white dark:bg-gray-800 rounded-[2rem] shadow-xl p-6 border dark:border-gray-700">
        <div class="space-y-4">
          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Город отправления</label>
              <input v-model="fromCity" @input="searchTrips" type="text" placeholder="Костанай" class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none focus:ring-2 focus:ring-blue-500">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Город прибытия</label>
              <input v-model="toCity" @input="searchTrips" type="text" placeholder="Астана" class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none focus:ring-2 focus:ring-blue-500">
            </div>
          </div>

          <div v-if="viewMode === 'find'">
            <div v-if="isSearching" class="text-center py-10">
               <div class="animate-spin text-blue-600 text-2xl inline-block mb-2">🔄</div>
               <p class="text-xs text-gray-500">Поиск поездок...</p>
            </div>
            
            <div v-else-if="trips.length > 0" class="mt-6 space-y-3">
              <h3 class="font-bold text-sm text-gray-700 dark:text-gray-300 px-1">Доступные поездки</h3>
              <div v-for="trip in trips" :key="trip.id" @click="selectTrip(trip)" class="p-4 rounded-2xl border-2 transition-all" :class="selectedTrip?.id === trip.id ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20' : 'border-gray-100 dark:border-gray-700 bg-gray-50 dark:bg-gray-800'">
                <div class="flex justify-between items-start mb-2">
                  <div>
                    <p class="font-bold text-blue-600">{{ trip.from_city }} ➔ {{ trip.to_city }}</p>
                    <p class="text-[10px] text-gray-500 flex items-center gap-1 mt-1">
                      <i class="fas fa-car"></i> {{ trip.transport_details || 'Попутка' }}
                    </p>
                  </div>
                  <div class="text-right">
                    <p class="font-black text-gray-900 dark:text-white">{{ trip.price_per_kg }} ₸/кг</p>
                    <p class="text-[10px] text-blue-500 font-bold">Водитель: {{ trip.user?.name || trip.driver_name || 'Александр' }}</p>
                  </div>
                </div>
                <div class="grid grid-cols-2 gap-2 pt-2 border-t dark:border-gray-700 mt-2">
                  <div>
                      <p class="text-[9px] text-gray-400 uppercase font-bold">Выезд</p>
                      <p class="text-xs font-bold">{{ new Date(trip.departure_date).toLocaleString('ru-RU', {day:'numeric', month:'short', hour:'2-digit', minute:'2-digit'}) }}</p>
                  </div>
                  <div>
                      <p class="text-[9px] text-gray-400 uppercase font-bold">Статус</p>
                      <p class="text-xs font-bold text-green-600">Активен</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="text-center py-10">
              <i class="fas fa-search text-3xl text-gray-300 mb-2"></i>
              <p class="text-xs text-gray-500">Поездок по этому маршруту пока нет</p>
            </div>

            <div v-if="selectedTrip" class="pt-4 mt-4 border-t dark:border-gray-700 space-y-4">
              <div class="bg-blue-50 dark:bg-blue-900/20 p-3 rounded-xl border border-blue-100 dark:border-blue-800 flex gap-3">
                  <i class="fas fa-info-circle text-blue-500 mt-0.5"></i>
                  <p class="text-[10px] text-blue-700 dark:text-blue-300 font-medium leading-relaxed">
                    Важно: упаковка посылки в присутствии водителя. Это необходимо для безопасности.
                  </p>
              </div>
              <div>
                <label class="block text-xs font-bold text-gray-500 mb-1">Вес посылки (кг)</label>
                <div class="flex items-center gap-4">
                  <input v-model.number="packageWeight" @input="selectTrip(selectedTrip)" type="range" min="1" max="10" class="flex-1 accent-blue-600">
                  <span class="font-bold text-blue-600">{{ packageWeight }} кг</span>
                </div>
              </div>
              <div class="p-3 bg-gray-100 dark:bg-gray-700 rounded-xl flex justify-between">
                  <span class="text-sm font-bold">К оплате:</span>
                  <span class="text-sm font-black text-blue-600">{{ packageWeight * selectedTrip.price_per_kg }} ₸</span>
              </div>
            </div>
          </div>

          <div v-else class="pt-4 space-y-4">
            <div class="bg-green-50 dark:bg-green-900/20 p-4 rounded-2xl border border-green-100 dark:border-green-800">
               <p class="text-xs text-green-700 dark:text-green-400 leading-relaxed font-bold">
                 Опубликуйте заявку, чтобы водители могли предложить вам свои услуги.
               </p>
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Что отправляем?</label>
              <input v-model="packageDetails" type="text" placeholder="Коробка, документы..." class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none">
            </div>
            <div>
              <label class="block text-xs font-bold text-gray-500 mb-1">Примерный вес (кг)</label>
              <input v-model.number="packageWeight" type="number" class="w-full bg-gray-50 dark:bg-gray-700 text-sm border-none rounded-xl p-3 outline-none">
            </div>
            
            <button @click="handlePostRequest" class="w-full bg-green-600 text-white font-bold py-4 rounded-2xl shadow-lg active:scale-95 transition mt-4">
               Опубликовать заявку
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
