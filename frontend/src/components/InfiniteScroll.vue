<template>
  <div class="infinite-scroll-container">
    <!-- Контент -->
    <div class="content">
      <slot :items="items" :loading="loading" :has-more="hasMore"></slot>
    </div>
    
    <!-- Индикатор загрузки -->
    <div v-if="loading" class="loading-indicator">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">Загрузка...</span>
      </div>
      <p class="mt-2 text-muted">Загружаем еще записи...</p>
    </div>
    
    <!-- Сообщение о конце списка -->
    <div v-else-if="!hasMore && items.length > 0" class="end-message">
      <p class="text-muted">Все записи загружены</p>
    </div>
    
    <!-- Триггер для загрузки -->
    <div ref="trigger" class="scroll-trigger"></div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue'

export default {
  name: 'InfiniteScroll',
  props: {
    items: {
      type: Array,
      default: () => []
    },
    loading: {
      type: Boolean,
      default: false
    },
    hasMore: {
      type: Boolean,
      default: true
    },
    threshold: {
      type: Number,
      default: 100 // пиксели до конца для начала загрузки
    }
  },
  emits: ['load-more'],
  setup(props, { emit }) {
    const trigger = ref(null)
    let observer = null

    const createObserver = () => {
      observer = new IntersectionObserver(
        (entries) => {
          entries.forEach(entry => {
            if (entry.isIntersecting && !props.loading && props.hasMore) {
              emit('load-more')
            }
          })
        },
        {
          rootMargin: `${props.threshold}px`
        }
      )
    }

    const observeTrigger = () => {
      if (trigger.value && observer) {
        observer.observe(trigger.value)
      }
    }

    const unobserveTrigger = () => {
      if (trigger.value && observer) {
        observer.unobserve(trigger.value)
      }
    }

    onMounted(() => {
      createObserver()
      observeTrigger()
    })

    onUnmounted(() => {
      if (observer) {
        observer.disconnect()
      }
    })

    // Переподключаем observer при изменении элементов
    watch(() => props.items, () => {
      if (observer) {
        unobserveTrigger()
        observeTrigger()
      }
    })

    return {
      trigger
    }
  }
}
</script>

<style scoped>
.infinite-scroll-container {
  position: relative;
}

.loading-indicator {
  text-align: center;
  padding: 20px;
}

.end-message {
  text-align: center;
  padding: 20px;
  border-top: 1px solid #e9ecef;
  margin-top: 20px;
}

.scroll-trigger {
  height: 1px;
  width: 100%;
}
</style>
