<template>
  <div class="page" v-loading="loading" element-loading-text="加载中...">

    <header class="topbar">
      <button class="back-btn" @click="$router.push('/')">← 新建审查</button>
      <div class="topbar-center">
        <a v-if="reviewData?.pr_url" :href="reviewData.pr_url" target="_blank" class="pr-link">
          {{ shortPrUrl }}
        </a>
      </div>
      <span v-if="reviewData" class="verdict" :class="verdictClass">{{ verdictLabel }}</span>
    </header>

    <div v-if="reviewData && reviewData.status === 'success'" class="dash">

      <div v-if="reviewData.is_trivial" class="alert">
        <span class="alert-icon">!</span>
        <div>
          <strong>轻量变更 · 已跳过深度审查</strong>
          <p>{{ reviewData.skip_reason || '该 PR 变更较简单，无需深度分析。' }}</p>
        </div>
      </div>

      <div v-if="reviewData.usage_stats" class="stats">
        <div class="stat">
          <span class="stat-val">{{ reviewData.usage_stats.elapsed_seconds }}s</span>
          <span class="stat-lbl">耗时</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ formatTokens(reviewData.usage_stats.total_tokens) }}</span>
          <span class="stat-lbl">Token</span>
        </div>
        <div class="stat">
          <span class="stat-val">${{ reviewData.usage_stats.estimated_cost_usd.toFixed(4) }}</span>
          <span class="stat-lbl">成本</span>
        </div>
        <div class="stat">
          <span class="stat-val">{{ reviewData.findings?.length || 0 }}</span>
          <span class="stat-lbl">问题</span>
        </div>
      </div>

      <div class="grid-2">
        <div class="card score-zone">
          <ScoreRing :score="reviewData.final_score" />
          <RadarChart :scores="radarScores" />
        </div>

        <div class="card">
          <div class="card-label">> 架构师洞察</div>
          <blockquote class="summary">{{ reviewData.summary }}</blockquote>

          <div v-if="reviewData.evaluation" class="eval">
            <div class="eval-item">
              <span class="eval-key">变更目的</span>
              <p>{{ reviewData.evaluation.purpose }}</p>
            </div>
            <div v-if="reviewData.evaluation.pros?.length" class="eval-item pros">
              <span class="eval-key">+ 亮点</span>
              <ul><li v-for="(item, i) in reviewData.evaluation.pros" :key="'p' + i">{{ item }}</li></ul>
            </div>
            <div v-if="reviewData.evaluation.cons?.length" class="eval-item cons">
              <span class="eval-key">- 隐患</span>
              <ul><li v-for="(item, i) in reviewData.evaluation.cons" :key="'c' + i">{{ item }}</li></ul>
            </div>
          </div>

          <div class="banner" :class="verdictClass">
            <div>
              <strong>{{ reviewData.final_score >= 90 ? 'LGTM · 建议合并' : '需要修复后再合并' }}</strong>
              <p>{{ reviewData.final_score >= 90 ? '未发现明显安全漏洞与性能瓶颈' : '请优先处理 Critical 级别问题' }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="reviewData.added_files?.length" class="card">
        <div class="card-label">> 新增文件 ({{ reviewData.added_files.length }})</div>
        <div class="chip-row">
          <span v-for="file in reviewData.added_files" :key="file" class="chip">{{ file }}</span>
        </div>
      </div>

      <div class="card">
        <div class="card-head">
          <span class="card-label">> 审查发现</span>
          <div class="filters">
            <button v-for="tab in filterTabs" :key="tab.key" class="filter" :class="{ on: activeFilter === tab.key }" @click="activeFilter = tab.key">
              {{ tab.label }}
              <span v-if="tab.count" class="n">{{ tab.count }}</span>
            </button>
          </div>
        </div>

        <div v-if="filteredFindings.length === 0" class="empty">
          {{ hasAnyFindings ? '当前筛选条件下无匹配问题' : '太完美了！未发现任何代码问题' }}
        </div>

        <div v-else class="findings">
          <div v-for="(issue, index) in filteredFindings" :key="index" class="finding" :class="issue.severity">
            <div class="finding-bar">
              <span class="badge" :class="issue.severity">
                {{ issue.severity === 'critical' ? '致命' : issue.severity === 'warning' ? '警告' : '建议' }}
              </span>
              <code class="fp">{{ issue.file_path }}</code>
              <span class="line">L{{ issue.line_number }}</span>
            </div>
            <div class="finding-body">
              <div class="sec">
                <span class="sec-label">风险描述</span>
                <div class="txt" v-html="formatInlineCode(issue.description)" />
              </div>
              <div class="sec">
                <span class="sec-label">修复建议</span>
                <div class="code-block">
                  <div class="code-topbar">
                    <span class="d r" /><span class="d y" /><span class="d g" />
                    <span>建议代码</span>
                  </div>
                  <pre class="code" v-html="formatRobustSuggestion(issue.suggestion)" />
                </div>
              </div>
            </div>
            <div class="finding-foot">
              <button class="chat-btn" @click="toggleChat(getOriginalIndex(issue))">
                {{ activeChatIndex === getOriginalIndex(issue) ? '收起' : '> 追问此缺陷' }}
              </button>
              <Transition name="slide">
                <div v-if="activeChatIndex === getOriginalIndex(issue)" class="chat">
                  <div v-if="chatMessages[getOriginalIndex(issue)]?.length" class="chat-msgs">
                    <div v-for="(msg, mi) in chatMessages[getOriginalIndex(issue)]" :key="mi" class="msg" :class="msg.role">
                      <span class="msg-role">{{ msg.role === 'user' ? '你' : 'AI 架构师' }}</span>
                      <div v-html="formatInlineCode(msg.content)" />
                    </div>
                  </div>
                  <div class="chat-row">
                    <input v-model="chatInputs[getOriginalIndex(issue)]" placeholder="对这个建议有疑问？" @keyup.enter="sendChat(getOriginalIndex(issue), issue)" />
                    <button :disabled="chatLoading[getOriginalIndex(issue)]" @click="sendChat(getOriginalIndex(issue), issue)">
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
import { REVIEW_STORAGE_KEY, type StoredReviewResult, type ReviewFinding } from '../types/review'

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
  const m = url.match(/github\.com\/(.+)/)
  return m ? m[1] : url.slice(-40)
})

