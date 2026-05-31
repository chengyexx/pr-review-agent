<template>
  <div class="detail-container" v-loading.fullscreen.lock="loading" element-loading-text="🚀 AI 引擎正在进行多维度深度扫描，请稍候...">

    <!-- 炫酷毛玻璃顶部导航 -->
    <div class="glass-header">
      <el-button class="back-btn" @click="$router.push('/')" plain round>
        <span class="icon">←</span> 返回控制台
      </el-button>
      <div class="title-wrapper">
        <h2 class="gradient-title">智能评审战报</h2>
        <el-tag effect="dark" round class="task-badge">ID: {{ $route.params.taskId.slice(-8) }}</el-tag>
      </div>
    </div>

    <!-- 真实数据渲染大盘 -->
    <div v-if="reviewData && reviewData.status === 'completed'" class="dashboard slide-up-anim">

      <!-- 上半部分：左侧雷达，右侧全局总结 -->
      <el-row :gutter="24">
        <el-col :span="10">
          <div class="glass-card radar-wrapper">
            <div class="card-header">
              <span class="header-title"><i class="el-icon-data-analysis"></i> 多维质量感知</span>
              <div class="score-display" :class="getScoreClass(reviewData.result.score)">
                {{ reviewData.result.score }} <span class="score-unit">分</span>
              </div>
            </div>
            <div class="chart-box">
              <RadarChart :scores="reviewData.result.radar_scores || { security: 100, performance: 100, style: 100, robustness: 100 }" />
            </div>
          </div>
        </el-col>

        <el-col :span="14">
          <div class="glass-card summary-wrapper">
            <div class="card-header">
              <span class="header-title">🧠 架构师全局洞察</span>
            </div>
            <div class="summary-content">
              <div class="summary-quote">
                " {{ reviewData.result.summary }} "
              </div>

              <div class="status-banner" :class="reviewData.result.score >= 90 ? 'banner-success' : 'banner-warning'">
                <div class="banner-icon">{{ reviewData.result.score >= 90 ? '✨' : '⚠️' }}</div>
                <div class="banner-text">
                  <strong>{{ reviewData.result.score >= 90 ? '代码规范极佳 (LGTM)' : '存在优化空间' }}</strong>
                  <p>{{ reviewData.result.score >= 90 ? '未发现明显的安全漏洞与性能瓶颈，建议直接合并。' : '请重点关注下方列出的高优先级建议，修复后方可合并。' }}</p>
                </div>
              </div>
            </div>
          </div>
        </el-col>
      </el-row>

      <!-- 下半部分：代码错误详情 -->
      <div class="glass-card issues-wrapper mt-6">
        <div class="card-header">
          <span class="header-title">🔍 代码级审查细节</span>
          <el-badge :value="reviewData.result.details?.length || 0" type="primary" />
        </div>

        <el-empty
          v-if="!reviewData.result.details || reviewData.result.details.length === 0"
          description="太完美了！AI 未发现任何瑕疵 🎉"
          :image-size="120"
        />

        <div v-else class="issue-list">
          <div v-for="(issue, index) in reviewData.result.details" :key="index"
               class="issue-item" :class="`severity-${issue.severity}`">

            <div class="issue-header">
              <el-tag :type="getSeverityType(issue.severity)" effect="dark" class="severity-tag">
                {{ issue.severity.toUpperCase() }}
              </el-tag>
              <span class="file-path"><i class="el-icon-document"></i> {{ issue.file_path }}</span>
              <span class="line-number">Line: {{ issue.line_number }}</span>
            </div>

            <div class="issue-desc">
              <span class="desc-label">风险描述：</span>
              <!-- 强制保留换行与格式 -->
              <div class="raw-text-content" v-html="formatInlineCode(issue.description)"></div>
            </div>

            <div class="issue-suggest">
              <span class="desc-label">修复建议：</span>
              <!-- 终极降维打击：统一包裹在一个极客风格的底板中，强制保留所有大模型吐出的代码缩进 -->
              <div class="universal-code-panel">
                <div class="panel-header">
                  <span class="dot red"></span><span class="dot yellow"></span><span class="dot green"></span>
                  <span class="panel-title">AI Solution</span>
                </div>
                <div class="panel-body" v-html="formatRobustSuggestion(issue.suggestion)"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { api } from '../api/index'
import RadarChart from '../components/RadarChart.vue'

const route = useRoute()
const loading = ref(true)
const reviewData = ref<any>(null)
let pollTimer: any = null

const getScoreClass = (score: number) => {
  if (score >= 90) return 'text-success'
  if (score >= 70) return 'text-warning'
  return 'text-danger'
}

const getSeverityType = (severity: string) => {
  if (severity === 'critical') return 'danger'
  if (severity === 'warning') return 'warning'
  return 'info'
}

// 仅处理行内单反引号，不破坏原始结构
const formatInlineCode = (text: string) => {
  if (!text) return '';
  return text.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
}

// 终极抗造解析器：无论大模型怎么乱吐数据，统一强力格式化
const formatRobustSuggestion = (text: string) => {
  if (!text) return '';
  // 1. 如果模型乖乖用了 ```，去掉它们，因为我们最外层已经有面板了
  let cleanText = text.replace(/```[a-z]*\n?/g, '').replace(/```/g, '');

  // 2. 处理单反引号为红字灰底标签
  cleanText = cleanText.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');

  // 3. 返回纯净文本（依靠 CSS 的 white-space: pre-wrap 保留换行和缩进）
  return cleanText;
}

