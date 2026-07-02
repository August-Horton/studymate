<template>
  <van-dropdown-menu>
    <van-dropdown-item v-model="selectedId" :options="courseOptions" @change="handleChange" />
  </van-dropdown-menu>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const emit = defineEmits(['select'])
const selectedId = ref(1)
const courseOptions = ref([])

const fetchCourses = async () => {
  try {
    const res = await api.get('/courses/', { params: { user_id: 1 } })
    courseOptions.value = res.map(c => ({ text: c.name, value: c.id }))
    if (courseOptions.value.length > 0) {
      selectedId.value = courseOptions.value[0].value
      emit('select', selectedId.value)
    }
  } catch (error) {
    console.error('Error fetching courses:', error)
  }
}

const handleChange = (value) => {
  emit('select', value)
}

onMounted(fetchCourses)
</script>