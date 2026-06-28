<template>
  <div class="page">
    <div class="page-header">
      <h1>好友请求</h1>
      <button class="btn-icon" @click="logout" title="退出">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
      </button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>加载中...</span></div>
    <div v-else-if="requests.length === 0" class="empty-state">
      <div class="empty-icon">&#128276;</div>
      <div class="empty-text">还没人加你</div>
      <div class="empty-sub">多去「星球」页面逛逛吧</div>
    </div>

    <div v-for="(item, idx) in requests" :key="item.id" class="req-card" :style="{ animationDelay: idx * 0.06 + 's' }">
      <div class="req-card-accent"></div>
      <div class="avatar avatar-sm" :style="{ background: avatarColor(item.user.id) }">{{ item.user.nickname?.charAt(0) || item.user.username.charAt(0) }}</div>
      <div class="user-info">
        <div class="name">{{ item.user.nickname || item.user.username }}</div>
        <div class="detail">想认识你 ♥</div>
      </div>
      <div class="req-actions">
        <button class="btn-accept" @click="accept(item.id)" title="接受">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
        </button>
        <button class="btn-reject" @click="reject(item.id)" title="拒绝">
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']
export default {
  name: 'FriendRequests',
  data() { return { requests: [], loading: true } },
  mounted() { this.load() },
  methods: {
    avatarColor(id) { return COLORS[id % COLORS.length] },
    async load() {
      this.loading = true
      try {
        const res = await api.friends.requests(localStorage.getItem('userId'))
        this.requests = res.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async accept(id) {
      try {
        await api.friends.accept(id, localStorage.getItem('userId'))
        this.requests = this.requests.filter(r => r.id !== id)
      } catch (e) { alert(e.response?.data?.error || '操作失败') }
    },
    async reject(id) {
      try {
        await api.friends.reject(id, localStorage.getItem('userId'))
        this.requests = this.requests.filter(r => r.id !== id)
      } catch (e) { alert(e.response?.data?.error || '操作失败') }
    },
    logout() { localStorage.clear(); this.$router.push('/login') }
  }
}
</script>

<style scoped>
.req-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg-card); border-radius: var(--radius); padding: 14px 16px;
  backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: var(--shadow); margin-bottom: 10px;
  position: relative; overflow: hidden;
  animation: fadeUp 0.35s ease both;
  transition: transform 0.2s, box-shadow 0.2s;
}
.req-card:hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 40px rgba(0,0,0,0.4);
}
.req-card-accent {
  position: absolute; left: 0; top: 0; width: 3px; height: 100%;
  background: linear-gradient(180deg, #38bdf8, #3b82f6);
}
.req-card .user-info { flex: 1; }
.req-card .detail { color: var(--primary-light); }
.req-actions { display: flex; gap: 8px; align-items: center; }
.btn-accept {
  width: 38px; height: 38px; border-radius: 50%; border: none;
  background: var(--primary-gradient); color: white; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px var(--primary-glow);
  transition: all 0.2s;
}
.btn-accept:hover { transform: scale(1.15); }
.btn-reject {
  width: 38px; height: 38px; border-radius: 50%; border: 1px solid rgba(239,68,68,0.3);
  background: rgba(239,68,68,0.1); color: #ef4444; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.btn-reject:hover { background: rgba(239,68,68,0.2); transform: scale(1.15); }
</style>
