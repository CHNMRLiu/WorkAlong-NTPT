<template>
  <div class="stat-card app-card">
    <div class="stat-card__label">{{ label }}</div>
    <div class="stat-card__value tnum">{{ value }}<span class="stat-card__unit" v-if="unit">{{ unit }}</span></div>
    <div v-if="hint" class="stat-card__hint">{{ hint }}</div>
  </div>
</template>

<script setup>
defineProps({
  label: { type: String, required: true },
  value: { type: [String, Number], default: '—' },
  unit: { type: String, default: '' },
  hint: { type: String, default: '' }
})
</script>

<style scoped>
.stat-card { padding: 20px 24px; }
.stat-card__label { font-size: 13px; color: var(--c-text-2); margin-bottom: 8px; }
.stat-card__value { font-size: 32px; font-weight: 700; line-height: 1.1; color: var(--c-text); }
.stat-card__unit { font-size: 14px; font-weight: 500; color: var(--c-text-2); margin-left: 6px; }
.stat-card__hint { font-size: 12px; color: var(--c-text-3); margin-top: 8px; }
</style>
