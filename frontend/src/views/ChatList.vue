<template>
  <div class="page">
    <div class="page-header">
      <h1>聊天</h1>
    </div>

    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>加载中...</span></div>

    <div v-else-if="chats.length === 0" class="empty-state">
      <div class="empty-icon">💬</div>
      <div class="empty-text">还没有聊天</div>
      <div class="empty-sub">去星球加好友开始聊天吧</div>
    </div>

    <div v-else class="chat-list">
      <div v-for="chat in chats" :key="chat.id" class="chat-card fade-up" @click="$router.push('/chat/' + chat.id)">
        <div class="chat-avatar" :style="{ background: avatarColor(chat.id) }">
          <img v-if="chat.avatar" :src="IMG_BASE + chat.avatar" class="chat-avatar-img" />
          <span v-else>{{ chat.nickname?.charAt(0) || '?' }}</span>
        </div>
        <div class="chat-info">
          <div class="chat-name">{{ chat.nickname || chat.username }}</div>
          <div class="chat-last">{{ chat.lastMessage || '开始聊天吧' }}</div>
        </div>
        <div class="chat-meta">
          <div class="chat-time">{{ formatTime(chat.lastTime) }}</div>
          <span v-if="chat.unread > 0" class="chat-badge">{{ chat.unread > 99 ? '99+' : chat.unread }}</span>
        </div>
        <button class="chat-del" @click.stop="deleteChat(chat)" title="删除聊天">✕</button>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'
const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']
export default {
  name: 'ChatList',
  data() {
    return { chats: [], loading: true, IMG_BASE }
  },
  mounted() { this.load() },
  methods: {
    avatarColor(id) { return COLORS[id % COLORS.length] },
    async load() {
      this.loading = true
      try {
        const userId = localStorage.getItem('userId')
        // Load conversations with real last message data
        const res = await api.messages.conversations(userId)
        this.chats = (res.data.conversations || []).map(c => ({
          id: c.userId,
          nickname: c.nickname,
          avatar: c.avatar,
          username: c.nickname,
          lastMessage: c.lastMessage,
          lastTime: c.lastTime,
          unread: c.unread || 0
        }))
      } catch (e) {
        console.error(e)
        // Fallback
        try {
          const res = await api.friends.list(localStorage.getItem('userId'))
          this.chats = res.data.map(f => ({ ...f, lastMessage: null, lastTime: null, unread: 0 }))
        } catch (e2) {}
      }
      finally { this.loading = false }
    },
    async deleteChat(chat) {
      if (!confirm('确定删除与 ' + (chat.nickname || chat.username) + ' 的聊天记录？')) return
      try {
        await api.messages.deleteConversation(localStorage.getItem('userId'), chat.id)
        this.chats = this.chats.filter(c => c.id !== chat.id)
      } catch (e) { /* ignore */ }
    },
    formatTime(t) {
      if (!t) return ''
      const d = new Date(t)
      const now = new Date()
      if (d.toDateString() === now.toDateString())
        return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  }
}
</script>

<style scoped>
.chat-list { display: flex; flex-direction: column; gap: 12px; }
.chat-card {
  display: flex; align-items: center; gap: 16px;
  padding: 18px 16px;
  background: var(--bg-card);
  backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  border-radius: 18px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.04);
  cursor: pointer;
  transition: all 0.2s;
}
.chat-card:hover { background: var(--bg-card-hover); transform: translateY(-1px); box-shadow: 0 4px 18px rgba(0,0,0,0.06); }
.chat-card:active { transform: scale(0.98); }

.chat-avatar {
  width: 56px; height: 56px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 24px; font-weight: 700; flex-shrink: 0;
  overflow: hidden;
  box-shadow: 0 4px 15px rgba(59,130,246,0.25);
}
.chat-avatar-img { width: 100%; height: 100%; object-fit: cover; }

.chat-info { flex: 1; min-width: 0; }
.chat-name { font-size: 17px; font-weight: 600; color: var(--text); margin-bottom: 6px; }
.chat-last { font-size: 14px; color: var(--text-secondary); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; line-height: 1.4; }

.chat-meta { text-align: right; flex-shrink: 0; min-width: 50px; }
.chat-time { font-size: 12px; color: #94a3b8; margin-bottom: 8px; display: block; }
.chat-badge {
  display: inline-block;
  min-width: 22px; height: 22px; line-height: 22px;
  border-radius: 11px; background: #ef4444; color: white;
  font-size: 12px; font-weight: 700; text-align: center; padding: 0 7px;
  box-shadow: 0 2px 8px rgba(239,68,68,0.35);
}
.chat-del {
  width: 24px; height: 24px; border-radius: 50%; border: none;
  background: transparent; color: #cbd5e1; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 10px; transition: all 0.2s; flex-shrink: 0; margin-left: 4px;
}
.chat-del:hover { background: rgba(239,68,68,0.1); color: #ef4444; }
</style>