const verdictClass = computed(() => {
  const s = reviewData.value?.final_score ?? 0
  if (s >= 90) return 'pass'
  if (s >= 70) return 'warn'
  return 'fail'
})

const verdictLabel = computed(() => {
  const s = reviewData.value?.final_score ?? 0
  if (s >= 90) return 'LGTM'
  if (s >= 70) return '待修复'
  return '阻断'
})

const countBySeverity = (sev: string) =>
  reviewData.value?.findings?.filter(f => f.severity === sev).length ?? 0

const filterTabs = computed(() => [
  { key: 'all' as const, label: '全部', count: reviewData.value?.findings?.length ?? 0 },
  { key: 'critical' as const, label: '致命', count: countBySeverity('critical') },
  { key: 'warning' as const, label: '警告', count: countBySeverity('warning') },
  { key: 'info' as const, label: '建议', count: countBySeverity('info') },
])

const filteredFindings = computed(() => {
  const findings = reviewData.value?.findings ?? []
  if (activeFilter.value === 'all') return findings
  return findings.filter(f => f.severity === activeFilter.value)
})

const hasAnyFindings = computed(() => (reviewData.value?.findings?.length ?? 0) > 0)

const DEFAULT_RADAR = { security: 100, performance: 100, style: 100, robustness: 100 }
const radarScores = computed(() => reviewData.value?.radar_scores ?? DEFAULT_RADAR)

const getOriginalIndex = (issue: ReviewFinding) =>
  reviewData.value?.findings?.indexOf(issue) ?? -1

const formatTokens = (n: number) => n >= 1000 ? `${(n / 1000).toFixed(1)}k` : String(n)

const formatInlineCode = (text: string) => {
  if (!text) return ''
  return text.replace(/`([^`]+)`/g, '<code class="ic">$1</code>')
}

const formatRobustSuggestion = (text: string) => {
  if (!text) return ''
  const inlineCodes: string[] = []
  let t = text.replace(/`([^`]+)`/g, (_, code) => {
    inlineCodes.push(code)
    return `\x00I${inlineCodes.length - 1}\x00`
  })
  t = t.replace(/```[a-zA-Z]*\n?/g, '').replace(/```/g, '')
  t = t.replace(/\x00I(\d+)\x00/g, (_, i) => `<code class="ic">${inlineCodes[parseInt(i)]}</code>`)
  return t
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
    if (parsed.status !== 'success') throw new Error('invalid')
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
  animation: fadeUp 0.4s ease-out;
}

