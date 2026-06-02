<template>
  <div class="app-root">
    <div class="grid-bg" />
    <router-view />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.grid-bg {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  background-image: radial-gradient(circle, var(--border) 1px, transparent 1px);
  background-size: 24px 24px;
  opacity: 0.4;
}
</style>
