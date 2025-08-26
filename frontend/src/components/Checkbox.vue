<template>
  <label class="custom-checkbox cursor-pointer">
    <input
      type="checkbox"
      :checked="modelValue"
      @change="$emit('update:modelValue', ($event.target as HTMLInputElement).checked)"
      class="sr-only"
    />
    <div class="checkbox-wrapper">
      <svg
        v-if="modelValue"
        class="check-icon"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        stroke-width="3"
        stroke-linecap="round"
        stroke-linejoin="round"
      >
        <polyline points="20,6 9,17 4,12"></polyline>
      </svg>
    </div>
    <span v-if="label" class="ml-2 text-sm text-gray-700">{{ label }}</span>
  </label>
</template>

<script setup lang="ts">
interface Props {
  modelValue: boolean
  label?: string
}

defineProps<Props>()
defineEmits<{
  'update:modelValue': [value: boolean]
}>()
</script>

<style scoped>
.custom-checkbox {
  display: inline-flex;
  align-items: center;
  user-select: none;
}

.checkbox-wrapper {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-radius: 6px;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s ease-in-out;
  position: relative;
}

.checkbox-wrapper:hover {
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1);
}

.custom-checkbox input:checked + .checkbox-wrapper {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border-color: #8b5cf6;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.2);
}

.check-icon {
  width: 12px;
  height: 12px;
  color: white;
  opacity: 0;
  transform: scale(0.5);
  transition: all 0.2s ease-in-out;
}

.custom-checkbox input:checked + .checkbox-wrapper .check-icon {
  opacity: 1;
  transform: scale(1);
}

/* 全選checkbox的特殊樣式 */
.custom-checkbox.select-all .checkbox-wrapper {
  width: 18px;
  height: 18px;
  border-width: 2px;
}

.custom-checkbox.select-all .check-icon {
  width: 10px;
  height: 10px;
}

/* 播客卡片中的checkbox樣式 */
.custom-checkbox.card-checkbox .checkbox-wrapper {
  width: 20px;
  height: 20px;
  border-width: 2px;
  background: white;
  border-color: #e5e7eb;
  flex-shrink: 0;
}

.custom-checkbox.card-checkbox .check-icon {
  width: 12px;
  height: 12px;
}

.custom-checkbox.card-checkbox:hover .checkbox-wrapper {
  border-color: #8b5cf6;
  background: white;
  box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.15);
}

.custom-checkbox.card-checkbox input:checked + .checkbox-wrapper {
  background: linear-gradient(135deg, #8b5cf6, #a855f7);
  border-color: #8b5cf6;
}
</style>
