<template>
  <div class="page">
    <header class="topbar">
      <span class="logo">> pr-review-agent<span class="cursor">_</span></span>
      <span class="tag">v1</span>
    </header>

    <main class="main">
      <h1 class="title">PR Review Agent</h1>
      <p class="subtitle">
        多 Agent 协同 · 深度上下文理解 · 并发极速响应<br />不只是 Lint，是真正的代码审查。
      </p>

      <div class="input-block">
        <label class="label">> 仓库地址</label>
        <div class="input-row">
          <input
            v-model="prUrl"
            class="input"
            placeholder="github.com/owner/repo/pull/123"
            @keyup.enter="handleSubmit"
          />
        </div>

        <div class="toggle-row">
          <span class="label">> 模式</span>
          <div class="toggle-group">
            <button class="toggle" :class="{ active: readSourceCode }" @click="readSourceCode = true">
              深度
            </button>
            <button class="toggle" :class="{ active: !readSourceCode }" @click="readSourceCode = false">
              极速
            </button>
          </div>
          <span class="hint">{{ readSourceCode ? '查阅源码 · 上下文完整' : '仅 Diff · 低延迟' }}</span>
        </div>

        <button class="run-btn" :disabled="loading" @click="handleSubmit">
          <template v-if="loading">
            <span class="spin" /> 分析中...
          </template>
          <template v-else>
            > 开始审查
          </template>
        </button>
      </div>

      <div class="demos">
        <span class="label dim">> 快速体验</span>
        <div class="demo-row">
          <button v-for="d in demos" :key="d.url" class="demo-chip" @click="prUrl = d.url">
            {{ d.name }}
          </button>
        </div>
      </div>

      <div class="capsules">
        <span v-for="f in features" :key="f.key" class="capsule">{{ f.label }}</span>
      </div>
    </main>

    <Transition name="fade">
      <div v-if="loading" class="overlay">
        <div class="overlay-box">
          <span class="overlay-prompt">> 执行中</span>
          <p class="overlay-step">{{ loadingStep }}</p>
          <div class="track"><div class="track-fill" /></div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/index'
import { REVIEW_STORAGE_KEY, type StoredReviewResult } from '../types/review'

const prUrl = ref('')
const readSourceCode = ref(true)
const loading = ref(false)
const loadingStep = ref('正在拉取 PR Diff...')
const router = useRouter()

let stepTimer: ReturnType<typeof setInterval> | null = null

const steps = [
  '正在拉取 PR Diff...',
  'Scout Agent · 扫描变更范围...',
  'Evaluate Agent · 并发深度审查...',
  'Synthesize Agent · 生成综合报告...',
]

const demos = [
  { name: 'Vue.js Core', url: 'https://github.com/vuejs/core/pull/9652', color: '#42b883' },
  { name: 'FastAPI', url: 'https://github.com/fastapi/fastapi/pull/15661', color: '#009688' },
]

const features = [
  { key: 'security', label: '安全检测' },
  { key: 'perf', label: '性能分析' },
  { key: 'style', label: '规范审查' },
  { key: 'chat', label: '缺陷追问' },
]

const startStepAnimation = () => {
  let i = 0
  loadingStep.value = steps[0]
  stepTimer = setInterval(() => {
    i = (i + 1) % steps.length
    loadingStep.value = steps[i]
  }, 4000)
}

const stopStepAnimation = () => {
  if (stepTimer) { clearInterval(stepTimer); stepTimer = null }
}

const handleSubmit = async () => {
  if (!prUrl.value.includes('github.com')) {
    ElMessage.warning('请输入有效的 GitHub PR 链接')
    return
  }
  loading.value = true
  startStepAnimation()
  try {
    const res = await api.reviewPr({ pr_url: prUrl.value, read_source_code: readSourceCode.value })
    const stored: StoredReviewResult = { ...res, pr_url: prUrl.value }
    sessionStorage.setItem(REVIEW_STORAGE_KEY, JSON.stringify(stored))
    router.push('/review')
  } catch (error) {
    console.error(error)
  } finally {
    loading.value = false
    stopStepAnimation()
  }
}

onUnmounted(stopStepAnimation)
</script>

<style scoped>
.page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  padding: 0 24px 60px;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 640px;
  width: 100%;
  margin: 0 auto;
  padding: 28px 0;
}

.logo {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
}

.cursor {
  color: var(--accent);
  animation: blink 1s step-end infinite;
}

.tag {
  font-size: 10px;
  color: var(--text-muted);
  border: 1px solid var(--border);
  padding: 2px 8px;
}

.main {
  flex: 1;
  max-width: 640px;
  width: 100%;
  margin: 0 auto;
  animation: fadeUp 0.5s ease-out;
}

.title {
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin: 60px 0 12px;
  color: var(--text-primary);
}

.subtitle {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.8;
  margin: 0 0 40px;
}

.input-block {
  background: var(--bg-card);
  border: 1px solid var(--border);
  padding: 24px;
}

.label {
  display: block;
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 10px;
}

.label.dim { color: var(--text-muted); }

.input-row {
  display: flex;
  align-items: center;
  background: var(--bg-base);
  border: 1px solid var(--border);
  padding: 0 14px;
  transition: border-color 0.15s;
}

.input-row:focus-within { border-color: var(--accent); }

.input {
  width: 100%;
  background: none;
  border: none;
  outline: none;
  padding: 12px 0;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 13px;
}

.input::placeholder { color: var(--text-muted); }

.toggle-row {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-top: 18px;
}

.toggle-row .label { margin-bottom: 0; white-space: nowrap; }

.toggle-group {
  display: flex;
  border: 1px solid var(--border);
}

.toggle {
  padding: 6px 14px;
  background: none;
  border: none;
  color: var(--text-muted);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s;
}

.toggle.active {
  background: var(--accent-dim);
  color: var(--accent);
}

.toggle:not(:last-child) { border-right: 1px solid var(--border); }

.hint {
  font-size: 11px;
  color: var(--text-muted);
}

.run-btn {
  width: 100%;
  margin-top: 18px;
  padding: 14px;
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 600;
  color: var(--bg-base);
  background: var(--accent);
  border: none;
  cursor: pointer;
  transition: opacity 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.run-btn:hover:not(:disabled) { opacity: 0.88; }
.run-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.spin {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(11,11,15,0.3);
  border-top-color: var(--bg-base);
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.demos { margin-top: 32px; }
.demo-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }

.demo-chip {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.15s;
}

.demo-chip:hover {
  border-color: var(--accent);
  color: var(--accent);
}

.capsules {
  display: flex;
  gap: 8px;
  margin-top: 48px;
  flex-wrap: wrap;
}

.capsule {
  font-size: 11px;
  font-weight: 600;
  padding: 5px 12px;
  border: 1px solid var(--border);
  color: var(--text-muted);
}

/* overlay */
.overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(11,11,15,0.92);
}

.overlay-box { text-align: center; padding: 48px; }

.overlay-prompt {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--accent);
}

.overlay-step {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-secondary);
  margin: 12px 0 24px;
  min-height: 18px;
}

.track {
  width: 200px;
  height: 2px;
  background: var(--border);
  margin: 0 auto;
  overflow: hidden;
}

.track-fill {
  width: 40%;
  height: 100%;
  background: var(--accent);
  animation: shimmer 1.5s ease-in-out infinite;
}

@keyframes shimmer {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(350%); }
}

.fade-enter-active, .fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

@media (max-width: 480px) {
  .title { font-size: 22px; margin-top: 32px; }
  .toggle-row { flex-wrap: wrap; gap: 8px; }
}
</style>
