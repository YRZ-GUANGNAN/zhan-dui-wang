<template>
  <div class="page">
    <div class="page-header">
      <h1>🌍 星球</h1>
      <button class="btn-icon" @click="showSearch = !showSearch" title="搜索">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      </button>
    </div>

    <!-- Search panel -->
    <Transition name="search-drop">
      <div v-if="showSearch" class="search-panel">
        <div class="search-inner">
          <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#64748b" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
          <input v-model="keyword" class="search-input" placeholder="搜索星球上的TA..." @input="doSearch" ref="searchInput" />
          <button v-if="keyword" class="search-clear" @click="clearSearch">✕</button>
        </div>
      </div>
    </Transition>

    <!-- Notice bar -->
    <div class="notice-bar">
      <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/></svg>
      <span>这里只展示愿意找对象的用户，不想展示可在「我的」页面关闭</span>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="loading-state" style="margin-top:80px">
      <div class="spinner"></div>
      <span>探索宇宙中...</span>
    </div>

    <!-- Empty state -->
    <div v-else-if="users.length === 0" class="empty-state" style="margin-top:80px">
      <div class="empty-icon">&#127776;</div>
      <div class="empty-text">这个星球还没有人</div>
      <div class="empty-sub">喊同学来注册吧</div>
    </div>

    <!-- Card stack -->
    <div v-else class="card-stack" ref="stackEl" :class="{ dragging: isDragging }">
      <div
        v-for="(user, idx) in visibleCards"
        :key="user.id"
        class="swipe-card"
        :class="{ 'card-top': idx === 0, 'card-dragging': isDragging && idx === 0 }"
        :style="getCardStyle(idx)"
      @pointerdown="idx === 0 && onPointerDown($event)"
      >
        <!-- NOPE badge (shows on left drag) -->
        <div class="swipe-badge swipe-badge-nope" :style="{ opacity: idx === 0 ? nopeOpacity : 0 }">
          NOPE
        </div>
        <!-- LIKE badge (shows on right drag) -->
        <div class="swipe-badge swipe-badge-like" :style="{ opacity: idx === 0 ? likeOpacity : 0 }">
          LIKE
        </div>

        <!-- Top gradient area -->
        <div class="swipe-card-top" :style="cardTopStyle(user)">
          <div class="swipe-avatar">
            <img v-if="user.avatar" :src="IMG_BASE + user.avatar" class="swipe-avatar-img" />
            <span v-else>{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</span>
          </div>
          <div class="match-badge" :class="matchClass(user.score)">{{ user.score || 0 }}% 匹配</div>
        </div>

        <!-- Bottom info area -->
        <div class="swipe-card-body">
          <div class="swipe-name-row">
            <span class="swipe-name">{{ user.nickname || user.username }}</span>
            <span v-if="user.age" class="swipe-age">{{ user.age }}</span>
            <span v-if="user.gender" :class="['tag', user.gender === '男' ? 'tag-male' : 'tag-female']">{{ user.gender }}</span>
          </div>
          <div class="swipe-meta">
            <span v-if="user.location" class="swipe-location">🎓 {{ user.location }}</span>
          </div>
          <p v-if="user.bio" class="swipe-bio">{{ user.bio }}</p>
          <div v-if="user.interests && user.interests.length" class="swipe-tags">
            <span v-for="(tag, i) in user.interests.slice(0,3)" :key="i" class="interest-tag">{{ tag }}</span>
          </div>
        </div>

        <!-- Drag-handle indicator -->
        <div v-if="idx === 0 && !isDragging" class="drag-hint">↔ 拖动操作</div>
      </div>
    </div>

    <!-- Action buttons -->
    <div v-if="users.length > 0 && !loading" class="action-bar">
      <button class="act-btn act-skip" @click="swipeLeft">
        <span class="act-icon-wrap act-icon-skip">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </span>
        <span class="act-label">跳过</span>
      </button>

      <button class="act-btn act-rewind" @click="loadUsers">
        <span class="act-icon-wrap act-icon-rewind">
          <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
        </span>
        <span class="act-label">刷新</span>
      </button>

      <button class="act-btn act-like" @click="addFriend">
        <span class="act-icon-wrap act-icon-like">
          <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/><line x1="20" y1="8" x2="20" y2="14"/><line x1="23" y1="11" x2="17" y2="11"/></svg>
        </span>
        <span class="act-label">加好友</span>
      </button>

      <button class="act-btn act-greet" @click="greetAndAdd">
        <span class="act-icon-wrap act-icon-greet">
          <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
        </span>
        <span class="act-label">打招呼</span>
      </button>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'

const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']
const SWIPE_THRESHOLD = 100

export default {
  name: 'Home',
  data() {
    return {
      users: [], keyword: '', loading: true, showSearch: false,
      cardIndex: 0,
      // drag state
      isDragging: false, startX: 0, startY: 0, deltaX: 0, deltaY: 0,
      // exit animation state
      exiting: false, exitX: 0, exitY: 0, exitRotate: 0,
      exitingDirection: 0, // -1 left, 1 right
      // lock to prevent double-swipe
      swipeLock: false,
      IMG_BASE,
    }
  },
  computed: {
    visibleCards() {
      return this.users.slice(this.cardIndex, this.cardIndex + 3)
    },
    likeOpacity() {
      if (!this.isDragging || this.deltaX <= 0) return 0
      return Math.min(Math.abs(this.deltaX) / SWIPE_THRESHOLD, 1)
    },
    nopeOpacity() {
      if (!this.isDragging || this.deltaX >= 0) return 0
      return Math.min(Math.abs(this.deltaX) / SWIPE_THRESHOLD, 1)
    }
  },
  mounted() {
    this.loadUsers()
    document.addEventListener('pointermove', this.onPointerMove)
    document.addEventListener('pointerup', this.onPointerUp)
  },
  beforeUnmount() {
    document.removeEventListener('pointermove', this.onPointerMove)
    document.removeEventListener('pointerup', this.onPointerUp)
  },
  methods: {
    avatarGradient(id) {
      const c1 = COLORS[id % COLORS.length]
      const c2 = COLORS[(id + 3) % COLORS.length]
      return `linear-gradient(135deg, ${c1}, ${c2})`
    },
    cardTopStyle(user) {
      if (user.background) {
        return { backgroundImage: `url(${IMG_BASE}${user.background})`, backgroundSize: 'cover', backgroundPosition: 'center' }
      }
      return { background: this.avatarGradient(user.id) }
    },
    matchClass(score) {
      if (!score) return ''
      if (score >= 70) return 'match-high'
      if (score >= 40) return 'match-mid'
      return 'match-low'
    },
    async loadUsers() {
      this.loading = true
      this.cardIndex = 0
      this.resetDrag()
      try {
        const res = await api.users.recommend(localStorage.getItem('userId'))
        this.users = res.data
      } catch (e) {
        // Fallback to regular list
        try {
          const res = await api.users.list(localStorage.getItem('userId'))
          this.users = res.data
        } catch (e2) { console.error(e2) }
      }
      finally { this.loading = false }
    },
    async doSearch() {
      if (!this.keyword) { this.loadUsers(); return }
      this.loading = true
      this.cardIndex = 0
      try {
        const res = await api.users.search(this.keyword)
        this.users = res.data
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    clearSearch() {
      this.keyword = ''
      this.loadUsers()
    },
    nextCard() {
      this.cardIndex++
      this.resetDrag()
      // Pre-fetch more users when running low
      if (this.cardIndex >= this.users.length - 2 && !this.keyword) {
        this.loadUsers()
      }
    },
    // ---- Drag system ----
    resetDrag() {
      this.isDragging = false
      this.deltaX = 0
      this.deltaY = 0
      this.exiting = false
      this.exitX = 0
      this.exitY = 0
      this.exitRotate = 0
      this.exitingDirection = 0
    },
    onPointerDown(e) {
      if (this.swipeLock || this.exiting || this.visibleCards.length === 0) return
      const card = e.currentTarget
      card.setPointerCapture(e.pointerId)
      this.isDragging = true
      this.startX = e.clientX
      this.startY = e.clientY
      this.deltaX = 0
      this.deltaY = 0
    },
    onPointerMove(e) {
      if (!this.isDragging) return
      this.deltaX = e.clientX - this.startX
      this.deltaY = e.clientY - this.startY
    },
    onPointerUp(e) {
      if (!this.isDragging) return
      this.isDragging = false

      if (Math.abs(this.deltaX) > SWIPE_THRESHOLD) {
        // Trigger fly-out
        const direction = this.deltaX > 0 ? 1 : -1
        this.exiting = true
        this.exitingDirection = direction
        this.exitX = direction * (window.innerWidth * 1.2)
        this.exitY = this.deltaY * 2
        this.exitRotate = direction * 30

        // After exit animation
        const targetId = this.users[this.cardIndex].id
        setTimeout(async () => {
          if (direction > 0) {
            // 右滑: 加好友 + 自动发消息 + 跳转聊天
            const ok = await this.sendFriendRequest(targetId)
            if (ok) {
              try {
                const { default: api } = await import('../api/index.js')
                await api.messages.send(localStorage.getItem('userId'), targetId, '你好，很高兴认识你！')
              } catch (e) {}
              this.nextCard()
              this.$router.push('/chat/' + targetId)
              return
            }
          }
          this.nextCard()
        }, 350)
      } else {
        // Snap back
        this.deltaX = 0
        this.deltaY = 0
      }
    },
    getCardStyle(idx) {
      const isTop = idx === 0
      const isSecond = idx === 1
      const isThird = idx === 2

      // Base stack transforms
      let scale = 1
      let translateY = 0
      let zIndex = 10 - idx

      if (isTop) {
        scale = 1
        translateY = 0
      } else if (isSecond) {
        scale = 0.95
        translateY = 10
      } else {
        scale = 0.90
        translateY = 20
      }

      // Apply exit animation for top card
      if (isTop && this.exiting) {
        return {
          transform: `translate(${this.exitX}px, ${this.exitY}px) rotate(${this.exitRotate}deg)`,
          transition: 'transform 0.35s cubic-bezier(0.22, 1, 0.36, 1)',
          zIndex,
          opacity: 0.5 + Math.min(Math.abs(this.exitX) / (window.innerWidth * 2), 0.5)
        }
      }

      // Apply drag transform for top card
      if (isTop && this.isDragging) {
        const rotation = this.deltaX * 0.1 // 0.1 deg per px
        return {
          transform: `translate(${this.deltaX}px, ${this.deltaY}px) rotate(${rotation}deg)`,
          transition: 'none',
          zIndex,
          cursor: 'grabbing'
        }
      }

      // Snap-back transition
      if (isTop && !this.isDragging) {
        return {
          transform: `translate(0, 0) rotate(0deg)`,
          transition: 'transform 0.4s cubic-bezier(0.22, 1, 0.36, 1)',
          zIndex
        }
      }

      // Stack transforms for non-top cards
      return {
        transform: `translate(0, ${translateY}px) scale(${scale})`,
        zIndex,
        transition: 'transform 0.3s cubic-bezier(0.22, 1, 0.36, 1)'
      }
    },
    // ---- Actions ----
    async sendFriendRequest(userId) {
      try {
        await api.friends.request(userId, localStorage.getItem('userId'))
        return true
      } catch (e) {
        const msg = e.response?.data?.error || e.response?.data || '操作失败'
        this.showToast(msg)
        return false
      }
    },
    addFriend() {
      if (this.swipeLock || this.exiting || this.visibleCards.length === 0) return
      if (!localStorage.getItem('token')) { this.$router.push('/login'); return }
      this.swipeLock = true
      const targetId = this.users[this.cardIndex].id
      this.sendFriendRequest(targetId).then(async ok => {
        if (ok) {
          try {
            await api.messages.send(localStorage.getItem('userId'), targetId, '你好，很高兴认识你！')
          } catch (e) { /* ignore */ }
        }
        this.exiting = true
        this.exitingDirection = 1
        this.exitX = window.innerWidth * 1.2
        this.exitY = -50
        this.exitRotate = 30
        setTimeout(() => {
          this.nextCard()
          this.swipeLock = false
        }, 350)
      })
    },
    async greetAndAdd() {
      if (this.swipeLock || this.exiting || this.visibleCards.length === 0) return
      if (!localStorage.getItem('token')) { this.$router.push('/login'); return }
      this.swipeLock = true
      const targetId = this.users[this.cardIndex].id
      const ok = await this.sendFriendRequest(targetId)
      this.exiting = true
      this.exitingDirection = 1
      this.exitX = window.innerWidth * 1.2
      this.exitY = -80
      this.exitRotate = 25
      setTimeout(() => {
        this.nextCard()
        this.swipeLock = false
        if (ok) this.$router.push('/chat/' + targetId)
      }, 350)
    },
    swipeRight() {
      // Map to addFriend
      this.addFriend()
    },
    swipeLeft() {
      if (this.swipeLock || this.exiting || this.visibleCards.length === 0) return
      this.swipeLock = true
      this.exiting = true
      this.exitingDirection = -1
      this.exitX = -window.innerWidth * 1.2
      this.exitY = 50
      this.exitRotate = -30

      setTimeout(() => {
        this.nextCard()
        this.swipeLock = false
      }, 350)
    },
    showToast(msg) {
      const t = document.createElement('div')
      t.className = 'toast'
      t.textContent = msg
      document.body.appendChild(t)
      setTimeout(() => t.remove(), 2000)
    },
    logout() { api.auth.logout(); this.$router.push('/login') }
  }
}
</script>

<style scoped>
/* Search panel */
.search-panel {
  margin-bottom: 16px;
  animation: slideDown 0.25s ease both;
}
@keyframes slideDown {
  from { opacity: 0; transform: translateY(-10px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Notice bar */
.notice-bar {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 14px; margin-bottom: 16px;
  background: linear-gradient(135deg, rgba(59,130,246,0.08), rgba(99,102,241,0.08));
  border-radius: 12px;
  border: 1px solid rgba(59,130,246,0.15);
  font-size: 13px; color: #3b82f6; line-height: 1.5;
}
.notice-bar svg { flex-shrink: 0; color: #3b82f6; }

.search-inner {
  display: flex; align-items: center; gap: 10px;
  background: var(--bg-card); border-radius: 14px; padding: 0 14px;
  border: 1px solid var(--border); transition: all 0.3s;
  backdrop-filter: blur(20px);
}
.search-inner:focus-within {
  border-color: var(--primary-light);
  box-shadow: 0 0 15px var(--primary-glow);
}
.search-input {
  flex: 1; padding: 14px 0; border: none; outline: none; font-size: 15px;
  background: transparent; font-family: inherit; color: var(--text);
}
.search-input::placeholder { color: #94a3b8; }
.search-clear {
  background: none; border: none; color: var(--text-secondary); cursor: pointer;
  font-size: 16px; padding: 4px;
}

/* Card stack container */
.card-stack {
  position: relative;
  width: 100%;
  max-width: 400px;
  height: min(520px, calc(100vh - 340px));
  min-height: 360px;
  margin: 0 auto 16px;
  touch-action: pan-y;
  user-select: none;
  -webkit-user-select: none;
  overflow: visible;
}
.card-stack.dragging {
  touch-action: none;
}

/* Individual swipe card */
.swipe-card {
  position: absolute;
  top: 0; left: 0;
  width: 100%;
  height: 100%;
  border-radius: 20px;
  overflow: hidden;
  background: var(--bg-card);
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
  will-change: transform;
  cursor: grab;
}

.swipe-card.card-top {
  cursor: grab;
}

/* Top gradient area */
.swipe-card-top {
  height: 55%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}
.swipe-card-top::after {
  content: ''; position: absolute; inset: 0;
  background: linear-gradient(0deg, rgba(0,0,0,0.4), transparent);
  pointer-events: none;
}

.swipe-avatar {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  background: rgba(0,0,0,0.25);
  border: 3px solid rgba(255,255,255,0.3);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36px;
  font-weight: 700;
  color: white;
  backdrop-filter: blur(10px);
  box-shadow: 0 0 30px rgba(0,0,0,0.3);
  overflow: hidden;
}
.swipe-avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }

.match-badge {
  position: absolute; bottom: 12px; right: 12px;
  padding: 4px 10px; border-radius: 8px;
  font-size: 12px; font-weight: 700; letter-spacing: 0.5px;
  backdrop-filter: blur(8px);
}
.match-high { background: rgba(59,130,246,0.85); color: white; }
.match-mid { background: rgba(34,197,94,0.85); color: white; }
.match-low { background: rgba(148,163,184,0.85); color: white; }

/* Bottom info area */
.swipe-card-body {
  padding: 16px 20px;
  background: white;
  height: 45%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.swipe-name-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.swipe-name {
  font-size: 22px;
  font-weight: 700;
  color: var(--text);
}

.swipe-age {
  font-size: 20px;
  font-weight: 400;
  color: var(--text-secondary);
}

.swipe-meta {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 6px;
}

.swipe-bio {
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.swipe-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
}

.interest-tag {
  padding: 4px 10px; border-radius: 6px;
  background: rgba(0,0,0,0.04); color: var(--text-secondary);
  font-size: 12px;
}

/* Swipe badges (NOPE / LIKE) */
.swipe-badge {
  position: absolute;
  top: 24px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 28px;
  font-weight: 800;
  letter-spacing: 3px;
  z-index: 10;
  pointer-events: none;
  transform: rotate(-15deg);
  border: 3px solid;
  backdrop-filter: blur(4px);
}

.swipe-badge-like {
  right: 20px;
  color: #22c55e;
  border-color: #22c55e;
  background: rgba(34,197,94,0.1);
  transform: rotate(15deg);
}

.swipe-badge-nope {
  left: 20px;
  color: #ef4444;
  border-color: #ef4444;
  background: rgba(239,68,68,0.1);
  transform: rotate(-15deg);
}

/* Drag hint */
.drag-hint {
  position: absolute;
  bottom: 12px;
  left: 50%;
  transform: translateX(-50%);
  color: #94a3b8;
  font-size: 13px;
  animation: hintPulse 2s ease-in-out infinite;
  white-space: nowrap;
}

@keyframes hintPulse {
  0%, 100% { opacity: 0.4; }
  50% { opacity: 0.8; }
}

/* Action bar */
.action-bar {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 12px 0 28px;
  position: relative;
  z-index: 2;
}

.act-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  border: none;
  background: transparent;
  cursor: pointer;
  transition: transform 0.2s cubic-bezier(0.34, 1.56, 0.64, 1);
  -webkit-tap-highlight-color: transparent;
}
.act-btn:active {
  transform: scale(0.88);
}

.act-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  transition: all 0.25s ease;
  position: relative;
}
.act-icon-wrap::after {
  content: '';
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.25s;
}
.act-btn:active .act-icon-wrap::after {
  opacity: 1;
}

.act-label {
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.5px;
}

/* 跳过 - 白色小圆 */
.act-skip .act-icon-wrap {
  width: 48px; height: 48px;
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(0,0,0,0.06), 0 0 0 1px rgba(0,0,0,0.04);
}
.act-icon-skip { color: #94a3b8; }
.act-icon-skip::after { box-shadow: 0 0 20px rgba(148,163,184,0.3); }
.act-skip:hover .act-icon-wrap { background: #fff; transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.08); }
.act-skip:hover .act-icon-skip { color: #64748b; }
.act-skip .act-label { color: #94a3b8; }

/* 刷新 */
.act-rewind .act-icon-wrap {
  width: 44px; height: 44px;
  background: linear-gradient(135deg, rgba(255,255,255,0.95), rgba(240,245,255,0.95));
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 12px rgba(59,130,246,0.08), 0 0 0 1px rgba(59,130,246,0.08);
}
.act-icon-rewind { color: #60a5fa; }
.act-icon-rewind::after { box-shadow: 0 0 15px rgba(96,165,250,0.25); }
.act-rewind:hover .act-icon-wrap {
  background: #fff;
  transform: rotate(-30deg);
  box-shadow: 0 4px 16px rgba(59,130,246,0.15), 0 0 0 2px rgba(59,130,246,0.12);
}
.act-rewind:hover .act-icon-rewind { color: #3b82f6; }
.act-rewind .act-label { color: #93bbfd; }

/* 加好友 - 最大最醒目 */
.act-like .act-icon-wrap {
  width: 64px; height: 64px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  box-shadow: 0 6px 24px rgba(59,130,246,0.4), 0 0 0 4px rgba(59,130,246,0.12);
}
.act-icon-like { color: #fff; }
.act-icon-like::after { box-shadow: 0 0 30px rgba(59,130,246,0.5); }
.act-like:hover .act-icon-wrap {
  transform: translateY(-3px);
  box-shadow: 0 10px 32px rgba(59,130,246,0.5), 0 0 0 6px rgba(59,130,246,0.15);
}
.act-like .act-label { color: #3b82f6; font-size: 13px; }

/* 打招呼 */
.act-greet .act-icon-wrap {
  width: 48px; height: 48px;
  background: linear-gradient(135deg, #8b5cf6, #6366f1);
  box-shadow: 0 4px 16px rgba(99,102,241,0.35), 0 0 0 2px rgba(99,102,241,0.1);
}
.act-icon-greet { color: #fff; }
.act-icon-greet::after { box-shadow: 0 0 25px rgba(139,92,246,0.4); }
.act-greet:hover .act-icon-wrap {
  transform: translateY(-2px);
  box-shadow: 0 6px 22px rgba(99,102,241,0.45), 0 0 0 3px rgba(99,102,241,0.15);
}
.act-greet .act-label { color: #7c3aed; }

/* Search transition */
.search-drop-enter-active, .search-drop-leave-active {
  transition: all 0.25s ease;
}
.search-drop-enter-from, .search-drop-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}
</style>