const checkStatus = async () => {
  const taskId = route.params.taskId as string
  try {
    const res: any = await api.getReviewStatus(taskId)
    if (res.status === 'completed') {
      reviewData.value = res
      loading.value = false
      if (pollTimer) clearInterval(pollTimer)
    } else if (res.status === 'failed') {
      loading.value = false
      if (pollTimer) clearInterval(pollTimer)
      ElMessage.error(`AI 分析失败: ${res.message}`)
    }
  } catch (error) {
    console.error(error)
  }
}

onMounted(() => {
  checkStatus()
  pollTimer = setInterval(checkStatus, 3000)
})

onUnmounted(() => {
  if (pollTimer) clearInterval(pollTimer)
})
</script>

<style scoped>
.detail-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #f0f4f8 0%, #e2e8f0 100%);
  padding: 40px 20px;
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
}

.glass-header {
  max-width: 1200px;
  margin: 0 auto 30px auto;
  display: flex;
  align-items: center;
  gap: 20px;
}

.back-btn {
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
}

.title-wrapper {
  display: flex;
  align-items: center;
  gap: 15px;
}

.gradient-title {
  margin: 0;
  font-size: 28px;
  font-weight: 800;
  background: linear-gradient(90deg, #2563eb, #7c3aed);
  -webkit-background-clip: text;
  color: transparent;
}

.task-badge {
  font-family: 'Fira Code', monospace;
  font-weight: bold;
}

.dashboard { max-width: 1200px; margin: 0 auto; }
.mt-6 { margin-top: 24px; }

.glass-card {
  background: rgba(255, 255, 255, 0.7);
  backdrop-filter: blur(16px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 16px;
  padding: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.03);
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  padding-bottom: 12px;
}

.header-title { font-size: 18px; font-weight: 700; color: #1e293b; }
.score-display { font-size: 32px; font-weight: 900; }
.score-unit { font-size: 14px; font-weight: normal; color: #64748b; }
.text-success { color: #10b981; }
.text-warning { color: #f59e0b; }
.text-danger { color: #ef4444; }

.summary-quote {
  font-size: 20px;
  font-weight: 500;
  color: #334155;
  line-height: 1.6;
  font-style: italic;
  margin-bottom: 24px;
  padding-left: 16px;
  border-left: 4px solid #3b82f6;
}

.status-banner {
  display: flex;
  align-items: flex-start;
  gap: 16px;
  padding: 20px;
  border-radius: 12px;
}
.banner-success { background: rgba(16, 185, 129, 0.05); border: 1px solid rgba(16, 185, 129, 0.2); }
.banner-warning { background: rgba(245, 158, 11, 0.05); border: 1px solid rgba(245, 158, 11, 0.2); }
.banner-icon { font-size: 28px; }
.banner-text strong { display: block; font-size: 16px; margin-bottom: 4px; }

.issue-item {
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.02);
  border: 1px solid #e2e8f0;
}
.severity-critical { border-left: 4px solid #ef4444; }
.severity-warning { border-left: 4px solid #f59e0b; }
.severity-info { border-left: 4px solid #3b82f6; }

.issue-header { display: flex; align-items: center; gap: 12px; margin-bottom: 16px; }
.severity-tag { font-weight: bold; }
.file-path { font-family: 'Fira Code', monospace; color: #334155; font-weight: 600; font-size: 15px; }
.line-number { background: #f1f5f9; padding: 2px 8px; border-radius: 4px; font-size: 13px; color: #64748b; }
.desc-label { font-weight: bold; color: #0f172a; margin-right: 8px; display: block; margin-bottom: 6px; }

.raw-text-content {
  color: #475569;
  font-size: 15px;
  margin-bottom: 16px;
  line-height: 1.6;
  white-space: pre-wrap; /* 强制保留换行 */
}

/* 🌟 兜底王炸：通用极客黑板面板 */
.universal-code-panel {
  background: #1e1e1e;
  border-radius: 10px;
  overflow: hidden;
  margin-top: 10px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
  border: 1px solid #333;
}

.panel-header {
  background: #2d2d2d;
  padding: 8px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  border-bottom: 1px solid #1a1a1a;
}

.dot { width: 10px; height: 10px; border-radius: 50%; display: inline-block; }
.dot.red { background: #ff5f56; }
.dot.yellow { background: #ffbd2e; }
.dot.green { background: #27c93f; }

.panel-title {
  color: #8b949e;
  font-size: 12px;
  font-family: monospace;
  margin-left: 10px;
}

/* 🌟 核心魔法：白空保留符 */
.panel-body {
  padding: 16px;
  margin: 0;
  color: #d4d4d4;
  font-family: 'Fira Code', Consolas, Monaco, monospace;
  font-size: 14px;
  line-height: 1.6;
  white-space: pre-wrap; /* 核心兜底：强行保留大模型吐出的所有缩进和回车 */
  word-wrap: break-word;
}

/* 行内小代码标签 */
:deep(.inline-code) {
  background-color: #374151;
  color: #fca5a5;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}

.slide-up-anim { animation: slideUp 0.6s forwards; }
@keyframes slideUp {
  0% { opacity: 0; transform: translateY(30px); }
  100% { opacity: 1; transform: translateY(0); }
}
</style>