/* topbar */
.topbar {
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  max-width: 960px;
  margin: 0 auto;
  padding: 18px 0;
  background: rgba(11,11,15,0.88);
  border-bottom: 1px solid var(--border);
}

.back-btn {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 6px 12px;
  background: none;
  border: 1px solid var(--border);
  color: var(--text-secondary);
  cursor: pointer;
  white-space: nowrap;
}
.back-btn:hover { color: var(--accent); border-color: var(--accent); }

.topbar-center { flex: 1; min-width: 0; text-align: center; }
.pr-link {
  font-size: 11px;
  color: var(--text-muted);
  text-decoration: none;
  max-width: 320px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  display: inline-block;
}
.pr-link:hover { color: var(--accent); }

.verdict {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 4px 12px;
  border: 1px solid;
}
.verdict.pass { color: var(--green); border-color: rgba(74,222,128,0.3); }
.verdict.warn { color: var(--amber); border-color: rgba(251,191,36,0.3); }
.verdict.fail { color: var(--red); border-color: rgba(248,113,113,0.3); }

/* dash */
.dash { max-width: 960px; margin: 0 auto; }

.alert {
  display: flex;
  gap: 12px;
  padding: 14px 18px;
  margin: 18px 0;
  border: 1px solid rgba(34,211,238,0.25);
  background: rgba(34,211,238,0.04);
  font-size: 12px;
}
.alert-icon { font-weight: 700; font-size: 16px; color: var(--cyan); }
.alert strong { display: block; margin-bottom: 2px; }
.alert p { margin: 0; color: var(--text-secondary); }

