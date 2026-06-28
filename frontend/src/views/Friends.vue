<template>
  <div class="page">
    <div class="page-header">
      <h1>好友</h1>
    </div>

    <!-- 公告栏 -->
    <div class="notice-bar">
      <span class="notice-icon">📢</span>
      <span class="notice-msg">主播没太多钱买太多服务器和适配实时通知，加到好友要赶紧互换微信喔</span>
    </div>

    <!-- Pending requests section -->
    <div v-if="requests.length > 0" class="requests-section">
      <div class="section-header" @click="showRequests = !showRequests">
        <span>好友请求 <span class="req-count">{{ requests.length }}</span></span>
        <svg :class="['chevron', { open: showRequests }]" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><polyline points="6 9 12 15 18 9"/></svg>
      </div>
      <Transition name="collapse">
        <div v-if="showRequests" class="requests-list">
          <div v-for="item in requests" :key="item.id" class="req-card">
            <div class="req-card-accent"></div>
            <div class="avatar avatar-sm" :style="{ background: avatarColor(item.user.id) }">
              <img v-if="item.user.avatar" :src="IMG_BASE + item.user.avatar" class="avatar-img" />
              <span v-else>{{ item.user.nickname?.charAt(0) || item.user.username.charAt(0) }}</span>
            </div>
            <div class="user-info">
              <div class="name">{{ item.user.nickname || item.user.username }}</div>
              <div class="detail">想认识你 ♥</div>
            </div>
            <div class="req-actions">
              <button class="btn-accept" @click="accept(item.friendship_id || item.id)" title="接受">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
              </button>
              <button class="btn-reject" @click="reject(item.friendship_id || item.id)" title="拒绝">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
              </button>
            </div>
          </div>
        </div>
      </Transition>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state"><div class="spinner"></div><span>加载中...</span></div>

    <!-- Search bar -->
    <div v-if="!loading" class="search-wrap">
      <div class="search-inner">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#94a3b8" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
        <input v-model="searchKeyword" class="search-input" placeholder="搜索好友或查找用户..." @input="onSearch" />
        <button v-if="searchKeyword" class="search-clear" @click="clearSearch">✕</button>
      </div>
    </div>

    <!-- Friend list (only show when not searching) -->
    <template v-if="!searchKeyword">
      <div v-if="!loading && friends.length === 0 && requests.length === 0" class="empty-state">
        <div class="empty-icon">&#128106;</div>
        <div class="empty-text">还没好友</div>
        <div class="empty-sub">去搜索框找人加吧</div>
      </div>

      <TransitionGroup name="list" tag="div">
        <div v-for="(friend, idx) in friends" :key="friend.id" class="friend-card" :style="{ animationDelay: idx * 0.06 + 's' }">
          <div class="friend-card-accent"></div>
          <div class="avatar" :style="{ background: avatarColor(friend.id) }">
            <img v-if="friend.avatar" :src="IMG_BASE + friend.avatar" class="avatar-img" />
            <span v-else>{{ friend.nickname?.charAt(0) || friend.username.charAt(0) }}</span>
          </div>
          <div class="friend-info">
            <div class="friend-name">{{ friend.nickname || friend.username }}</div>
            <div class="friend-detail">
              <span class="online-dot"></span>
              {{ friend.age || '?' }}岁 · {{ friend.location || '' }}
            </div>
          </div>
          <button class="btn-chat" @click="chat(friend.id)">
            <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
          </button>
          <button class="btn-del" @click="removeFriend(friend)" title="删除好友">
            <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
          </button>
        </div>
      </TransitionGroup>
    </template>

    <!-- Search results -->
    <template v-if="searchKeyword">
      <div class="search-section-title">好友</div>
      <div v-if="localResults.length === 0" class="search-hint">好友中无匹配</div>
      <div v-for="f in localResults" :key="f.id" class="search-result-card">
        <div class="avatar avatar-sm" :style="{ background: avatarColor(f.id) }">
          <img v-if="f.avatar" :src="IMG_BASE + f.avatar" class="avatar-img" />
          <span v-else>{{ f.nickname?.charAt(0) || f.username.charAt(0) }}</span>
        </div>
        <div class="user-info">
          <div class="name">{{ f.nickname || f.username }}</div>
          <div class="detail">{{ f.age || '?' }}岁 · {{ f.location || '未知' }}</div>
        </div>
        <button class="btn-sm-link" @click="chat(f.id)">聊天</button>
      </div>

      <div class="search-section-title" style="margin-top:12px">其他用户</div>
      <div v-if="searchResults.length === 0" class="search-hint">搜索中...</div>
      <div v-for="u in searchResults" :key="u.id" class="search-result-card" @click="$router.push('/user/' + u.id)">
        <div class="avatar avatar-sm clickable" :style="{ background: avatarColor(u.id) }">
          <img v-if="u.avatar" :src="IMG_BASE + u.avatar" class="avatar-img" />
          <span v-else>{{ u.nickname?.charAt(0) || u.username.charAt(0) }}</span>
        </div>
        <div class="user-info clickable">
          <div class="name">{{ u.nickname || u.username }}</div>
          <div class="detail">{{ u.age || '?' }}岁 · {{ u.gender || '?' }}</div>
        </div>
        <button class="btn-sm-outline">查看主页</button>
      </div>
    </template>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'
