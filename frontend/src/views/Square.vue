<template>
  <div class="page">
    <div class="page-header">
      <h1>忆涟</h1>
      <button class="btn-icon" @click="refresh" title="刷新">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg>
      </button>
    </div>

    <!-- 规则 -->
    <div class="rules-bar">
      <span class="rule-tag">🚫 禁止金钱交易</span>
      <span class="rule-tag">📖 用故事交换</span>
      <span class="rule-tag">📍 只限线下</span>
    </div>

    <!-- 搜索 -->
    <div class="search-bar">
      <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="#94a3b8" stroke-width="2"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
      <input v-model="keyword" class="search-input" placeholder="搜索物品、地点..." @input="doSearch" />
      <button v-if="keyword" class="search-clear" @click="keyword='';load()">✕</button>
    </div>

    <!-- 发布入口 -->
    <div class="composer-bar" @click="composerOpen = true" v-if="!composerOpen">
      <div class="composer-avatar" :style="{ background: myGradient }">
        <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="rgba(255,255,255,0.9)" stroke-width="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
      </div>
      <span class="composer-hint">发布你想交换的物品...</span>
    </div>

    <!-- 发布表单 -->
    <div v-if="composerOpen" class="composer-card">
      <div class="form-group">
        <label>物品名称 *</label>
        <input v-model="form.name" class="input" placeholder="例如：一台老式胶片相机" maxlength="30" />
      </div>
      <div class="form-group">
        <label>物品的故事 *</label>
        <textarea v-model="form.story" class="input story-input" placeholder="它背后有什么故事？陪你走过怎样的时光..." maxlength="500"></textarea>
        <span class="char-count">{{ form.story.length }}/500</span>
      </div>
      <div class="form-row">
        <div class="form-group" style="flex:1">
          <label>分类</label>
          <select v-model="form.category" class="input">
            <option value="">选分类</option>
            <option>📚 书籍</option>
            <option>💻 数码</option>
            <option>🎧 影音</option>
            <option>👕 服饰</option>
            <option>🎮 游戏</option>
            <option>🏀 运动</option>
            <option>🎨 艺术</option>
            <option>🧸 其他</option>
          </select>
        </div>
        <div class="form-group" style="flex:1">
          <label>想交换什么</label>
          <input v-model="form.want" class="input" placeholder="想换什么？" maxlength="30" />
        </div>
      </div>
      <div class="form-group">
        <label>交换地点 *</label>
        <input v-model="form.location" class="input" placeholder="图书馆门口 / 食堂三楼" maxlength="30" />
      </div>
      <div class="form-group">
        <label>物品照片</label>
        <div class="photo-upload" v-if="!form.imagePreview" @click="pickImage">
          <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="#cbd5e1" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
          <span>上传照片</span>
          <input type="file" accept="image/*" @change="onImage" hidden ref="imgInput" />
        </div>
        <div v-else class="photo-preview-wrap">
          <img :src="form.imagePreview" class="photo-preview" />
          <button class="photo-remove" @click="removeImage">✕</button>
        </div>
      </div>
      <div class="form-actions">
        <button class="btn btn-ghost btn-sm" @click="composerOpen = false">取消</button>
        <button class="btn btn-primary btn-sm" @click="publish" :disabled="!canPublish || publishing">
          <span v-if="publishing" class="spinner-sm"></span>{{ publishing ? '发布中...' : '发布物品 ✨' }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-skeleton">
      <div v-for="i in 3" :key="i" class="skel-card">
        <div class="skel-img"></div>
        <div class="skel-body"><div class="skel-line w80"></div><div class="skel-line w60"></div><div class="skel-line w40"></div></div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else-if="items.length === 0" class="empty-state">
      <div class="empty-icon">📦</div>
      <div class="empty-text">还没有物品</div>
      <div class="empty-sub">来做第一个分享故事的人吧</div>
    </div>

    <!-- 物品列表 -->
    <div v-else class="items-grid" ref="itemsEl"
      @touchstart="touchStart" @touchmove="touchMove" @touchend="touchEnd">
      <div v-for="item in items" :key="item.id" class="item-card fade-up">
        <div class="item-image-wrap" @click="openDetail(item)">
          <img v-if="item.imageUrl" :src="imgUrl(item.imageUrl)" class="item-image" />
          <div v-else class="item-image-placeholder">{{ item.category?.charAt(0) || '📦' }}</div>
          <span v-if="item.category" class="item-cat-tag">{{ item.category }}</span>
        </div>
        <div class="item-body" @click="openDetail(item)">
          <div class="item-header">
            <div class="item-owner" @click.stop.prevent="goUser(item.userId)">
              <div class="owner-avatar-sm" :style="{ background: avatarColor(item.userId) }">
                <img v-if="item.user?.avatar" :src="imgUrl(item.user.avatar)" class="owner-avatar-img" />
                <span v-else>{{ (item.user?.nickname || '?').charAt(0) }}</span>
              </div>
              <span class="owner-name">{{ item.user?.nickname || '用户' }} ›</span>
            </div>
            <span class="item-time">{{ formatTime(item.createTime) }}</span>
            <button v-if="item.userId == myId" class="item-delete" @click.stop="deleteItem(item.id)">🗑</button>
          </div>
          <h3 class="item-name">{{ item.name }}</h3>
          <p class="item-story">{{ item.story }}</p>
          <div class="item-tags">
            <span v-if="item.want" class="item-tag want-tag">🔄 {{ item.want }}</span>
            <span v-if="item.location" class="item-tag loc-tag">📍 {{ item.location }}</span>
          </div>
          <div class="item-actions">
            <button class="act-item" :class="{ liked: likeMap[item.id]?.liked }" @click.stop="toggleWant(item.id, $event)">
              <svg viewBox="0 0 24 24" width="18" height="18" :fill="likeMap[item.id]?.liked ? '#8b5cf6' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
              <span>{{ likeMap[item.id]?.count || 0 }}</span>
            </button>
            <button class="act-item" @click.stop="toggleAsk(item.id)">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              <span>{{ commentCount[item.id] || 0 }}</span>
            </button>
            <button class="act-item chat-btn" @click.stop="chatWithOwner(item.userId)">
              <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <Transition name="modal">
      <div v-if="detailItem" class="modal-overlay" @click.self="detailItem = null">
        <div class="modal-card">
          <div class="modal-image" @click="openImage(detailItem.imageUrl)">
            <img v-if="detailItem.imageUrl" :src="imgUrl(detailItem.imageUrl)" />
            <div v-else class="modal-image-placeholder">{{ detailItem.category?.charAt(0) || '📦' }}</div>
          </div>
          <button class="modal-close" @click="detailItem = null">✕</button>
          <div class="modal-body">
            <div class="modal-owner" @click="goUser(detailItem.userId); detailItem = null">
              <div class="owner-avatar-sm" :style="{ background: avatarColor(detailItem.userId) }">
                <img v-if="detailItem.user?.avatar" :src="imgUrl(detailItem.user.avatar)" class="owner-avatar-img" />
                <span v-else>{{ (detailItem.user?.nickname || '?').charAt(0) }}</span>
              </div>
              <span class="owner-name">{{ detailItem.user?.nickname || '' }}</span>
            </div>
            <h2 class="modal-name">{{ detailItem.name }}</h2>
            <span v-if="detailItem.category" class="item-cat-tag" style="margin-bottom:10px;display:inline-block">{{ detailItem.category }}</span>
            <p class="modal-story">{{ detailItem.story }}</p>
            <div class="modal-tags">
              <span v-if="detailItem.want" class="item-tag want-tag">🔄 想换：{{ detailItem.want }}</span>
              <span v-if="detailItem.location" class="item-tag loc-tag">📍 {{ detailItem.location }}</span>
            </div>
            <div class="modal-actions">
              <button class="act-item" :class="{ liked: likeMap[detailItem.id]?.liked }" @click="toggleWant(detailItem.id)">
                <svg viewBox="0 0 24 24" width="18" height="18" :fill="likeMap[detailItem.id]?.liked ? '#f59e0b' : 'none'" stroke="currentColor" stroke-width="2"><path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/></svg>
                <span>{{ likeMap[detailItem.id]?.count || 0 }}</span>
              </button>
              <button class="act-item" @click="toggleAsk(detailItem.id)">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
                <span>{{ commentCount[detailItem.id] || 0 }}</span>
              </button>
              <button class="act-item chat-btn" @click="chatWithOwner(detailItem.userId); detailItem = null">
                <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Toast -->
    <Transition name="toast-fade">
      <div v-if="toast" class="toast-msg">{{ toast }}</div>
    </Transition>

    <!-- 飘心动画 -->
    <div v-for="heart in hearts" :key="heart.id" class="floating-heart" :style="{ left: heart.x + 'px', top: heart.y + 'px' }">💜</div>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'
const COLORS = ['#3b82f6','#60a5fa','#38bdf8','#818cf8','#6366f1','#2563eb','#0ea5e9','#7dd3fc']

export default {
  name: 'Square',
  data() {
    return {
      items: [], allItems: [], loading: true, detailItem: null, keyword: '', searchTimer: null,
      composerOpen: false, publishing: false,
      form: { name: '', story: '', category: '', want: '', location: '', image: null, imagePreview: '' },
      myId: localStorage.getItem('userId'),
      likeMap: {}, askData: {}, askInput: {}, askLoading: {}, openAsk: null, commentCount: {},
      toast: '', toastTimer: null,
      hearts: [], heartId: 0,
      touchY: 0, pulling: false
    }
  },
  computed: {
    myGradient() {
      const g = ['linear-gradient(135deg, #f59e0b, #ef4444)', 'linear-gradient(135deg, #3b82f6, #6366f1)', 'linear-gradient(135deg, #10b981, #06b6d4)']
      return g[Number(this.myId || 0) % g.length]
    },
    canPublish() { return this.form.name.trim() && this.form.story.trim() && this.form.location.trim() }
  },
  mounted() { this.load() },
  methods: {
    avatarColor(id) { return COLORS[id % COLORS.length] },
    imgUrl(url) { return url?.startsWith('/') ? IMG_BASE + url : url },
    openImage(url) { if (url) window.open(this.imgUrl(url), '_blank') },
    openDetail(item) { this.detailItem = item; this.openAsk = null },
    goUser(id) { this.$router.push('/user/' + id) },

    // Search
    doSearch() {
      clearTimeout(this.searchTimer)
      this.searchTimer = setTimeout(() => {
        if (!this.keyword) { this.load(); return }
        this.loading = true
        // Client-side filter
        const kw = this.keyword.toLowerCase()
        this.items = this.allItems ? this.allItems.filter(i =>
          (i.name && i.name.toLowerCase().includes(kw)) ||
          (i.story && i.story.toLowerCase().includes(kw)) ||
          (i.location && i.location.toLowerCase().includes(kw)) ||
          (i.want && i.want.toLowerCase().includes(kw))
        ) : []
        this.loading = false
      }, 300)
    },

    // Load
    async load() {
      this.loading = true
      try {
        const res = await api.posts.feed()
        this.items = res.data.map(p => this.parseItem(p))
        this.allItems = [...this.items]
        for (const item of this.items) { this.loadLikes(item.id); this.loadAskCount(item.id) }
      } catch (e) { console.error(e) }
      finally { this.loading = false }
    },
    refresh() { this.keyword = ''; this.load() },

    parseItem(post) {
      let d = post.content
      if (typeof d === 'string') { try { d = JSON.parse(d) } catch { d = null } }
      if (d && typeof d === 'object') {
        return { id: post.id, userId: post.userId, user: post.user, name: d.name || '未命名', story: d.story || '', category: d.category || '', want: d.want || '', location: d.location || '', imageUrl: post.imageUrl, createTime: post.createTime }
      }
      return { id: post.id, userId: post.userId, user: post.user, name: '物品', story: '', category: '', want: '', location: '', imageUrl: post.imageUrl, createTime: post.createTime }
    },

    // Publish
    pickImage() { this.$refs.imgInput?.click() },
    onImage(e) { const f = e.target.files[0]; if (!f) return; this.form.image = f; this.form.imagePreview = URL.createObjectURL(f) },
    removeImage() { this.form.image = null; this.form.imagePreview = ''; if (this.$refs.imgInput) this.$refs.imgInput.value = '' },
    async publish() {
      if (!this.canPublish || this.publishing) return
      this.publishing = true
      try {
        const content = JSON.stringify({ name: this.form.name.trim(), story: this.form.story.trim(), category: this.form.category, want: this.form.want.trim(), location: this.form.location.trim() })
        await api.posts.create(this.myId, content, this.form.image || undefined)
        this.form = { name: '', story: '', category: '', want: '', location: '', image: null, imagePreview: '' }
        this.composerOpen = false
        window.scrollTo({ top: 0, behavior: "smooth" })
        await this.load()
        this.showToast('✨ 物品发布成功！')
      } catch (e) { this.showToast('发布失败') }
      finally { this.publishing = false }
    },

    // Likes with heart animation
    async loadLikes(id) { try { const r = await api.posts.likes(id, this.myId); this.likeMap = { ...this.likeMap, [id]: r.data } } catch (e) {} },
    async toggleWant(id, event) {
      const c = this.likeMap[id]
      try {
        if (c?.liked) { const r = await api.posts.unlike(id, this.myId); this.likeMap = { ...this.likeMap, [id]: { liked: false, count: r.data.count } } }
        else {
          const r = await api.posts.like(id, this.myId); this.likeMap = { ...this.likeMap, [id]: { liked: true, count: r.data.count } }
          // Heart animation
          if (event) {
            const rect = event.target.getBoundingClientRect()
            this.spawnHeart(rect.left + rect.width / 2, rect.top)
          }
        }
      } catch (e) {}
    },
    spawnHeart(x, y) {
      const id = ++this.heartId
      this.hearts.push({ id, x, y })
      setTimeout(() => { this.hearts = this.hearts.filter(h => h.id !== id) }, 1000)
    },

    // Comments
    async loadAskCount(id) { try { const r = await api.posts.comments(id); this.askData = { ...this.askData, [id]: r.data }; this.commentCount = { ...this.commentCount, [id]: r.data.length } } catch (e) {} },
    async toggleAsk(id) {
      if (this.openAsk === id) { this.openAsk = null; return }
      this.openAsk = id
      if (!this.askData[id]) {
        this.askLoading = { ...this.askLoading, [id]: true }
        try { const r = await api.posts.comments(id); this.askData = { ...this.askData, [id]: r.data }; this.commentCount = { ...this.commentCount, [id]: r.data.length } } catch (e) {}
        finally { this.askLoading = { ...this.askLoading, [id]: false } }
      }
    },
    async submitAsk(id) {
      const t = this.askInput[id]?.trim(); if (!t) return; this.askInput = { ...this.askInput, [id]: '' }
      try { await api.posts.comment(id, this.myId, t); const r = await api.posts.comments(id); this.askData = { ...this.askData, [id]: r.data }; this.commentCount = { ...this.commentCount, [id]: r.data.length } } catch (e) { this.showToast('发送失败') }
    },

    // Other
    chatWithOwner(uid) { if (uid != this.myId) this.$router.push('/chat/' + uid) },
    async deleteItem(id) { if (!confirm('确定下架？')) return; try { await api.posts.delete(id, this.myId); this.items = this.items.filter(i => i.id !== id); this.showToast('已下架') } catch (e) { this.showToast('删除失败') } },
    showToast(msg) {
      this.toast = msg; clearTimeout(this.toastTimer)
      this.toastTimer = setTimeout(() => { this.toast = '' }, 2000)
    },

    // Pull to refresh
    touchStart(e) { this.touchY = e.touches[0].clientY },
    touchMove(e) {
      const dy = e.touches[0].clientY - this.touchY
      if (dy > 80 && this.$refs.itemsEl?.scrollTop <= 0 && !this.pulling) {
        this.pulling = true
        this.load().then(() => { this.pulling = false; this.showToast('已刷新') })
      }
    },
    touchEnd() { this.pulling = false },

    formatTime(t) {
      if (!t) return ''; const d = new Date(t), n = new Date(), diff = n - d, min = Math.floor(diff/60000), h = Math.floor(diff/3600000), day = Math.floor(diff/86400000)
      if (min < 1) return '刚刚'; if (min < 60) return min + '分钟前'; if (h < 24) return h + '小时前'; if (day < 7) return day + '天前'
      return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  }
}
</script>

<style scoped>
.rules-bar { display: flex; gap: 6px; margin-bottom: 12px; flex-wrap: wrap; }
.rule-tag { padding: 4px 10px; border-radius: 8px; background: rgba(245,158,11,0.1); color: #b45309; font-size: 11px; font-weight: 600; }

/* Search */
.search-bar { display: flex; align-items: center; gap: 8px; background: var(--bg-card); border-radius: 14px; padding: 0 14px; margin-bottom: 12px; border: 1px solid var(--border); backdrop-filter: blur(20px); }
.search-input { flex: 1; padding: 12px 0; border: none; outline: none; font-size: 15px; background: transparent; color: var(--text); }
.search-clear { background: none; border: none; color: #94a3b8; cursor: pointer; font-size: 14px; padding: 4px; }

/* Composer */
.composer-bar { display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: var(--bg-card); border-radius: 16px; margin-bottom: 14px; backdrop-filter: blur(20px); border: 1px solid var(--border); cursor: pointer; box-shadow: var(--shadow); }
.composer-avatar { width: 40px; height: 40px; border-radius: 50%; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.composer-hint { color: #94a3b8; font-size: 15px; }
.composer-card { background: var(--bg-card); border-radius: 16px; padding: 16px; margin-bottom: 14px; backdrop-filter: blur(20px); border: 1px solid rgba(245,158,11,0.2); box-shadow: var(--shadow); }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 5px; }
.form-row { display: flex; gap: 10px; }
.story-input { min-height: 70px; resize: vertical; }
.char-count { display: block; text-align: right; font-size: 11px; color: #94a3b8; margin-top: 2px; }
.photo-upload { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 20px; border: 2px dashed #e2e8f0; border-radius: 12px; cursor: pointer; color: #94a3b8; font-size: 13px; }
.photo-preview-wrap { position: relative; display: inline-block; }
.photo-preview { max-height: 150px; max-width: 100%; border-radius: 12px; object-fit: cover; }
.photo-remove { position: absolute; top: -6px; right: -6px; width: 22px; height: 22px; border-radius: 50%; border: none; background: rgba(239,68,68,0.9); color: #fff; cursor: pointer; font-size: 11px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }

/* Skeleton loading */
.loading-skeleton { display: flex; flex-direction: column; gap: 14px; }
.skel-card { background: var(--bg-card); border-radius: 18px; overflow: hidden; border: 1px solid var(--border); }
.skel-img { height: 180px; background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.skel-body { padding: 16px; display: flex; flex-direction: column; gap: 8px; }
.skel-line { height: 14px; border-radius: 7px; background: linear-gradient(90deg, #f0f0f0 25%, #e8e8e8 50%, #f0f0f0 75%); background-size: 200% 100%; animation: shimmer 1.5s infinite; }
.w80 { width: 80%; } .w60 { width: 60%; } .w40 { width: 40%; }
@keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }

/* Items */
.items-grid { display: flex; flex-direction: column; gap: 14px; }
.item-card { background: var(--bg-card); border-radius: 18px; overflow: hidden; border: 1px solid var(--border); box-shadow: 0 2px 12px rgba(0,0,0,0.04); cursor: pointer; transition: transform 0.15s; }
.item-card:active { transform: scale(0.985); }
.item-image-wrap { position: relative; }
.item-image { width: 100%; height: 200px; object-fit: cover; display: block; }
.item-image-placeholder { height: 160px; display: flex; align-items: center; justify-content: center; font-size: 48px; background: linear-gradient(135deg, #fef3c7, #fef9c3); }
.item-cat-tag { position: absolute; top: 10px; left: 10px; padding: 4px 10px; background: rgba(0,0,0,0.5); backdrop-filter: blur(8px); color: #fff; border-radius: 8px; font-size: 12px; font-weight: 500; }
.item-body { padding: 16px; }
.item-header { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
.item-owner { display: flex; align-items: center; gap: 8px; cursor: pointer; flex: 1; }
.owner-avatar-sm { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: #fff; font-size: 13px; font-weight: 700; overflow: hidden; flex-shrink: 0; }
.owner-avatar-img { width: 100%; height: 100%; object-fit: cover; }
.owner-name { font-size: 14px; font-weight: 600; color: var(--text); }
.item-time { font-size: 12px; color: #94a3b8; }
.item-delete { background: none; border: none; cursor: pointer; font-size: 14px; opacity: 0.4; padding: 4px; }
.item-delete:hover { opacity: 1; }
.item-name { font-size: 18px; font-weight: 700; color: var(--text); margin-bottom: 6px; }
.item-story { font-size: 14px; color: #64748b; line-height: 1.6; margin-bottom: 10px; }
.item-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 12px; }
.item-tag { display: inline-flex; align-items: center; gap: 3px; padding: 4px 10px; border-radius: 8px; font-size: 12px; font-weight: 500; }
.want-tag { background: rgba(245,158,11,0.1); color: #b45309; }
.loc-tag { background: rgba(59,130,246,0.06); color: #3b82f6; }
.item-actions { display: flex; gap: 6px; padding-top: 10px; border-top: 1px solid var(--border); }
.act-item { display: flex; align-items: center; gap: 4px; padding: 8px 12px; border: none; border-radius: 10px; background: transparent; color: #94a3b8; cursor: pointer; font-size: 13px; font-weight: 500; transition: all 0.15s; }
.act-item:hover { background: rgba(59,130,246,0.06); color: #3b82f6; }
.act-item.liked { color: #8b5cf6; }
.act-item.liked:hover { background: rgba(139,92,246,0.08); }
.chat-btn { margin-left: auto; }
.chat-btn:hover { background: rgba(99,102,241,0.08); color: #6366f1; }

/* Heart animation */
.floating-heart { position: fixed; font-size: 20px; pointer-events: none; z-index: 999; animation: heartUp 1s ease-out forwards; }
@keyframes heartUp { 0% { opacity: 1; transform: translateY(0) scale(1); } 100% { opacity: 0; transform: translateY(-80px) scale(0.5); } }

/* Toast */
.toast-msg { position: fixed; top: 80px; left: 50%; transform: translateX(-50%); padding: 10px 24px; background: rgba(0,0,0,0.8); color: #fff; border-radius: 20px; font-size: 14px; z-index: 999; backdrop-filter: blur(10px); }
.toast-fade-enter-active, .toast-fade-leave-active { transition: all 0.3s; }
.toast-fade-enter-from, .toast-fade-leave-to { opacity: 0; transform: translateX(-50%) translateY(-10px); }

/* Modal */
.modal-overlay { position: fixed; inset: 0; z-index: 200; background: rgba(0,0,0,0.5); backdrop-filter: blur(4px); display: flex; align-items: flex-end; justify-content: center; }
.modal-card { background: #fff; border-radius: 22px 22px 0 0; width: 100%; max-width: 480px; max-height: 90vh; overflow-y: auto; position: relative; animation: modalUp 0.3s cubic-bezier(0.22, 1, 0.36, 1); }
@keyframes modalUp { from { transform: translateY(100%); } to { transform: translateY(0); } }
.modal-close { position: absolute; top: 12px; right: 12px; z-index: 10; width: 30px; height: 30px; border-radius: 50%; border: none; background: rgba(0,0,0,0.5); color: #fff; font-size: 16px; cursor: pointer; display: flex; align-items: center; justify-content: center; }
.modal-image { width: 100%; min-height: 200px; max-height: 350px; overflow: hidden; cursor: pointer; }
.modal-image img { width: 100%; object-fit: cover; }
.modal-image-placeholder { height: 200px; display: flex; align-items: center; justify-content: center; font-size: 72px; background: linear-gradient(135deg, #fef3c7, #fef9c3); }
.modal-body { padding: 16px 20px 24px; }
.modal-owner { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; cursor: pointer; }
.modal-name { font-size: 22px; font-weight: 700; margin-bottom: 8px; color: var(--text); }
.modal-story { font-size: 15px; line-height: 1.7; color: #64748b; margin-bottom: 12px; }
.modal-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-bottom: 14px; }
.modal-actions { display: flex; gap: 8px; padding-top: 12px; border-top: 1px solid var(--border); }
.modal-enter-active, .modal-leave-active { transition: all 0.3s; }
.modal-enter-from, .modal-leave-to { opacity: 0; }
.modal-enter-from .modal-card, .modal-leave-to .modal-card { transform: translateY(100%); }

.spinner-sm { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.2); border-top-color: #fff; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>
