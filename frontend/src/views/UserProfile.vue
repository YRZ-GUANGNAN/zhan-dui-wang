<template>
  <div class="page">
    <div class="page-header">
      <button class="btn-icon" @click="$router.back()" title="返回">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <h1>个人主页</h1>
      <button class="btn-icon" @click="chat" title="聊天" v-if="user && user.id != myId">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
      </button>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div></div>

    <template v-if="user">
      <!-- User info header -->
      <div class="user-header card">
        <div class="user-top">
          <div class="avatar avatar-lg" :style="{ background: avatarColor }">
        <img v-if="userAvatar" :src="userAvatar" class="avatar-img" />
        <span v-else>{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</span>
      </div>
          <div class="user-info">
            <div class="user-name-row">
              <h2 class="user-name">{{ user.nickname || user.username }}</h2>
              <span v-if="user.age" class="user-age">{{ user.age }}</span>
              <span v-if="user.gender" :class="['tag', 'tag-sm', user.gender === '男' ? 'tag-male' : 'tag-female']">{{ user.gender }}</span>
            </div>
            <p class="user-username">@{{ user.username }}</p>
            <p v-if="user.bio" class="user-bio">{{ user.bio }}</p>
            <div class="user-meta">
              <span v-if="user.location" class="meta-item">🎓 {{ user.location }}</span>
            </div>
            <button v-if="user.id != myId" class="btn btn-primary btn-sm btn-add" @click="addFriend" :disabled="adding">
              <span v-if="adding" class="spinner-sm"></span>
              {{ added ? '已发送请求' : '➕ 添加好友' }}
            </button>
          </div>
        </div>
      </div>

      <!-- User's posts -->
      <div class="section-title">Ta 的物品</div>
      <div v-if="postsLoading" class="loading-state" style="padding:20px"><div class="spinner"></div></div>
      <div v-else-if="posts.length === 0" class="empty-state" style="padding:20px">
        <div class="empty-text">Ta 还没发布过物品</div>
      </div>
      <div v-else class="posts-feed">
        <div v-for="post in posts" :key="post.id" class="post-card fade-up">
          <div class="post-content">{{ parseContent(post).story || '（无内容）' }}</div>
          <img v-if="post.imageUrl" :src="imgUrl(post.imageUrl)" class="post-image" @click="openImage(imgUrl(post.imageUrl))" />
          <div class="post-time">{{ formatTime(post.createTime) }}</div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'
const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']
export default {
  name: 'UserProfile',
  data() {
    return {
      user: null, posts: [], loading: true, postsLoading: false, adding: false, added: false,
      userId: Number(this.$route.params.userId),
      myId: Number(localStorage.getItem('userId'))
    }
  },
  computed: {
    avatarColor() { return COLORS[this.user?.id % COLORS.length] },
    userAvatar() { return this.user?.avatar ? IMG_BASE + this.user.avatar : null }
  },
  mounted() { this.load() },
  methods: {
    parseContent(post) {
      let d = post.content
      if (typeof d === 'string') { try { d = JSON.parse(d) } catch { d = null } }
      if (d && typeof d === 'object') return d
      return { story: '' }
    },
    async load() {
      this.loading = true
      try {
        const [userRes, postsRes] = await Promise.all([
          api.users.get(this.userId),
          api.posts.list(this.userId)
        ])
        this.user = userRes.data
        this.posts = postsRes.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    async addFriend() {
      if (this.added || this.adding) return
      this.adding = true
      try {
        await api.friends.request(this.userId, this.myId)
        this.added = true
        this.showToast('好友请求已发送')
      } catch (e) {
        this.showToast(e.response?.data?.error || '操作失败')
      } finally { this.adding = false }
    },
    chat() {
      if (this.userId === this.myId) return
      this.$router.push('/chat/' + this.userId)
    },
    openImage(url) { window.open(url, '_blank') },
    imgUrl(url) { return url?.startsWith('/') ? IMG_BASE + url : url },
    formatTime(t) {
      if (!t) return ''
      const d = new Date(t); const now = new Date()
      const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1)
      if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      if (d.toDateString() === yesterday.toDateString()) return '昨天'
      return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    },
    showToast(msg) {
      const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg
      document.body.appendChild(t)
      setTimeout(() => t.remove(), 2000)
    }
  }
}
</script>

<style scoped>
.user-header { margin-bottom: 16px; }
.user-top { display: flex; gap: 14px; align-items: flex-start; }
.avatar-lg { width: 64px; height: 64px; font-size: 26px; flex-shrink: 0; overflow: hidden; }
.avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
.user-info { flex: 1; min-width: 0; padding-top: 2px; }
.user-name-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.user-name { font-size: 20px; font-weight: 700; color: var(--text); }
.user-age { font-size: 18px; font-weight: 400; color: var(--text-secondary); }
.tag-sm { padding: 2px 8px; font-size: 11px; border-radius: 4px; }
.user-username { color: var(--text-secondary); font-size: 13px; margin-top: 1px; }
.user-bio { color: #64748b; font-size: 14px; margin-top: 6px; line-height: 1.5; }
.user-meta { margin-top: 6px; }
.meta-item { font-size: 13px; color: var(--text-secondary); }
.btn-add { margin-top: 10px; }
.spinner-sm { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.2); border-top-color: white; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }

.section-title { font-size: 15px; font-weight: 600; color: var(--text); margin-bottom: 10px; padding-left: 4px; }

.posts-feed { display: flex; flex-direction: column; gap: 10px; }
.post-card {
  background: var(--bg-card); border-radius: var(--radius); padding: 16px;
  backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: var(--shadow);
}
.post-content { font-size: 15px; line-height: 1.6; color: var(--text); white-space: pre-wrap; word-break: break-word; }
.post-image { width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; margin-top: 10px; cursor: pointer; border: 1px solid var(--border); }
.post-time { font-size: 12px; color: #94a3b8; margin-top: 8px; }
</style>
