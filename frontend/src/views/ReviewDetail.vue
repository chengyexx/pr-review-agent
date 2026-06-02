<template>
  <div class="page" v-loading="loading" element-loading-text="加载审查结果...">

    <header class="header">
      <button class="back-btn" @click="$router.push('/')">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M19 12H5M12 19l-7-7 7-7"/>
        </svg>
        新建审查
      </button>
      <div class="header-center">
        <h1>审查战报</h1>
        <a v-if="reviewData?.pr_url" :href="reviewData.pr_url" target="_blank" class="pr-link">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z"/>
          </svg>
          {{ shortPrUrl }}
        </a>
      </div>
      <div v-if="reviewData" class="verdict" :class="verdictClass">
        {{ verdictLabel }}
      </div>
    </header>

    <div v-if="reviewData && reviewData.status === 'success'" class="dashboard">

      <div v-if="reviewData.is_trivial" class="alert alert-info">
        <span class="alert-icon">📄</span>
        <div>
          <strong>轻量变更 — 已跳过深度审查</strong>
          <p>{{ reviewData.skip_reason || '该 PR 变更较简单，无需深度分析。' }}</p>
        </div>
      </div>

      <div v-if="reviewData.usage_stats" class="stats-row">
        <div class="stat-card">
          <span class="stat-icon">⏱</span>
          <div>
            <div class="stat-value">{{ reviewData.usage_stats.elapsed_seconds }}s</div>
            <div class="stat-label">分析耗时</div>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">🪙</span>
          <div>
            <div class="stat-value">{{ formatTokens(reviewData.usage_stats.total_tokens) }}</div>
            <div class="stat-label">Token 消耗</div>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">💰</span>
          <div>
            <div class="stat-value">${{ reviewData.usage_stats.estimated_cost_usd.toFixed(4) }}</div>
            <div class="stat-label">估算成本</div>
          </div>
        </div>
        <div class="stat-card">
          <span class="stat-icon">🔍</span>
          <div>
            <div class="stat-value">{{ reviewData.findings?.length || 0 }}</div>
            <div class="stat-label">发现问题</div>
          </div>
        </div>
      </div>

      <div class="overview-grid">
        <div class="card score-card">
          <ScoreRing :score="reviewData.final_score" />
              <RadarChart :scores="radarScores" />
        </div>

        <div class="card insight-card">
          <div class="card-head">
            <span class="card-title">架构师洞察</span>
          </div>
          <blockquote class="summary">{{ reviewData.summary }}</blockquote>

          <div v-if="reviewData.evaluation" class="eval-grid">
            <div class="eval-block">
              <span class="eval-tag">变更目的</span>
              <p>{{ reviewData.evaluation.purpose }}</p>
            </div>
            <div v-if="reviewData.evaluation.pros?.length" class="eval-block pros">
              <span class="eval-tag">✓ 亮点</span>
              <ul>
                <li v-for="(item, i) in reviewData.evaluation.pros" :key="'p' + i">{{ item }}</li>
              </ul>
            </div>
            <div v-if="reviewData.evaluation.cons?.length" class="eval-block cons">
              <span class="eval-tag">⚠ 隐患</span>
              <ul>
                <li v-for="(item, i) in reviewData.evaluation.cons" :key="'c' + i">{{ item }}</li>
              </ul>
            </div>
          </div>

          <div class="verdict-banner" :class="verdictClass">
            <span class="verdict-emoji">{{ reviewData.final_score >= 90 ? '✨' : '⚠️' }}</span>
            <div>
              <strong>{{ reviewData.final_score >= 90 ? 'LGTM — 建议合并' : '需要修复后再合并' }}</strong>
              <p>{{ reviewData.final_score >= 90
                ? '未发现明显安全漏洞与性能瓶颈'
                : '请优先处理 Critical 级别问题' }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="reviewData.added_files?.length" class="card files-card">
        <div class="card-head">
          <span class="card-title">新增文件</span>
          <span class="count-badge">{{ reviewData.added_files.length }}</span>
        </div>
        <div class="file-list">
          <span v-for="file in reviewData.added_files" :key="file" class="file-chip">
            {{ file }}
          </span>
        </div>
      </div>

      <div class="card findings-card">
        <div class="card-head">
          <span class="card-title">代码审查细节</span>
          <div class="filter-tabs">
            <button
              v-for="tab in filterTabs"
              :key="tab.key"
              class="filter-tab"
              :class="{ active: activeFilter === tab.key }"
              @click="activeFilter = tab.key"
            >
              {{ tab.label }}
              <span v-if="tab.count" class="tab-count">{{ tab.count }}</span>
            </button>
          </div>
        </div>

        <div v-if="filteredFindings.length === 0" class="empty-state">
          <div class="empty-icon">{{ hasAnyFindings ? '🔍' : '🎉' }}</div>
          <p>{{ emptyFindingsText }}</p>
        </div>

        <div v-else class="findings-list">
          <div
            v-for="(issue, index) in filteredFindings"
            :key="index"
            class="finding-item"
            :class="`sev-${issue.severity}`"
          >
            <div class="finding-top">
              <span class="sev-badge" :class="issue.severity">{{ issue.severity }}</span>
              <code class="file-path">{{ issue.file_path }}</code>
              <span class="line-badge">L{{ issue.line_number }}</span>
            </div>

            <div class="finding-body">
              <div class="finding-section">
                <label>风险描述</label>
                <div class="text-content" v-html="formatInlineCode(issue.description)" />
              </div>
              <div class="finding-section">
                <label>修复建议</label>
                <div class="code-block">
                  <div class="code-header">
                    <span class="dot red" /><span class="dot yellow" /><span class="dot green" />
                    <span>suggestion</span>
                  </div>
                  <pre class="code-body" v-html="formatRobustSuggestion(issue.suggestion)" />
                </div>
              </div>
            </div>

            <div class="finding-footer">
              <button class="chat-toggle" @click="toggleChat(getOriginalIndex(issue))">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
                </svg>
                {{ activeChatIndex === getOriginalIndex(issue) ? '收起对话' : '追问此缺陷' }}
              </button>

              <Transition name="slide">
                <div v-if="activeChatIndex === getOriginalIndex(issue)" class="chat-box">
                  <div v-if="chatMessages[getOriginalIndex(issue)]?.length" class="chat-thread">
                    <div
                      v-for="(msg, mi) in chatMessages[getOriginalIndex(issue)]"
                      :key="mi"
                      class="chat-bubble"
                      :class="msg.role"
                    >
                      <span class="bubble-label">{{ msg.role === 'user' ? '你' : 'AI 架构师' }}</span>
                      <div v-html="formatInlineCode(msg.content)" />
                    </div>
                  </div>
                  <div class="chat-input">
                    <input
                      v-model="chatInputs[getOriginalIndex(issue)]"
                      placeholder="对这个建议有疑问？"
                      @keyup.enter="sendChat(getOriginalIndex(issue), issue)"
                    />
                    <button
                      :disabled="chatLoading[getOriginalIndex(issue)]"
                      @click="sendChat(getOriginalIndex(issue), issue)"
                    >
                      {{ chatLoading[getOriginalIndex(issue)] ? '...' : '发送' }}
                    </button>
                  </div>
                </div>
              </Transition>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/index'
import RadarChart from '../components/RadarChart.vue'
import ScoreRing from '../components/ScoreRing.vue'
import {
  REVIEW_STORAGE_KEY,
  type StoredReviewResult,
  type ReviewFinding,
} from '../types/review'

const router = useRouter()
const loading = ref(true)
const reviewData = ref<StoredReviewResult | null>(null)
const activeFilter = ref<'all' | 'critical' | 'warning' | 'info'>('all')

const activeChatIndex = ref<number | null>(null)
const chatInputs = reactive<Record<number, string>>({})
const chatLoading = reactive<Record<number, boolean>>({})
const chatMessages = reactive<Record<number, Array<{ role: 'user' | 'assistant'; content: string }>>>({})

const shortPrUrl = computed(() => {
  const url = reviewData.value?.pr_url || ''
  const match = url.match(/github\.com\/(.+)/)
  return match ? match[1] : url.slice(-40)
})

const verdictClass = computed(() => {
  const score = reviewData.value?.final_score ?? 0
  if (score >= 90) return 'pass'
  if (score >= 70) return 'warn'
  return 'fail'
})

const verdictLabel = computed(() => {
  const score = reviewData.value?.final_score ?? 0
  if (score >= 90) return 'LGTM'
  if (score >= 70) return 'NEEDS WORK'
  return 'BLOCKED'
})

const countBySeverity = (sev: string) =>
  reviewData.value?.findings?.filter(f => f.severity === sev).length ?? 0

const filterTabs = computed(() => [
  { key: 'all' as const, label: '全部', count: reviewData.value?.findings?.length ?? 0 },
  { key: 'critical' as const, label: 'Critical', count: countBySeverity('critical') },
  { key: 'warning' as const, label: 'Warning', count: countBySeverity('warning') },
  { key: 'info' as const, label: 'Info', count: countBySeverity('info') },
])

const filteredFindings = computed(() => {
  const findings = reviewData.value?.findings ?? []
  if (activeFilter.value === 'all') return findings
  return findings.filter(f => f.severity === activeFilter.value)
})

const hasAnyFindings = computed(() => (reviewData.value?.findings?.length ?? 0) > 0)

const emptyFindingsText = computed(() => {
  if (!hasAnyFindings.value) return '太完美了！未发现任何瑕疵'
  return '当前筛选条件下无匹配问题'
})

const DEFAULT_RADAR = { security: 100, performance: 100, style: 100, robustness: 100 }

const radarScores = computed(() => reviewData.value?.radar_scores ?? DEFAULT_RADAR)

const getOriginalIndex = (issue: ReviewFinding) =>
  reviewData.value?.findings?.indexOf(issue) ?? -1

const formatTokens = (n: number) =>
  n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)

