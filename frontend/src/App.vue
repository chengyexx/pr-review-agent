<template>
  <div class="app-root">
    <div class="ambient ambient-1" />
    <div class="ambient ambient-2" />
    <router-view />
  </div>
</template>

<style scoped>
.app-root {
  min-height: 100vh;
  position: relative;
  overflow-x: hidden;
}

.ambient {
  position: fixed;
  border-radius: 50%;
  filter: blur(120px);
  pointer-events: none;
  z-index: 0;
}

.ambient-1 {
  width: 600px;
  height: 600px;
  background: rgba(99, 102, 241, 0.12);
  top: -200px;
  right: -100px;
  animation: pulse-glow 8s ease-in-out infinite;
}

.ambient-2 {
  width: 500px;
  height: 500px;
  background: rgba(34, 211, 238, 0.08);
  bottom: -150px;
  left: -100px;
  animation: pulse-glow 10s ease-in-out infinite reverse;
}
</style>
