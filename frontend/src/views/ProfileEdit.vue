<template>
  <div class="page page-edit">
    <div class="edit-header">
      <button class="edit-back" @click="$router.back()">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
      </button>
      <h1>编辑资料</h1>
      <button class="edit-save" @click="save" :disabled="saving">
        <span v-if="saving" class="spinner-sm"></span>
        {{ saving ? '保存中' : '保存' }}
      </button>
    </div>

    <div v-if="!user" class="loading-state"><div class="spinner"></div></div>

    <template v-if="user">
      <!-- Avatar section -->
      <div class="edit-avatar-section">
        <div class="edit-avatar-wrap" @click="triggerAvatarUpload">
          <img v-if="avatarUrl" :src="avatarUrl" class="edit-avatar-img" />
          <div v-else class="avatar avatar-lg" :style="{ background: avatarColor }">{{ user.nickname?.charAt(0) || user.username.charAt(0) }}</div>
          <div class="avatar-overlay">
            <svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="white" stroke-width="2"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>
          </div>
          <div v-if="uploading" class="avatar-uploading">
            <div class="spinner-sm-light"></div>
          </div>
        </div>
        <span class="edit-avatar-hint">点击更换头像</span>
        <input type="file" ref="avatarInput" accept="image/*" @change="onAvatarSelect" hidden />
      </div>

      <!-- Background section -->
      <div class="card edit-card" style="margin-bottom:16px">
        <div class="edit-avatar-section" style="padding:16px 0">
          <div class="edit-background-wrap" @click="triggerBgUpload">
            <img v-if="bgUrl" :src="bgUrl" class="edit-bg-img" />
            <div v-else class="edit-bg-placeholder">
              <svg viewBox="0 0 24 24" width="28" height="28" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
              <span>设置背景图</span>
            </div>
            <div v-if="bgUploading" class="avatar-uploading"><div class="spinner-sm-light"></div></div>
          </div>
          <span class="edit-avatar-hint">用于星球卡片背景（建议 4:3 比例）</span>
          <input type="file" ref="bgInput" accept="image/*" @change="onBgSelect" hidden />
        </div>
      </div>

      <!-- Edit form -->
      <div class="card edit-card">
        <div class="edit-field" v-for="field in fields" :key="field.key">
          <label class="edit-label">{{ field.label }}</label>
          <input v-if="field.type === 'text'" v-model="form[field.key]" class="edit-input" :placeholder="field.placeholder" />
          <input v-else-if="field.type === 'number'" v-model.number="form[field.key]" class="edit-input" type="number" :placeholder="field.placeholder" />
          <select v-else-if="field.type === 'select'" v-model="form[field.key]" class="edit-input">
            <option value="">请选择</option>
            <option v-for="opt in field.options" :key="opt" :value="opt">{{ opt }}</option>
          </select>
          <textarea v-else-if="field.type === 'textarea'" v-model="form[field.key]" class="edit-input edit-textarea" :placeholder="field.placeholder" rows="3"></textarea>
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
  name: 'ProfileEdit',
  data() {
    return {
      user: null, form: {}, saving: false, uploading: false, bgUploading: false,
      fields: [
        { key: 'nickname', label: '昵称', type: 'text', placeholder: '输入昵称' },
        { key: 'age', label: '年龄', type: 'number', placeholder: '输入年龄' },
        { key: 'gender', label: '性别', type: 'select', options: ['男', '女'] },
        { key: 'location', label: '院系', type: 'text', placeholder: '如: 计算机学院' },
        { key: 'email', label: '微信号', type: 'text', placeholder: '微信号（选填）' },
        { key: 'bio', label: '签名', type: 'textarea', placeholder: '介绍一下自己...' }
      ]
    }
  },
  computed: {
    avatarColor() { return COLORS[this.user?.id % COLORS.length] },
    avatarUrl() { return this.user?.avatar ? IMG_BASE + this.user.avatar : null },
    bgUrl() { return this.user?.background ? IMG_BASE + this.user.background : null }
  },
  mounted() { this.load() },
  methods: {
    async load() {
      try {
        const res = await api.users.get(localStorage.getItem('userId'))
        this.user = res.data
        this.form = { ...res.data }
      } catch (e) { console.error(e) }
    },
    triggerAvatarUpload() {
      this.$refs.avatarInput.click()
    },
    async onAvatarSelect(e) {
      const file = e.target.files[0]
      if (!file) return
      this.uploading = true
      try {
        const res = await api.users.avatar(localStorage.getItem('userId'), file)
        this.user = res.data.user
        if (res.data.avatar) this.showToast('头像已更新')
      } catch (e) {
        this.showToast(e.response?.data?.error || '头像上传失败')
      } finally {
        this.uploading = false
        this.$refs.avatarInput.value = ''
      }
    },
    triggerBgUpload() { this.$refs.bgInput.click() },
    async onBgSelect(e) {
      const file = e.target.files[0]
      if (!file) return
      this.bgUploading = true
      try {
        const res = await api.users.background(localStorage.getItem('userId'), file)
        this.user = res.data.user
        this.showToast('背景已更新')
      } catch (e) {
        this.showToast(e.response?.data?.error || '背景上传失败')
      } finally {
        this.bgUploading = false
        this.$refs.bgInput.value = ''
      }
    },
    async save() {
      this.saving = true
      try {
        const res = await api.users.update(localStorage.getItem('userId'), {
          nickname: this.form.nickname, age: this.form.age, gender: this.form.gender,
          location: this.form.location, email: this.form.email, bio: this.form.bio
        })
        this.user = res.data
        this.showToast('保存成功')
        this.$router.back()
      } catch (e) {
        this.showToast(e.response?.data?.error || '保存失败')
      } finally { this.saving = false }
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
.page-edit { padding: 0 !important; }
.edit-header {
  display: flex; align-items: center; gap: 12px;
  padding: 12px 16px; position: sticky; top: 0; z-index: 10;
  background: rgba(255,255,255,0.9); backdrop-filter: blur(20px);
  border-bottom: 1px solid var(--border);
}
.edit-back { background: none; border: none; cursor: pointer; padding: 4px; color: var(--text); display: flex; }
.edit-header h1 { flex: 1; font-size: 18px; font-weight: 600; color: var(--text); }
.edit-save {
  padding: 8px 20px; border-radius: 20px; border: none;
  background: var(--primary-gradient); color: white; font-size: 14px;
  font-weight: 600; cursor: pointer; transition: all 0.2s;
  box-shadow: 0 4px 12px var(--primary-glow);
}
.edit-save:active { transform: scale(0.96); }
.edit-save:disabled { opacity: 0.5; }
.spinner-sm { display: inline-block; width: 14px; height: 14px; border: 2px solid rgba(255,255,255,0.2); border-top-color: white; border-radius: 50%; animation: spin 0.6s linear infinite; vertical-align: middle; }
@keyframes spin { to { transform: rotate(360deg); } }

.edit-avatar-section {
  display: flex; flex-direction: column; align-items: center;
  padding: 24px 0 20px;
}
.edit-avatar-wrap {
  position: relative; cursor: pointer;
}
.avatar-lg {
  width: 80px; height: 80px; font-size: 32px;
  box-shadow: 0 0 30px rgba(59,130,246,0.4);
  border: 2px solid rgba(255,255,255,0.15);
}
.edit-avatar-img {
  width: 80px; height: 80px; border-radius: 50%; object-fit: cover;
  box-shadow: 0 0 30px rgba(59,130,246,0.4);
  border: 2px solid rgba(255,255,255,0.15);
}
.avatar-overlay {
  position: absolute; inset: 0; border-radius: 50%;
  background: rgba(0,0,0,0.45); display: flex; align-items: center;
  justify-content: center; opacity: 0; transition: opacity 0.25s;
}
.edit-avatar-wrap:hover .avatar-overlay { opacity: 1; }
.avatar-uploading {
  position: absolute; inset: 0; border-radius: 50%;
  background: rgba(0,0,0,0.6); display: flex; align-items: center;
  justify-content: center;
}
.spinner-sm-light {
  width: 22px; height: 22px; border: 2px solid rgba(255,255,255,0.2);
  border-top-color: white; border-radius: 50%;
  animation: spin 0.6s linear infinite;
}
.edit-avatar-hint { font-size: 13px; color: var(--text-secondary); margin-top: 8px; }

.edit-background-wrap {
  width: 100%; height: 150px; border-radius: 12px; overflow: hidden;
  cursor: pointer; position: relative;
  border: 2px dashed var(--border);
  display: flex; align-items: center; justify-content: center;
}
.edit-bg-img { width: 100%; height: 100%; object-fit: cover; }
.edit-bg-placeholder {
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  color: #94a3b8; font-size: 14px;
}
.edit-bg-placeholder:hover { color: var(--primary-light); }

.edit-card { margin: 0 16px 24px; }
.edit-field { padding: 14px 0; border-bottom: 1px solid var(--border); }
.edit-field:last-child { border-bottom: none; }
.edit-label { display: block; font-size: 13px; font-weight: 600; color: var(--text-secondary); margin-bottom: 6px; letter-spacing: 0.5px; }
.edit-input { width: 100%; padding: 10px 0; border: none; outline: none; background: transparent; font-family: inherit; font-size: 16px; color: var(--text); }
.edit-input::placeholder { color: #475569; }
.edit-input:focus { color: var(--primary-light); }
.edit-textarea { resize: vertical; min-height: 60px; }
select.edit-input { appearance: none; background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E"); background-repeat: no-repeat; background-position: right 0 center; padding-right: 24px; }
select.edit-input option { background: white; color: var(--text); }
</style>