const formatInlineCode = (text: string) => {
  if (!text) return ''
  return text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>')
}

const formatRobustSuggestion = (text: string) => {
  if (!text) return ''
  // 保留代码块内容但移除 markdown 围栏标记，同时保护行内代码
  // 先用占位符保护行内代码，处理完代码块后再还原
  const inlineCodes: string[] = []
  let protected_text = text.replace(/`([^`]+)`/g, (_, code) => {
    inlineCodes.push(code)
    return `\x00INLINE${inlineCodes.length - 1}\x00`
  })
  // 移除代码块围栏标记（```language 开头和 ``` 结尾）
  protected_text = protected_text.replace(/```[a-zA-Z]*\n?/g, '').replace(/```/g, '')
  // 还原行内代码
  protected_text = protected_text.replace(/\x00INLINE(\d+)\x00/g, (_, i) => {
    return `<code class="inline-code">${inlineCodes[parseInt(i)]}</code>`
  })
  return protected_text
}

const toggleChat = (index: number) => {
  if (index < 0) return
  activeChatIndex.value = activeChatIndex.value === index ? null : index
}

const sendChat = async (index: number, issue: ReviewFinding) => {
  if (index < 0) return
  const message = chatInputs[index]?.trim()
  if (!message) return

  if (!chatMessages[index]) chatMessages[index] = []
  chatMessages[index].push({ role: 'user', content: message })
  chatInputs[index] = ''
  chatLoading[index] = true

  try {
    const res = await api.chatAboutFinding({
      file_path: issue.file_path,
      code_snippet: issue.description,
      finding_description: issue.suggestion,
      user_message: message,
    })
    chatMessages[index].push({ role: 'assistant', content: res.reply })
  } catch (error) {
    console.error(error)
  } finally {
    chatLoading[index] = false
  }
}

onMounted(() => {
  const raw = sessionStorage.getItem(REVIEW_STORAGE_KEY)
  if (!raw) {
    ElMessage.warning('暂无审查结果，请先提交 PR')
    router.replace('/')
    return
  }
  try {
    const parsed = JSON.parse(raw) as StoredReviewResult
    if (parsed.status !== 'success') {
      throw new Error('invalid status')
    }
    reviewData.value = {
      ...parsed,
      findings: parsed.findings ?? [],
      added_files: parsed.added_files ?? [],
      final_score: parsed.final_score ?? 100,
      radar_scores: parsed.radar_scores ?? DEFAULT_RADAR,
    }
  } catch {
    ElMessage.error('审查结果解析失败')
    router.replace('/')
    return
  }
  loading.value = false
})
</script>

<style scoped>
.page {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  padding: 0 24px 80px;
  animation: fadeUp 0.5s ease-out;
}

.header {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px 0;
  background: rgba(9, 9, 11, 0.8);
  backdrop-filter: blur(16px);
  border-bottom: 1px solid var(--border-subtle);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.back-btn:hover {
  color: var(--text-primary);
  border-color: rgba(255,255,255,0.12);
}

.header-center {
  text-align: center;
  flex: 1;
  min-width: 0;
}

.header-center h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
}

.pr-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  text-decoration: none;
  max-width: 360px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pr-link:hover { color: var(--accent-light); }

.verdict {
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.1em;
  padding: 6px 14px;
  border-radius: 999px;
  white-space: nowrap;
}

.verdict.pass { background: rgba(52, 211, 153, 0.12); color: var(--green); border: 1px solid rgba(52, 211, 153, 0.3); }
.verdict.warn { background: rgba(251, 191, 36, 0.12); color: var(--amber); border: 1px solid rgba(251, 191, 36, 0.3); }
.verdict.fail { background: rgba(248, 113, 113, 0.12); color: var(--red); border: 1px solid rgba(248, 113, 113, 0.3); }

.dashboard {
  max-width: 1100px;
  margin: 0 auto;
}

.alert {
  display: flex;
  gap: 14px;
  padding: 16px 20px;
  border-radius: var(--radius-md);
  margin-bottom: 20px;
}

.alert-info {
  background: rgba(34, 211, 238, 0.06);
  border: 1px solid rgba(34, 211, 238, 0.2);
}

.alert-icon { font-size: 24px; }
.alert strong { display: block; margin-bottom: 4px; font-size: 14px; }
.alert p { margin: 0; font-size: 13px; color: var(--text-secondary); }

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 18px;
  background: var(--bg-card);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.stat-icon { font-size: 22px; }
.stat-value {
  font-size: 18px;
  font-weight: 700;
  font-family: var(--font-mono);
  color: var(--text-primary);
}
.stat-label {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 2px;
}

.overview-grid {
  display: grid;
  grid-template-columns: 380px 1fr;
  gap: 16px;
  margin-bottom: 16px;
}

.card {
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 24px;
}

.score-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--text-primary);
}

.summary {
  margin: 0 0 20px;
  padding: 16px 20px;
  font-size: 15px;
  line-height: 1.65;
  color: var(--text-secondary);
  border-left: 3px solid var(--accent);
  background: rgba(99, 102, 241, 0.06);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

.eval-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 20px;
}

.eval-block p, .eval-block ul {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.55;
}

.eval-block ul { padding-left: 18px; }

.eval-tag {
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  color: var(--text-muted);
}

.eval-block.pros .eval-tag { color: var(--green); }
.eval-block.cons .eval-tag { color: var(--amber); }

.verdict-banner {
  display: flex;
  gap: 14px;
  padding: 16px;
  border-radius: var(--radius-md);
}

.verdict-banner.pass { background: rgba(52, 211, 153, 0.06); border: 1px solid rgba(52, 211, 153, 0.15); }
.verdict-banner.warn { background: rgba(251, 191, 36, 0.06); border: 1px solid rgba(251, 191, 36, 0.15); }
.verdict-banner.fail { background: rgba(248, 113, 113, 0.06); border: 1px solid rgba(248, 113, 113, 0.15); }

.verdict-emoji { font-size: 28px; }
.verdict-banner strong { display: block; font-size: 14px; margin-bottom: 4px; }
.verdict-banner p { margin: 0; font-size: 12px; color: var(--text-muted); }

.files-card { margin-bottom: 16px; }

.count-badge {
  font-size: 12px;
  font-weight: 700;
  padding: 2px 10px;
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-light);
  border-radius: 999px;
}

.file-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.file-chip {
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 6px 12px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-secondary);
}

.filter-tabs {
  display: flex;
  gap: 4px;
}

.filter-tab {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: none;
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  color: var(--text-muted);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.filter-tab:hover { color: var(--text-secondary); }
.filter-tab.active {
  background: rgba(99, 102, 241, 0.12);
  border-color: var(--border-accent);
  color: var(--accent-light);
}

.tab-count {
  font-size: 10px;
  font-weight: 700;
  padding: 1px 6px;
  background: rgba(255,255,255,0.06);
  border-radius: 999px;
}

.empty-state {
  text-align: center;
  padding: 48px 0;
  color: var(--text-muted);
}

.empty-icon { font-size: 48px; margin-bottom: 12px; }

.findings-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.finding-item {
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: border-color 0.2s;
}

.finding-item:hover { border-color: rgba(255,255,255,0.1); }
.finding-item.sev-critical { border-left: 3px solid var(--red); }
.finding-item.sev-warning { border-left: 3px solid var(--amber); }
.finding-item.sev-info { border-left: 3px solid var(--accent); }

.finding-top {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  border-bottom: 1px solid var(--border-subtle);
  flex-wrap: wrap;
}

.sev-badge {
  font-size: 10px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 3px 8px;
  border-radius: 4px;
}

.sev-badge.critical { background: rgba(248,113,113,0.15); color: var(--red); }
.sev-badge.warning { background: rgba(251,191,36,0.15); color: var(--amber); }
.sev-badge.info { background: rgba(99,102,241,0.15); color: var(--accent-light); }

.file-path {
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line-badge {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  padding: 2px 8px;
  background: rgba(255,255,255,0.04);
  border-radius: 4px;
}

.finding-body { padding: 18px; }

.finding-section { margin-bottom: 16px; }
.finding-section:last-child { margin-bottom: 0; }

.finding-section label {
  display: block;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.text-content {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

.code-block {
  border-radius: var(--radius-sm);
  overflow: hidden;
  border: 1px solid rgba(255,255,255,0.06);
}

.code-header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 14px;
  background: #1a1a1f;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
}

.dot { width: 10px; height: 10px; border-radius: 50%; }
.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }

.code-body {
  margin: 0;
  padding: 16px;
  background: #121216;
  color: #c9d1d9;
  font-family: var(--font-mono);
  font-size: 13px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.finding-footer {
  padding: 0 18px 18px;
}

.chat-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: none;
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--accent-light);
  font-size: 12px;
  font-family: inherit;
  cursor: pointer;
  transition: all 0.15s;
}

.chat-toggle:hover {
  background: rgba(99, 102, 241, 0.08);
  border-color: var(--border-accent);
}

.chat-box {
  margin-top: 12px;
  padding: 16px;
  background: rgba(255,255,255,0.02);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
}

.chat-thread {
  max-height: 280px;
  overflow-y: auto;
  margin-bottom: 12px;
}

.chat-bubble {
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  margin-bottom: 8px;
  font-size: 13px;
  line-height: 1.55;
}

.chat-bubble.user {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.15);
}

.chat-bubble.assistant {
  background: rgba(255,255,255,0.03);
  border: 1px solid var(--border-subtle);
}

.bubble-label {
  display: block;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 4px;
}

.chat-input {
  display: flex;
  gap: 8px;
}

.chat-input input {
  flex: 1;
  padding: 10px 14px;
  background: var(--bg-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
  font-family: inherit;
  font-size: 13px;
  outline: none;
}

.chat-input input:focus {
  border-color: var(--accent);
}

.chat-input button {
  padding: 10px 18px;
  background: var(--accent);
  border: none;
  border-radius: var(--radius-sm);
  color: white;
  font-weight: 600;
  font-size: 13px;
  font-family: inherit;
  cursor: pointer;
}

.chat-input button:disabled { opacity: 0.5; cursor: not-allowed; }

:deep(.inline-code) {
  background: rgba(99, 102, 241, 0.15);
  color: var(--accent-light);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}

.slide-enter-active, .slide-leave-active {
  transition: all 0.25s ease;
}
.slide-enter-from, .slide-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

@media (max-width: 860px) {
  .overview-grid { grid-template-columns: 1fr; }
  .stats-row { grid-template-columns: repeat(2, 1fr); }
  .header { flex-wrap: wrap; }
  .verdict { display: none; }
  .filter-tabs { flex-wrap: wrap; }
}
</style>
