<template>
  <div class="page">
    <div class="page-header">
      <h1>我的</h1>
      <button class="btn-icon" @click="logout" title="退出">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>
      </button>
    </div>

    <div v-if="!myId" class="guest-state">
      <div class="guest-card">
        <div class="guest-icon">🔐</div>
        <h2 class="guest-title">登录后查看更多</h2>
        <p class="guest-desc">登录后可以编辑资料、发布物品、查看好友</p>
        <router-link to="/login" class="btn btn-primary" style="display:inline-block;padding:12px 32px;border-radius:12px;text-decoration:none;font-size:16px;font-weight:600;margin-top:12px">立即登录</router-link>
        <div style="margin-top:12px;font-size:14px;color:#94a3b8">
          没有账号？<router-link to="/register">注册一个</router-link>
        </div>
      </div>
    </div>
    <div v-else-if="!user" class="loading-state"><div class="spinner"></div></div>

    <template v-if="user">
      <!-- Profile header - avatar + info -->
      <div class="profile-header card fade-up" @click="$router.push('/profile/edit')">
        <div v-if="bgUrl" class="profile-bg" :style="{ backgroundImage: 'url(' + bgUrl + ')' }"></div>
        <div class="profile-top" :class="{ 'has-bg': bgUrl }">
          <div class="planet-avatar-wrap">
            <svg class="orbit-ring" viewBox="0 0 100 100" width="100" height="100">
              <ellipse cx="50" cy="50" rx="40" ry="12" fill="none" stroke="url(#orbitGrad)" stroke-width="2" transform="rotate(-20, 50, 50)" opacity="0.5"/>
              <circle cx="50" cy="50" r="26" fill="url(#planetFill)" opacity="0.25"/>
              <defs>
                <linearGradient id="orbitGrad" x1="0" y1="0" x2="1" y2="1">
                  <stop offset="0%" stop-color="#38bdf8" stop-opacity="0"/>
                  <stop offset="40%" stop-color="#38bdf8" stop-opacity="0.9"/>
                  <stop offset="60%" stop-color="#818cf8" stop-opacity="0.9"/>
                  <stop offset="100%" stop-color="#818cf8" stop-opacity="0"/>
                </linearGradient>
                <radialGradient id="planetFill">
                  <stop offset="0%" stop-color="#60a5fa"/>
                  <stop offset="100%" stop-color="#1d4ed8"/>
                </radialGradient>
              </defs>
            </svg>
            <div class="avatar avatar-lg" :style="{ background: avatarColor }">
              <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
              <span v-else>{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</span>
            </div>
            <div class="edit-badge">
              <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="white" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </div>
          </div>
          <div class="profile-info">
            <div class="profile-name-row">
              <h2 class="profile-name">{{ user.nickname || user.username }}</h2>
              <span v-if="user.age" class="profile-age">{{ user.age }}</span>
              <span v-if="user.gender" :class="['tag', 'tag-sm', user.gender === '男' ? 'tag-male' : 'tag-female']">{{ user.gender }}</span>
            </div>
            <p class="profile-username">@{{ user.username }}</p>
            <p v-if="user.bio" class="profile-bio">{{ user.bio }}</p>
            <div class="profile-meta">
              <span v-if="user.location" class="meta-item">
                🎓 {{ user.location }}
              </span>
              <span v-if="user.email" class="meta-item">
                <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M8.5 4h7l4 4v10.5a1.5 1.5 0 0 1-1.5 1.5h-12A1.5 1.5 0 0 1 4.5 18V8l4-4z"/><path d="M8.5 4v4h7V4"/></svg>
                {{ user.email }}
              </span>
            </div>
          </div>
        </div>
        <div class="edit-hint">
          <span>点击编辑资料</span>
          <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="2"><polyline points="9 18 15 12 9 6"/></svg>
        </div>
      </div>

      <!-- Show on Planet toggle -->
      <div class="card planet-toggle">
        <div class="toggle-row">
          <div class="toggle-info">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#3b82f6" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
            <div>
              <div class="toggle-label">在星球展示</div>
              <div class="toggle-desc">愿意让其他人看到并匹配你</div>
            </div>
          </div>
          <button :class="['toggle-switch', { on: user.showOnPlanet !== false }]" @click="toggleShowOnPlanet">
            <div class="toggle-knob"></div>
          </button>
        </div>
      </div>

      <!-- === Post composer === -->
      <div class="post-composer card">
        <div v-if="!composerOpen" class="composer-row clickable" @click="composerOpen = true">
          <div class="avatar avatar-sm" :style="{ background: avatarColor }">
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
            <span v-else>{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</span>
          </div>
          <span class="composer-hint">发布交换物品...</span>
        </div>
        <div v-else>
          <div class="form-group">
            <label>物品名称 <span class="required">*</span></label>
            <input v-model="form.name" class="input" placeholder="例如：一台老式胶片相机" maxlength="30" />
          </div>
          <div class="form-group">
            <label>物品的故事 <span class="required">*</span></label>
            <textarea v-model="form.story" class="input story-input" placeholder="这件物品背后的故事是什么？" maxlength="500"></textarea>
            <span class="char-count">{{ form.story.length }}/500</span>
          </div>
          <div class="form-group">
            <label>想交换什么</label>
            <input v-model="form.want" class="input" placeholder="你希望换到什么类型的物品？" maxlength="50" />
          </div>
          <div class="form-group">
            <label>交换地点 <span class="required">*</span></label>
            <input v-model="form.location" class="input" placeholder="例如：图书馆门口、食堂三楼" maxlength="30" />
          </div>
          <div class="form-group">
            <label>物品照片</label>
            <div class="photo-upload" v-if="!form.imagePreview" @click="pickImage">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="#94a3b8" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>上传照片</span>
              <input type="file" accept="image/*" @change="onImageSelect" hidden ref="imgInput" />
            </div>
            <div v-else class="photo-preview-wrap">
              <img :src="form.imagePreview" class="photo-preview" />
              <button class="photo-remove" @click="removeImage">✕</button>
            </div>
          </div>
          <div class="form-actions">
            <button class="btn btn-ghost btn-sm" @click="composerOpen = false">取消</button>
            <button class="btn btn-primary btn-sm" @click="submitPost" :disabled="!canPublish || posting">
              <span v-if="posting" class="spinner-sm"></span>
              {{ posting ? '发布中...' : '发布物品' }}
            </button>
          </div>
        </div>
      </div>

      <!-- === Posts feed === -->
      <div class="posts-feed">
        <div v-if="postsLoading" class="loading-state" style="padding:30px"><div class="spinner"></div></div>
        <div v-else-if="posts.length === 0" class="empty-state" style="padding:30px">
          <div class="empty-icon">&#128172;</div>
          <div class="empty-text">还没发布过物品</div>
          <div class="empty-sub">发布第一个物品吧</div>
        </div>

        <div v-for="post in posts" :key="post.id" class="post-card fade-up">
          <div class="post-header">
            <div class="avatar avatar-sm" :style="{ background: avatarColor }">
            <img v-if="avatarUrl" :src="avatarUrl" class="avatar-img" />
            <span v-else>{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</span>
          </div>
            <div class="post-author">
              <span class="post-name">{{ post.itemName || '物品' }}</span>
              <span class="post-time">{{ formatPostTime(post.createTime) }}</span>
            </div>
            <button v-if="post.userId == myId" class="post-delete" @click="deletePost(post.id)" title="删除">🗑</button>
          </div>
          <div class="post-content">{{ post.itemStory || post.content }}</div>
          <div v-if="post.want || post.location" class="post-tags">
            <span v-if="post.want" class="tag-swap">🔄 {{ post.want }}</span>
            <span v-if="post.location" class="tag-loc">📍 {{ post.location }}</span>
          </div>
          <img v-if="post.imageUrl" :src="imgUrl(post.imageUrl)" class="post-image" @click="openImage(imgUrl(post.imageUrl))" />
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
  name: 'Profile',
  data() {
    return {
      user: null,
      myId: localStorage.getItem('userId'),
      composerOpen: false,
      form: { name: '', story: '', want: '', location: '', image: null, imagePreview: '' },
      posts: [],
      postsLoading: false,
      posting: false
    }
  },
  computed: {
    canPublish() { return this.form.name.trim() && this.form.story.trim() && this.form.location.trim() },
    avatarColor() { return COLORS[this.user?.id % COLORS.length] },
    avatarUrl() { return this.user?.avatar ? IMG_BASE + this.user.avatar : null },
    bgUrl() { return this.user?.background ? IMG_BASE + this.user.background : null }
  },
  mounted() { this.load(); this.loadPosts() },
  methods: {
    async load() {
      try {
        const res = await api.users.get(this.myId)
        this.user = res.data
      } catch (e) { console.error(e) }
    },
    showToast(msg) {
      const t = document.createElement('div'); t.className = 'toast'; t.textContent = msg
      document.body.appendChild(t)
      setTimeout(() => t.remove(), 2000)
    },
    logout() { localStorage.clear(); this.$router.push('/login') },
    async toggleShowOnPlanet() {
      const newVal = !(this.user.showOnPlanet !== false)
      try {
        await api.users.showOnPlanet(this.myId, newVal)
        this.user.showOnPlanet = newVal
        this.showToast(newVal ? '已开启星球展示' : '已关闭星球展示')
      } catch (e) { /* ignore */ }
    },
    async loadPosts() {
      this.postsLoading = true
      try {
        const res = await api.posts.list(this.myId)
        this.posts = res.data.map(p => {
          let d = p.content
          if (typeof d === "string") { try { d = JSON.parse(d) } catch { d = null } }
          if (d && typeof d === "object") {
            return { ...p, itemName: d.name || '物品', itemStory: d.story || '', want: d.want || '', location: d.location || '' }
          }
          return { ...p, itemName: '物品', itemStory: '', want: '', location: '' }
        })
      } catch (e) { console.error(e) }
      finally { this.postsLoading = false }
    },
    pickImage() { this.$refs.imgInput?.click() },
    onImageSelect(e) {
      const file = e.target.files[0]; if (!file) return
      this.form.image = file; this.form.imagePreview = URL.createObjectURL(file)
    },
    removeImage() {
      this.form.image = null; this.form.imagePreview = ''
      if (this.$refs.imgInput) this.$refs.imgInput.value = ''
    },
    async submitPost() {
      if (!this.canPublish || this.posting) return
      this.posting = true
      try {
        const content = JSON.stringify({ name: this.form.name.trim(), story: this.form.story.trim(), want: this.form.want.trim(), location: this.form.location.trim() })
        await api.posts.create(this.myId, content, this.form.image || undefined)
        this.form = { name: '', story: '', want: '', location: '', image: null, imagePreview: '' }
        this.composerOpen = false
        await this.loadPosts()
        this.showToast('物品发布成功！')
      } catch (e) { this.showToast(e.response?.data?.error || '发布失败') }
      finally { this.posting = false }
    },
    async deletePost(postId) {
      if (!confirm('确定删除这条牢骚？')) return
      try {
        await api.posts.delete(postId, this.myId)
        this.posts = this.posts.filter(p => p.id !== postId)
        this.showToast('已删除')
      } catch (e) { this.showToast(e.response?.data?.error || '删除失败') }
    },
    openImage(url) { window.open(url, '_blank') },
    imgUrl(url) { return url?.startsWith('/') ? IMG_BASE + url : url },
    formatPostTime(t) {
      if (!t) return ''
      const d = new Date(t); const now = new Date()
      const yesterday = new Date(now); yesterday.setDate(yesterday.getDate() - 1)
      if (d.toDateString() === now.toDateString()) {
        return d.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
      }
      if (d.toDateString() === yesterday.toDateString()) return '昨天'
      return d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' })
    }
  }
}
</script>

<style scoped>
/* ===== Profile Header ===== */
.profile-header {
  cursor: pointer; margin-bottom: 16px;
  transition: transform 0.2s, box-shadow 0.2s;
  position: relative; overflow: hidden;
}
.profile-bg {
  position: absolute; top: 0; left: 0; width: 100%; height: 160px;
  background-size: cover; background-position: center;
}
.profile-top {
  display: flex; gap: 16px; align-items: flex-start;
}
.profile-top.has-bg {
  padding-top: 120px;
  background: linear-gradient(180deg, transparent 0%, rgba(255,255,255,0.95) 40%);
  position: relative;
  z-index: 1;
}

/* Avatar */
.planet-avatar-wrap {
  position: relative; width: 80px; height: 80px;
  flex-shrink: 0;
}
.orbit-ring {
  position: absolute; top: -10px; left: -10px;
  width: 100px; height: 100px;
  animation: orbitSpin 8s linear infinite;
}
.planet-avatar-wrap .avatar {
  width: 64px; height: 64px; font-size: 26px;
  box-shadow: 0 0 30px rgba(59,130,246,0.4);
  border: 2px solid rgba(255,255,255,0.15);
  animation: avatarGlow 3s ease-in-out infinite;
  margin: 8px;
}
.avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
.edit-badge {
  position: absolute; bottom: 2px; right: 2px;
  width: 24px; height: 24px; border-radius: 50%;
  background: var(--primary-gradient); color: white;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(59,130,246,0.5);
  border: 2px solid white;
}
@keyframes orbitSpin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
@keyframes avatarGlow { 0%, 100% { box-shadow: 0 0 30px rgba(59,130,246,0.4); } 50% { box-shadow: 0 0 50px rgba(59,130,246,0.6), 0 0 70px rgba(59,130,246,0.2); } }

/* Info */
.profile-info { flex: 1; min-width: 0; padding-top: 4px; }
.profile-name-row { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.profile-name { font-size: 20px; font-weight: 700; color: var(--text); }
.profile-age { font-size: 18px; font-weight: 400; color: var(--text-secondary); }
.tag-sm { padding: 2px 8px; font-size: 11px; border-radius: 4px; }
.profile-username { color: var(--text-secondary); font-size: 13px; margin-top: 1px; }
.profile-bio { color: #64748b; font-size: 14px; margin-top: 6px; line-height: 1.5; }

.profile-meta {
  display: flex; flex-wrap: wrap; gap: 10px; margin-top: 8px;
}
.meta-item {
  display: inline-flex; align-items: center; gap: 4px;
  font-size: 13px; color: var(--text-secondary);
}
.meta-item svg { flex-shrink: 0; }

.edit-hint {
  display: flex; align-items: center; justify-content: flex-end; gap: 4px;
  margin-top: 10px; padding-top: 10px;
  border-top: 1px solid var(--border);
  font-size: 13px; color: var(--primary-light); opacity: 0.7;
}

/* ===== Post Composer ===== */
.post-composer { margin-top: 0; margin-bottom: 16px; }
.composer-row { display: flex; gap: 12px; align-items: flex-start; }
.composer-input {
  flex: 1; padding: 10px 14px; border: none; outline: none;
  background: transparent; font-family: inherit; font-size: 15px;
  color: var(--text); resize: none; border-radius: 12px;
  min-height: 50px; line-height: 1.5;
}
.composer-input::placeholder { color: #475569; }
.composer-input:focus { background: rgba(255,255,255,0.04); }
.composer-preview { position: relative; margin-top: 10px; display: inline-block; }
.preview-img { max-height: 180px; max-width: 100%; border-radius: 12px; object-fit: cover; border: 1px solid var(--border); }
.preview-remove {
  position: absolute; top: -8px; right: -8px;
  width: 24px; height: 24px; border-radius: 50%; border: none;
  background: rgba(239,68,68,0.9); color: white; cursor: pointer;
  font-size: 12px; display: flex; align-items: center; justify-content: center;
}
.composer-actions { display: flex; align-items: center; gap: 10px; margin-top: 10px; padding-top: 10px; border-top: 1px solid var(--border); }
.upload-btn { cursor: pointer; color: var(--text-secondary); padding: 4px; display: flex; transition: color 0.2s; }
.upload-btn:hover { color: var(--primary-light); }
.char-count { font-size: 12px; color: #475569; flex: 1; }
.spinner-sm { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.2); border-top-color: white; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }

/* ===== Posts Feed ===== */
.posts-feed { display: flex; flex-direction: column; gap: 10px; }
.post-card {
  background: var(--bg-card); border-radius: var(--radius); padding: 16px;
  backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: var(--shadow); position: relative;
}
.post-header { display: flex; align-items: flex-start; gap: 10px; margin-bottom: 10px; }
.post-author { flex: 1; display: flex; flex-direction: column; gap: 2px; }
.post-name { font-weight: 600; font-size: 15px; color: var(--text); }
.post-time { font-size: 12px; color: #475569; }
.post-card .avatar-img { width: 100%; height: 100%; border-radius: 50%; object-fit: cover; }
.post-delete {
  width: 30px; height: 30px; border-radius: 50%; border: none;
  background: transparent; color: #475569; cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  opacity: 0; transition: all 0.2s;
}
.post-card:hover .post-delete { opacity: 1; }
.post-delete:hover { background: rgba(239,68,68,0.15); color: #ef4444; }
.post-content { font-size: 15px; line-height: 1.6; color: var(--text); white-space: pre-wrap; word-break: break-word; }
.post-image { width: 100%; max-height: 300px; object-fit: cover; border-radius: 12px; margin-top: 10px; cursor: pointer; border: 1px solid var(--border); transition: opacity 0.2s; }
.post-image:hover { opacity: 0.9; }

/* Planet toggle */
.planet-toggle { margin-bottom: 16px; cursor: default; }
.planet-toggle:hover { transform: none; box-shadow: var(--shadow); }
.toggle-row { display: flex; align-items: center; justify-content: space-between; }
.toggle-info { display: flex; align-items: center; gap: 10px; }
.toggle-label { font-size: 15px; font-weight: 600; color: var(--text); }
.toggle-desc { font-size: 12px; color: var(--text-secondary); margin-top: 1px; }

.toggle-switch {
  width: 48px; height: 28px; border-radius: 14px; border: none;
  background: #cbd5e1; cursor: pointer; position: relative;
  transition: background 0.25s; flex-shrink: 0;
}
.toggle-switch.on { background: var(--primary-gradient); }
.toggle-knob {
  width: 22px; height: 22px; border-radius: 50%; background: white;
  position: absolute; top: 3px; left: 3px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
  transition: transform 0.25s;
}
.toggle-switch.on .toggle-knob { transform: translateX(20px); }

.composer-hint { color: #94a3b8; font-size: 15px; flex: 1; }
.clickable { cursor: pointer; }
.form-group { margin-bottom: 12px; }
.form-group label { display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; }
.required { color: #ef4444; }
.story-input { min-height: 70px; resize: vertical; }
.char-count { display: block; text-align: right; font-size: 11px; color: #94a3b8; margin-top: 4px; }
.photo-upload { display: flex; flex-direction: column; align-items: center; gap: 6px; padding: 20px; border: 2px dashed #e2e8f0; border-radius: 12px; cursor: pointer; color: #94a3b8; font-size: 13px; transition: all 0.2s; }
.photo-upload:hover { border-color: #f59e0b; color: #f59e0b; }
.photo-preview-wrap { position: relative; display: inline-block; }
.photo-preview { max-height: 150px; max-width: 100%; border-radius: 12px; object-fit: cover; }
.photo-remove { position: absolute; top: -8px; right: -8px; width: 24px; height: 24px; border-radius: 50%; border: none; background: rgba(239,68,68,0.9); color: white; cursor: pointer; font-size: 12px; }
.form-actions { display: flex; justify-content: flex-end; gap: 10px; margin-top: 8px; }
.post-tags { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 8px; }
.tag-swap { padding: 4px 8px; border-radius: 6px; background: rgba(245,158,11,0.1); color: #b45309; font-size: 12px; font-weight: 500; }
.tag-loc { padding: 4px 8px; border-radius: 6px; background: rgba(59,130,246,0.06); color: #3b82f6; font-size: 12px; font-weight: 500; }
.guest-state{display:flex;align-items:center;justify-content:center;min-height:60vh}.guest-card{text-align:center;padding:40px}.guest-icon{font-size:64px;margin-bottom:16px}.guest-title{font-size:22px;font-weight:700;color:var(--text);margin-bottom:8px}.guest-desc{font-size:14px;color:var(--text-secondary)}
</style>
