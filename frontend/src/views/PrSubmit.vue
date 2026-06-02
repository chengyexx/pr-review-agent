<template>
  <div class="page">
    <nav class="top-nav">
      <div class="nav-brand">
        <div class="brand-icon">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7l10 5 10-5-10-5z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
            <path d="M2 17l10 5 10-5M2 12l10 5 10-5" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
          </svg>
        </div>
        <span>PR Review</span>
      </div>
      <div class="nav-badge">LangGraph Agent</div>
    </nav>

    <main class="hero">
      <div class="hero-badge">AI-Powered Code Review</div>
      <h1 class="hero-title">
        让 AI 架构师<br />
        <span class="gradient-text">审查你的 Pull Request</span>
      </h1>
      <p class="hero-desc">
        基于 LangGraph 多 Agent 协同引擎，深度分析代码变更的安全、性能与规范问题
      </p>

      <div class="input-card">
        <label class="input-label">GitHub PR 链接</label>
        <div class="input-wrapper">
          <svg class="input-icon" width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          <input
            v-model="prUrl"
            class="url-input"
            placeholder="https://github.com/owner/repo/pull/123"
            @keyup.enter="handleSubmit"
          />
        </div>

        <div class="mode-selector">
          <button
            class="mode-card"
            :class="{ active: readSourceCode }"
            @click="readSourceCode = true"
          >
            <div class="mode-icon deep">🔬</div>
            <div class="mode-info">
              <span class="mode-name">深度模式</span>
              <span class="mode-desc">查阅源码，上下文更完整</span>
            </div>
          </button>
          <button
            class="mode-card"
            :class="{ active: !readSourceCode }"
            @click="readSourceCode = false"
          >
            <div class="mode-icon fast">⚡</div>
            <div class="mode-info">
              <span class="mode-name">极速模式</span>
              <span class="mode-desc">仅 Diff 分析，速度更快</span>
            </div>
          </button>
        </div>

        <button class="submit-btn" :disabled="loading" @click="handleSubmit">
          <span v-if="loading" class="btn-loading">
            <span class="spinner" />
            AI 正在深度分析...
          </span>
          <span v-else>
            开始智能评审
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M5 12h14M12 5l7 7-7 7"/>
            </svg>
          </span>
        </button>
      </div>

      <div class="demo-section">
        <span class="demo-label">快速体验</span>
        <div class="demo-chips">
          <button
            v-for="demo in demos"
            :key="demo.url"
            class="demo-chip"
            @click="prUrl = demo.url"
          >
            <span class="chip-dot" :style="{ background: demo.color }" />
            {{ demo.name }}
          </button>
        </div>
      </div>

      <div class="features">
        <div v-for="f in features" :key="f.title" class="feature-item">
          <span class="feature-icon">{{ f.icon }}</span>
          <div>
            <div class="feature-title">{{ f.title }}</div>
            <div class="feature-desc">{{ f.desc }}</div>
          </div>
        </div>
      </div>
    </main>

    <Transition name="overlay">
      <div v-if="loading" class="loading-overlay">
        <div class="loading-card">
          <div class="loading-orbit">
            <div class="orbit-dot" />
          </div>
          <h3>AI 引擎运行中</h3>
          <p class="loading-step">{{ loadingStep }}</p>
          <div class="loading-bar">
            <div class="loading-bar-fill" />
          </div>
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
  'Scout Agent 扫描变更范围...',
  'Evaluate Agent 并发审查代码...',
  'Synthesize Agent 生成评估报告...',
]

const demos = [
  { name: 'Vue.js Core', url: 'https://github.com/vuejs/core/pull/9652', color: '#42b883' },
  { name: 'FastAPI', url: 'https://github.com/fastapi/fastapi/pull/15661', color: '#009688' },
]

const features = [
  { icon: '🛡️', title: '安全检测', desc: '识别注入、越权等安全隐患' },
  { icon: '⚡', title: '性能分析', desc: '发现 N+1 查询与内存泄漏' },
  { icon: '📐', title: '规范审查', desc: '代码风格与最佳实践检查' },
  { icon: '💬', title: '缺陷追问', desc: '针对每条建议实时对话' },
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
  if (stepTimer) {
    clearInterval(stepTimer)
    stepTimer = null
  }
}

const handleSubmit = async () => {
  if (!prUrl.value.includes('github.com')) {
    ElMessage.warning('请输入有效的 GitHub PR 链接')
    return
  }

  loading.value = true
  startStepAnimation()
  try {
    const res = await api.reviewPr({
      pr_url: prUrl.value,
      read_source_code: readSourceCode.value,
    })

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
  padding: 0 24px 80px;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 720px;
  margin: 0 auto;
  padding: 24px 0;
}

.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 700;
  font-size: 15px;
  color: var(--text-primary);
}

.brand-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, var(--accent), var(--cyan));
  border-radius: var(--radius-sm);
  color: white;
}

.nav-badge {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 4px 12px;
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
}

