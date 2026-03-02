import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useCartStore = defineStore('cart', () => {
  const items = ref([])
  const deliveryFee = 700

  const subtotal = computed(() => {
    return items.value.reduce((total, item) => total + (item.price * item.qty), 0)
  })

  const total = computed(() => subtotal.value + deliveryFee)

  const cartCount = computed(() => {
    return items.value.reduce((count, item) => count + item.qty, 0)
  })

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
    clearCart 
  }
})