const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']
export default {
  name: 'Friends',
  data() {
    return {
      friends: [], requests: [], loading: true, showRequests: true,
      IMG_BASE,
      searchKeyword: '', searchResults: [], searchTimer: null,
      myId: localStorage.getItem('userId')
    }
  },
  computed: {
    localResults() {
      if (!this.searchKeyword) return []
      const kw = this.searchKeyword.toLowerCase()
      return this.friends.filter(f =>
        (f.nickname && f.nickname.toLowerCase().includes(kw)) ||
        (f.username && f.username.toLowerCase().includes(kw))
      )
    }
  },
  mounted() { this.loadAll() },
  methods: {
    avatarColor(id) { return COLORS[id % COLORS.length] },
    async loadAll() {
      this.loading = true
      try {
        const [friendsRes, reqRes] = await Promise.all([
          api.friends.list(this.myId),
          api.friends.requests(this.myId)
        ])
        this.friends = friendsRes.data
        this.requests = reqRes.data
        this.showRequests = this.requests.length > 0
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    onSearch() {
      clearTimeout(this.searchTimer)
      if (!this.searchKeyword) { this.searchResults = []; return }
      this.searchTimer = setTimeout(async () => {
        try {
          const res = await api.users.search(this.searchKeyword)
          // Filter out current user and existing friends
          this.searchResults = res.data.filter(u => u.id != this.myId)
        } catch (e) { /* ignore */ }
      }, 300)
    },
    clearSearch() {
      this.searchKeyword = ''
      this.searchResults = []
    },
    async accept(id) {
      try {
        await api.friends.accept(id, this.myId)
        this.requests = this.requests.filter(r => r.id !== id)
        this.loadAll()
      } catch (e) { alert(e.response?.data?.error || '操作失败') }
    },
    async reject(id) {
      try {
        await api.friends.reject(id, this.myId)
        this.requests = this.requests.filter(r => r.id !== id)
      } catch (e) { alert(e.response?.data?.error || '操作失败') }
    },
    chat(userId) { this.$router.push(`/chat/${userId}`) },
    async removeFriend(friend) {
      if (!confirm('确定删除好友 ' + (friend.nickname || friend.username) + '？')) return
      try {
        await api.friends.remove(friend.id, this.myId)
        this.friends = this.friends.filter(f => f.id !== friend.id)
      } catch (e) {}
    }
  }
}
</script>

<style scoped>
.notice-bar {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  margin-bottom: 14px;
  background: linear-gradient(135deg, rgba(245,158,11,0.08), rgba(239,68,68,0.05));
  border: 1px solid rgba(245,158,11,0.2);
  border-radius: 14px;
  font-size: 13px;
  line-height: 1.6;
  color: #92400e;
}
.notice-icon { flex-shrink: 0; font-size: 16px; }
.notice-msg { flex: 1; font-weight: 500; }

/* Requests section */
.requests-section {
  background: var(--bg-card); border-radius: var(--radius);
  backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: var(--shadow); margin-bottom: 14px;
  overflow: hidden;
}
.section-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; cursor: pointer; user-select: none;
  font-size: 15px; font-weight: 600; color: var(--text);
}
.section-header:hover { background: rgba(0,0,0,0.02); }
.req-count {
  display: inline-flex; align-items: center; justify-content: center;
  background: var(--primary-gradient); color: white; font-size: 11px; font-weight: 700;
  min-width: 20px; height: 20px; border-radius: 10px;
  padding: 0 6px; margin-left: 6px;
}
.chevron { transition: transform 0.25s; color: var(--text-secondary); }
.chevron.open { transform: rotate(180deg); }
.requests-list { border-top: 1px solid var(--border); }
.req-card { display: flex; align-items: center; gap: 12px; padding: 12px 16px; position: relative; overflow: hidden; transition: background 0.2s; }
.req-card:hover { background: rgba(0,0,0,0.02); }
.req-card:not(:last-child) { border-bottom: 1px solid var(--border); }
.req-card-accent { position: absolute; left: 0; top: 0; width: 3px; height: 100%; background: linear-gradient(180deg, #38bdf8, #3b82f6); }
.req-card .user-info { flex: 1; min-width: 0; }
.req-card .name { font-weight: 600; font-size: 14px; color: var(--text); }
.req-card .detail { font-size: 12px; color: var(--primary-light); margin-top: 1px; }
.req-actions { display: flex; gap: 8px; align-items: center; flex-shrink: 0; }
.btn-accept { width: 34px; height: 34px; border-radius: 50%; border: none; background: var(--primary-gradient); color: white; cursor: pointer; display: flex; align-items: center; justify-content: center; box-shadow: 0 4px 12px var(--primary-glow); transition: all 0.2s; }
.btn-accept:hover { transform: scale(1.15); }
.btn-reject { width: 34px; height: 34px; border-radius: 50%; border: 1px solid rgba(239,68,68,0.3); background: rgba(239,68,68,0.1); color: #ef4444; cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.2s; }
.btn-reject:hover { background: rgba(239,68,68,0.2); transform: scale(1.15); }

/* Search bar */
.search-wrap { margin-bottom: 14px; }
.search-inner { display: flex; align-items: center; gap: 10px; background: white; border-radius: 12px; padding: 0 14px; border: 1.5px solid var(--border); transition: all 0.3s; }
.search-inner:focus-within { border-color: var(--primary-light); box-shadow: 0 0 0 3px var(--primary-glow); }
.search-input { flex: 1; padding: 12px 0; border: none; outline: none; font-size: 15px; background: transparent; font-family: inherit; color: var(--text); }
.search-input::placeholder { color: #94a3b8; }
.search-clear { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 16px; padding: 4px; }

/* Friend cards */
.friend-card {
  display: flex; align-items: center; gap: 14px;
  background: var(--bg-card); border-radius: var(--radius); padding: 14px 16px;
  backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: var(--shadow); margin-bottom: 10px;
  position: relative; overflow: hidden;
  animation: fadeUp 0.35s ease both;
  transition: transform 0.2s, box-shadow 0.2s;
}
.friend-card:hover { transform: translateY(-1px); box-shadow: 0 12px 40px rgba(0,0,0,0.1); }
.friend-card-accent { position: absolute; left: 0; top: 0; width: 3px; height: 100%; background: var(--primary-gradient); }
.friend-info { flex: 1; min-width: 0; }
.avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
.friend-name { font-weight: 600; font-size: 16px; color: var(--text); }
.friend-detail { font-size: 13px; color: var(--text-secondary); margin-top: 3px; display: flex; align-items: center; gap: 6px; }
.online-dot { display: inline-block; width: 7px; height: 7px; border-radius: 50%; background: #22c55e; box-shadow: 0 0 8px rgba(34,197,94,0.5); animation: dotPulse 2s ease-in-out infinite; }
@keyframes dotPulse { 0%, 100% { box-shadow: 0 0 6px rgba(34,197,94,0.4); } 50% { box-shadow: 0 0 12px rgba(34,197,94,0.7), 0 0 20px rgba(34,197,94,0.2); } }
.btn-chat { width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--border); background: var(--bg-card); color: var(--primary-light); cursor: pointer; display: flex; align-items: center; justify-content: center; transition: all 0.25s; flex-shrink: 0; }
.btn-chat:hover { background: var(--primary-gradient); color: white; box-shadow: 0 4px 15px var(--primary-glow); border-color: transparent; transform: scale(1.1); }
.btn-del {
  width: 32px; height: 32px; border-radius: 50%; border: none;
  background: transparent; color: #cbd5e1; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  font-size: 13px; font-weight: 600; transition: all 0.2s; flex-shrink: 0;
}
.btn-del:hover { background: rgba(239,68,68,0.1); color: #ef4444; transform: scale(1.1); }

/* Search results */
.search-section-title { font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 8px; padding-left: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
.search-hint { font-size: 13px; color: #94a3b8; padding: 8px 4px; }
.search-result-card {
  display: flex; align-items: center; gap: 12px;
  padding: 10px 12px; border-radius: 12px; cursor: pointer;
  transition: background 0.2s; margin-bottom: 4px;
}
.search-result-card:hover { background: rgba(0,0,0,0.03); }
.search-result-card .user-info { flex: 1; min-width: 0; }
.search-result-card .user-info.clickable { cursor: pointer; }
.search-result-card .avatar.clickable { cursor: pointer; }
.search-result-card .name { font-weight: 600; font-size: 14px; color: var(--text); }
.search-result-card .detail { font-size: 12px; color: var(--text-secondary); margin-top: 1px; }
.btn-sm-link { padding: 6px 14px; border-radius: 8px; border: none; background: transparent; color: var(--primary-light); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; flex-shrink: 0; }
.btn-sm-link:hover { background: rgba(59,130,246,0.08); }
.btn-sm-outline { padding: 6px 14px; border-radius: 8px; border: 1px solid var(--primary-light); background: transparent; color: var(--primary-light); font-size: 13px; font-weight: 600; cursor: pointer; transition: all 0.2s; flex-shrink: 0; }
.btn-sm-outline:hover { background: rgba(59,130,246,0.08); }

/* Collapse transition */
.collapse-enter-active, .collapse-leave-active { transition: all 0.25s ease; overflow: hidden; }
.collapse-enter-from, .collapse-leave-to { opacity: 0; max-height: 0; }
.collapse-enter-to, .collapse-leave-from { max-height: 500px; }

/* List transition */
.list-enter-active { transition: all 0.4s ease; }
.list-enter-from { opacity: 0; transform: translateY(20px); }
</style>