/* stats */
.stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  margin-bottom: 16px;
}
.stat {
  background: var(--bg-card);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stat-val { font-size: 16px; font-weight: 700; color: var(--text-primary); }
.stat-lbl { font-size: 11px; color: var(--text-muted); }

/* grid */
.grid-2 {
  display: grid;
  grid-template-columns: 360px 1fr;
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  margin-bottom: 16px;
}

.card {
  background: var(--bg-card);
  padding: 24px;
  margin-bottom: 1px;
}
.grid-2 .card { margin-bottom: 0; }

.score-zone {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.card-label {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  color: var(--accent);
  margin-bottom: 16px;
}

.card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 16px;
}
.card-head .card-label { margin-bottom: 0; }

/* summary */
.summary {
  margin: 0 0 18px;
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.7;
  color: var(--text-secondary);
  border-left: 2px solid var(--accent);
  background: var(--accent-dim);
}

/* eval */
.eval { display: flex; flex-direction: column; gap: 14px; margin-bottom: 18px; }
.eval-item p, .eval-item ul { margin: 6px 0 0; font-size: 13px; color: var(--text-secondary); line-height: 1.55; }
.eval-item ul { padding-left: 16px; }
.eval-key {
  font-family: var(--font-mono);
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
}
.eval-item.pros .eval-key { color: var(--green); }
.eval-item.cons .eval-key { color: var(--amber); }

/* banner */
.banner {
  padding: 14px 16px;
  border: 1px solid;
  font-size: 13px;
}
.banner.pass { border-color: rgba(74,222,128,0.2); background: rgba(74,222,128,0.04); }
.banner.warn { border-color: rgba(251,191,36,0.2); background: rgba(251,191,36,0.04); }
.banner.fail { border-color: rgba(248,113,113,0.2); background: rgba(248,113,113,0.04); }
.banner strong { display: block; margin-bottom: 2px; }
.banner p { margin: 0; font-size: 11px; color: var(--text-muted); }

/* chip row */
.chip-row { display: flex; flex-wrap: wrap; gap: 6px; }
.chip {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 4px 10px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  color: var(--text-secondary);
}

/* filters */
.filters { display: flex; gap: 2px; }
.filter {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 5px 10px;
  background: none;
  border: 1px solid transparent;
  color: var(--text-muted);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 5px;
}
.filter:hover { color: var(--text-secondary); }
.filter.on { border-color: var(--accent); color: var(--accent); }
.n { font-size: 10px; color: var(--text-muted); }

/* empty */
.empty {
  text-align: center;
  padding: 48px 0;
  font-size: 13px;
  color: var(--text-muted);
}

/* findings */
.findings { display: flex; flex-direction: column; gap: 1px; background: var(--border); }

.finding {
  background: var(--bg-base);
  border-left: 2px solid;
}
.finding.critical { border-left-color: var(--red); }
.finding.warning { border-left-color: var(--amber); }
.finding.info { border-left-color: var(--accent); }

.finding-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.badge {
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  border: 1px solid;
}
.badge.critical { color: var(--red); border-color: rgba(248,113,113,0.3); }
.badge.warning { color: var(--amber); border-color: rgba(251,191,36,0.3); }
.badge.info { color: var(--accent); border-color: rgba(163,230,53,0.3); }

.fp {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--text-primary);
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.line {
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  padding: 2px 6px;
  background: var(--bg-card);
}

.finding-body { padding: 16px; }
.sec { margin-bottom: 14px; }
.sec:last-child { margin-bottom: 0; }

.sec-label {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.05em;
  color: var(--text-muted);
  margin-bottom: 8px;
}

.txt {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  white-space: pre-wrap;
}

/* code block */
.code-block { border: 1px solid var(--border); overflow: hidden; }
.code-topbar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 7px 12px;
  background: var(--bg-card);
  font-family: var(--font-mono);
  font-size: 10px;
  color: var(--text-muted);
  border-bottom: 1px solid var(--border);
}
.d { width: 8px; height: 8px; border-radius: 50%; }
.d.r { background: #ff5f56; }
.d.y { background: #ffbd2e; }
.d.g { background: #27c93f; }
.code {
  margin: 0;
  padding: 14px 16px;
  background: var(--bg-base);
  color: #c9d1d9;
  font-family: var(--font-mono);
  font-size: 12px;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

/* finding foot */
.finding-foot { padding: 0 16px 14px; }

.chat-btn {
  font-family: var(--font-mono);
  font-size: 11px;
  padding: 5px 12px;
  background: none;
  border: 1px solid var(--border);
  color: var(--accent);
  cursor: pointer;
}
.chat-btn:hover { background: var(--accent-dim); }

/* chat */
.chat {
  margin-top: 12px;
  padding: 14px;
  border: 1px solid var(--border);
  background: var(--bg-card);
}
.chat-msgs { max-height: 240px; overflow-y: auto; margin-bottom: 12px; }
.msg {
  padding: 10px 12px;
  margin-bottom: 6px;
  font-size: 13px;
  line-height: 1.5;
  border: 1px solid var(--border);
}
.msg.user { background: var(--bg-base); }
.msg.assistant { border-color: var(--accent-dim); }
.msg-role {
  display: block;
  font-family: var(--font-mono);
  font-size: 10px;
  font-weight: 700;
  color: var(--accent);
  margin-bottom: 4px;
}
.msg.user .msg-role { color: var(--text-muted); }

.chat-row { display: flex; gap: 8px; }
.chat-row input {
  flex: 1;
  padding: 8px 12px;
  background: var(--bg-base);
  border: 1px solid var(--border);
  color: var(--text-primary);
  font-family: var(--font-mono);
  font-size: 12px;
  outline: none;
}
.chat-row input:focus { border-color: var(--accent); }
.chat-row button {
  padding: 8px 16px;
  background: var(--accent);
  border: none;
  color: var(--bg-base);
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}
.chat-row button:disabled { opacity: 0.4; cursor: not-allowed; }

/* inline code */
:deep(.ic) {
  background: var(--accent-dim);
  color: var(--accent);
  padding: 1px 5px;
  font-family: var(--font-mono);
  font-size: 0.9em;
}

/* transitions */
.slide-enter-active, .slide-leave-active { transition: all 0.2s ease; }
.slide-enter-from, .slide-leave-to { opacity: 0; transform: translateY(-6px); }

@media (max-width: 760px) {
  .grid-2 { grid-template-columns: 1fr; }
  .stats { grid-template-columns: repeat(2, 1fr); }
  .topbar { flex-wrap: wrap; }
  .verdict { display: none; }
}
</style>