.hero {
  max-width: 720px;
  margin: 0 auto;
  text-align: center;
  animation: fadeUp 0.7s ease-out;
}

.hero-badge {
  display: inline-block;
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--accent-light);
  background: rgba(99, 102, 241, 0.12);
  border: 1px solid var(--border-accent);
  padding: 6px 16px;
  border-radius: 999px;
  margin-bottom: 24px;
}

.hero-title {
  font-size: clamp(32px, 5vw, 48px);
  font-weight: 800;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin: 0 0 16px;
  color: var(--text-primary);
}

.gradient-text {
  background: linear-gradient(135deg, var(--accent-light) 0%, var(--cyan) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.hero-desc {
  font-size: 16px;
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0 0 40px;
  max-width: 520px;
  margin-left: auto;
  margin-right: auto;
}

.input-card {
  text-align: left;
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-xl);
  padding: 28px;
  box-shadow: var(--shadow-glow);
}

.input-label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
  margin-bottom: 10px;
}

.input-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 0 16px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15);
}

.input-icon {
  color: var(--text-muted);
  flex-shrink: 0;
}

.url-input {
  flex: 1;
  background: none;
  border: none;
  outline: none;
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 14px;
  padding: 14px 0;
}

.url-input::placeholder {
  color: var(--text-muted);
}

.mode-selector {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 20px;
}

.mode-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
  color: inherit;
  font-family: inherit;
}

.mode-card:hover {
  border-color: rgba(255, 255, 255, 0.12);
  background: var(--bg-card-hover);
}

.mode-card.active {
  border-color: var(--accent);
  background: rgba(99, 102, 241, 0.08);
  box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
}

.mode-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-sm);
  font-size: 20px;
}

.mode-icon.deep { background: rgba(99, 102, 241, 0.15); }
.mode-icon.fast { background: rgba(251, 191, 36, 0.15); }

.mode-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.mode-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.mode-desc {
  font-size: 11px;
  color: var(--text-muted);
}

.submit-btn {
  width: 100%;
  margin-top: 20px;
  padding: 16px;
  font-size: 15px;
  font-weight: 700;
  font-family: inherit;
  color: white;
  background: linear-gradient(135deg, var(--accent) 0%, #7c3aed 100%);
  border: none;
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: transform 0.15s, box-shadow 0.15s, opacity 0.15s;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 8px 24px rgba(99, 102, 241, 0.35);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.btn-loading {
  display: flex;
  align-items: center;
  gap: 10px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 0.7s linear infinite;
}

.demo-section {
  margin-top: 32px;
}

.demo-label {
  font-size: 12px;
  color: var(--text-muted);
  font-weight: 500;
}

.demo-chips {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.demo-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: 999px;
  color: var(--text-secondary);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
}

.demo-chip:hover {
  border-color: var(--border-accent);
  color: var(--text-primary);
  transform: translateY(-1px);
}

.chip-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.features {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 48px;
  text-align: left;
}

.feature-item {
  display: flex;
  gap: 14px;
  padding: 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  transition: border-color 0.2s;
}

.feature-item:hover {
  border-color: rgba(255, 255, 255, 0.1);
}

.feature-icon {
  font-size: 24px;
  line-height: 1;
}

.feature-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.feature-desc {
  font-size: 12px;
  color: var(--text-muted);
  line-height: 1.4;
}

/* Loading overlay */
.loading-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(9, 9, 11, 0.85);
  backdrop-filter: blur(16px);
}

.loading-card {
  text-align: center;
  padding: 48px;
}

.loading-orbit {
  width: 64px;
  height: 64px;
  margin: 0 auto 24px;
  border: 2px solid var(--border-subtle);
  border-radius: 50%;
  position: relative;
  animation: spin 3s linear infinite;
}

.orbit-dot {
  position: absolute;
  top: -4px;
  left: 50%;
  transform: translateX(-50%);
  width: 8px;
  height: 8px;
  background: var(--accent);
  border-radius: 50%;
  box-shadow: 0 0 12px var(--accent-glow);
}

.loading-card h3 {
  margin: 0 0 8px;
  font-size: 20px;
  font-weight: 700;
}

.loading-step {
  color: var(--text-secondary);
  font-size: 14px;
  margin: 0 0 24px;
  min-height: 20px;
}

.loading-bar {
  width: 240px;
  height: 3px;
  background: var(--border-subtle);
  border-radius: 2px;
  overflow: hidden;
  margin: 0 auto;
}

.loading-bar-fill {
  height: 100%;
  width: 40%;
  background: linear-gradient(90deg, var(--accent), var(--cyan));
  border-radius: 2px;
  animation: shimmer 2s ease-in-out infinite;
  background-size: 200% 100%;
}

.overlay-enter-active, .overlay-leave-active {
  transition: opacity 0.3s;
}
.overlay-enter-from, .overlay-leave-to {
  opacity: 0;
}

@media (max-width: 560px) {
  .mode-selector { grid-template-columns: 1fr; }
  .features { grid-template-columns: 1fr; }
}
</style>
