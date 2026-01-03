import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'

export const useSearchStore = defineStore('search', () => {
  const searchQuery = ref('')
  const results = ref([])
  const isLoading = ref(false)
  let debounceTimer = null
  
  function setSearchQuery(query) {
    searchQuery.value = query
    if (query.length > 1) {
      debounceFetch()
    } else {
      results.value = []
    }
  }

  const debounceFetch = () => {
    clearTimeout(debounceTimer)
    debounceTimer = setTimeout(fetchResults, 300)
  }

  const fetchResults = async () => {
    if (searchQuery.value.length < 2) {
      results.value = []
      return
    }

    isLoading.value = true
    try {
      const res = await api.get('/devices/', {
        params: {
          search: searchQuery.value,
          limit: 8
        }
      })
      if (res.data && Array.isArray(res.data.items)) {
        results.value = res.data.items
      } else {
        results.value = []
      }
    } catch (e) {
      console.error('[SearchStore] Failed to fetch search results', e)
      results.value = []
    } finally {
      isLoading.value = false
    }
  }

  return {
    searchQuery,
    results,
    isLoading,
    setSearchQuery,
    fetchResults
  }
})
