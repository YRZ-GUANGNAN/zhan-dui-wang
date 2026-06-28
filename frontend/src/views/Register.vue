<template>
  <div class="page page-center">
    <div class="login-wrap">
      <div class="login-header">
        <div class="logo-wrap">
          <svg viewBox="0 0 100 100" width="100" height="100" class="planet-svg">
            <defs>
              <radialGradient id="planetGrad2" cx="40%" cy="40%">
                <stop offset="0%" stop-color="#60a5fa"/>
                <stop offset="50%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#1d4ed8"/>
              </radialGradient>
              <linearGradient id="ringGrad2" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0"/>
                <stop offset="40%" stop-color="#38bdf8" stop-opacity="0.8"/>
                <stop offset="60%" stop-color="#818cf8" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#818cf8" stop-opacity="0"/>
              </linearGradient>
              <radialGradient id="planetGlow2" cx="50%" cy="50%">
                <stop offset="60%" stop-color="rgba(59,130,246,0)" />
                <stop offset="100%" stop-color="rgba(59,130,246,0.15)" />
              </radialGradient>
            </defs>
            <circle cx="50" cy="50" r="28" fill="url(#planetGrad2)"/>
            <ellipse cx="50" cy="50" rx="38" ry="10" fill="none" stroke="url(#ringGrad2)" stroke-width="3" transform="rotate(-15, 50, 50)" class="orbit-ring"/>
            <circle cx="40" cy="42" r="3.5" fill="rgba(255,255,255,0.2)"/>
            <circle cx="57" cy="48" r="2.5" fill="rgba(255,255,255,0.15)"/>
            <circle cx="48" cy="58" r="2" fill="rgba(255,255,255,0.15)"/>
            <circle cx="55" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/>
            <circle cx="50" cy="50" r="40" fill="url(#planetGlow2)" class="planet-glow"/>
          </svg>
        </div>
        <h1 class="soul-title">注册</h1>
        <p class="login-sub">填完资料直接开始找</p>
      </div>

      <Transition name="msg-slide">
        <div v-if="error" class="msg-box msg-error shake">{{ error }}</div>
      </Transition>

      <div class="login-form">
        <div class="input-group">
          <label>用户名</label>
          <input v-model="form.username" class="input" placeholder="3-20位字符" />
        </div>
        <div class="input-group">
          <label>密码</label>
          <input v-model="form.password" type="password" class="input" placeholder="至少6位" />
        </div>
        <div class="input-group">
          <label>确认密码</label>
          <input v-model="form.confirmPassword" type="password" class="input" placeholder="再次输入密码" />
        </div>
        <div class="input-group">
          <label>邮箱</label>
          <input v-model="form.email" class="input" placeholder="用于找回密码，可不填自动生成" />
        </div>
        <div class="input-group">
          <label>昵称（选填）</label>
          <input v-model="form.nickname" class="input" placeholder="真名或外号" />
        </div>

        <button class="btn btn-primary btn-block btn-lg" @click="register" :disabled="loading" style="margin-top:8px">
          <span v-if="loading" class="spinner-sm"></span>
          {{ loading ? '注册中...' : '注册' }}
        </button>

        <div class="login-footer">
          已有账号？<router-link to="/login">直接登录</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
export default {
  name: 'Register',
  data() {
    return { form: { username: '', password: '', confirmPassword: '', email: '', nickname: '' }, error: '', loading: false }
  },
  methods: {
    async register() {
      if (!this.form.username || !this.form.password || !this.form.confirmPassword) {
        this.error = '请填写必填项'; return
      }
      this.loading = true; this.error = ''
      if (this.form.password !== this.form.confirmPassword) { this.error = '两次密码不一致'; this.loading = false; return }
      // Auto-generate email if not provided or not valid email format
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
      if (!this.form.email || !emailRegex.test(this.form.email)) {
        this.form.email = `user${Date.now()}@zhandui.com`
      }
      try {
        const res = await api.auth.register(this.form)
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('userId', res.data.userId)
        localStorage.setItem('username', res.data.username)
        this.$router.push('/square')
      } catch (e) {
        this.error = e.response?.data?.error || e.response?.data || '注册失败'
      } finally { this.loading = false }
    }
  }
}
</script>

<style scoped>
.page-center {
  display: flex; align-items: center; justify-content: center;
  min-height: 100vh; padding: 0;
}
.login-wrap {
  width: 100%; max-width: 380px; padding: 0 24px;
  position: relative; z-index: 1;
}
.login-header { text-align: center; margin-bottom: 36px; }
.logo-wrap { margin-bottom: 16px; position: relative; display: inline-block; }
.planet-svg {
  width: 100px; height: 100px;
  filter: drop-shadow(0 0 40px rgba(59,130,246,0.4));
  animation: planetFloat 3s ease-in-out infinite;
}
.orbit-ring {
  transform-origin: center;
  animation: orbitSpin 8s linear infinite;
}
.planet-glow {
  animation: glowPulse 3s ease-in-out infinite;
}
@keyframes orbitSpin {
  from { transform: rotate(-15deg) rotate(0deg); }
  to { transform: rotate(-15deg) rotate(360deg); }
}
@keyframes planetFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}
@keyframes glowPulse {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}
.soul-title {
  font-size: 32px; font-weight: 700; letter-spacing: -0.5px; text-align: center;
  background: linear-gradient(135deg, #60a5fa, #38bdf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
}
.login-sub { color: var(--text-secondary); margin-top: 6px; font-size: 15px; text-align: center; }
.login-footer { text-align: center; margin-top: 24px; font-size: 14px; color: var(--text-secondary); }
.login-footer a { color: var(--primary-light); text-decoration: none; font-weight: 600; }
.login-footer a:hover { text-decoration: underline; }
.spinner-sm { display: inline-block; width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.2); border-top-color: white; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.msg-slide-enter-active, .msg-slide-leave-active {
  transition: all 0.3s ease;
}
.msg-slide-enter-from { opacity: 0; transform: translateY(-10px); }
.msg-slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
