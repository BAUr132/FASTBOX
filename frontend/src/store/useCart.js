import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import api from '../api/axios'
import { useAuthStore } from './useAuth'

export const useCartStore = defineStore('cart', () => {
  const authStore = useAuthStore()
  const getStoredCart = () => {
    const stored = localStorage.getItem('fb_cart_items');
    if (!stored || stored === 'undefined' || stored === 'null') return [];
    try {
      return JSON.parse(stored);
    } catch (e) {
      return [];
    }
  }

  const items = ref(getStoredCart())
  const deliveryFee = 500
  const isProcessing = ref(false)
  
  watch(items, (newItems) => {
    localStorage.setItem('fb_cart_items', JSON.stringify(newItems))
  }, { deep: true })

  const subtotal = computed(() => {
    return items.value.reduce((total, item) => total + (item.price * item.qty), 0)
  })

  const total = computed(() => subtotal.value + deliveryFee)

  const cartCount = computed(() => {
    return items.value.reduce((count, item) => count + item.qty, 0)
  })

  async function authenticate() {
    if (authStore.isAuthenticated) return authStore.token
    return await authStore.authenticateTelegram()
  }

  async function checkout(paymentMethod = 'card') {
    if (isProcessing.value) return;
    
    // Authenticate if not already
    if (!authStore.isAuthenticated) {
      await authenticate()
    }
    
    if (!authStore.isAuthenticated) {
      throw new Error('Ошибка авторизации. Пожалуйста, перезапустите приложение.')
    }

    isProcessing.value = true;

    const orderData = {
      id: Math.floor(Math.random() * 9000) + 1000,
      user_id: authStore.user?.id || 999,
      type: 'shop',
      status: 'new',
      payment_method: paymentMethod,
      items: items.value.map(item => ({
        product_id: item.id,
        quantity: item.qty,
        product: { name: item.name, price: item.price }
      })),
      delivery_fee: deliveryFee,
      total_price: subtotal.value,
      pickup_address: 'Магазин "FastBox"',
      delivery_address: 'Ваш адрес',
      created_at: new Date().toISOString()
    }

    try {
      // ЗАКОММЕНТИРОВАНО ДЛЯ ДЕМО
      // const response = await api.post('/orders', orderData)
      
      // Имитация сохранения для курьера
      const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
      mockOrders.push(orderData);
      localStorage.setItem('fb_mock_orders', JSON.stringify(mockOrders));

      clearCart()
      return { order: orderData }
    } catch (error) {
      console.warn('Checkout backend error, using mock:', error)
      const mockOrders = JSON.parse(localStorage.getItem('fb_mock_orders') || '[]');
      mockOrders.push(orderData);
      localStorage.setItem('fb_mock_orders', JSON.stringify(mockOrders));
      
      clearCart()
      return { order: orderData }
    } finally {
      isProcessing.value = false;
    }
  }

  function addToCart(product) {
    const existingItem = items.value.find(i => i.id === product.id)
    if (existingItem) {
      existingItem.qty++
    } else {
      items.value.push({ ...product, qty: 1 })
    }
  }

  function updateQty(id, delta) {
    const item = items.value.find(i => i.id === id)
    if (item) {
      item.qty += delta
      if (item.qty <= 0) {
        items.value = items.value.filter(i => i.id !== id)
      }
    }
  }

  function clearCart() {
    items.value = []
  }

  return { 
    items, 
    deliveryFee, 
    subtotal, 
    total, 
    cartCount,
    addToCart, 
    updateQty, 
    clearCart,
    checkout
  }
})
