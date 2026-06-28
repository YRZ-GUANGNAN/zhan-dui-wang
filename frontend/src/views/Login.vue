<template>
  <div class="page page-center">
    <div class="login-wrap">
      <div class="login-header">
        <div class="logo-wrap">
          <svg viewBox="0 0 100 100" width="100" height="100" class="planet-svg">
            <defs>
              <radialGradient id="planetGrad" cx="40%" cy="40%">
                <stop offset="0%" stop-color="#60a5fa"/>
                <stop offset="50%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#1d4ed8"/>
              </radialGradient>
              <linearGradient id="ringGrad" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0"/>
                <stop offset="40%" stop-color="#38bdf8" stop-opacity="0.8"/>
                <stop offset="60%" stop-color="#818cf8" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#818cf8" stop-opacity="0"/>
              </linearGradient>
              <radialGradient id="planetGlow" cx="50%" cy="50%">
                <stop offset="60%" stop-color="rgba(59,130,246,0)" />
                <stop offset="100%" stop-color="rgba(59,130,246,0.15)" />
              </radialGradient>
            </defs>
            <circle cx="50" cy="50" r="28" fill="url(#planetGrad)"/>
            <ellipse cx="50" cy="50" rx="38" ry="10" fill="none" stroke="url(#ringGrad)" stroke-width="3" transform="rotate(-15, 50, 50)" class="orbit-ring"/>
            <circle cx="40" cy="42" r="3.5" fill="rgba(255,255,255,0.2)"/>
            <circle cx="57" cy="48" r="2.5" fill="rgba(255,255,255,0.15)"/>
            <circle cx="48" cy="58" r="2" fill="rgba(255,255,255,0.15)"/>
            <circle cx="55" cy="40" r="1.5" fill="rgba(255,255,255,0.1)"/>
            <circle cx="50" cy="50" r="40" fill="url(#planetGlow)" class="planet-glow"/>
          </svg>
        </div>
        <h1 class="soul-title">湛对网</h1>
        <p class="login-sub">遇见对的人</p>
      </div>

      <Transition name="msg-slide">
        <div v-if="error" class="msg-box msg-error shake">{{ error }}</div>
      </Transition>

      <div class="login-form">
        <div class="input-group">
          <label>用户名</label>
          <div class="input-icon-wrap">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            <input v-model="username" class="input" placeholder="用户名" @keyup.enter="login" autofocus />
          </div>
        </div>

        <div class="input-group">
          <label>密码</label>
          <div class="input-icon-wrap">
            <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="#64748b" stroke-width="1.5"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
            <input v-model="password" type="password" class="input" placeholder="密码" @keyup.enter="login" />
          </div>
        </div>

        <button class="btn btn-primary btn-block btn-lg" @click="login" :disabled="loading" style="margin-top:8px">
          <span v-if="loading" class="spinner-sm"></span>
          {{ loading ? '登录中...' : '登录' }}
        </button>

        <!-- <router-link to="/phone-login">📱 手机验证码登录</router-link> -->
        <div class="login-footer">
          没有账号？<router-link to="/register">注册一个</router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
export default {
  name: 'Login',
  data() {
    return { username: '', password: '', error: '', loading: false }
  },
  methods: {
    async login() {
      if (!this.username || !this.password) { this.error = '请输入用户名和密码'; return }
      this.loading = true; this.error = ''
      try {
        const res = await api.auth.login({ username: this.username, password: this.password })
        localStorage.setItem('token', res.data.token)
        localStorage.setItem('userId', res.data.userId)
        localStorage.setItem('username', res.data.username)
        this.$router.push('/square')
      } catch (e) {
        this.error = e.response?.data?.error || e.response?.data || '登录失败'
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
.login-header { text-align: center; margin-bottom: 40px; }
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
  font-size: 32px; font-weight: 700; letter-spacing: -0.5px;
  background: linear-gradient(135deg, #60a5fa, #38bdf8);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-top: 8px;
}
.login-sub { color: var(--text-secondary); margin-top: 6px; font-size: 15px; }
.input-icon-wrap {
  position: relative; display: flex; align-items: center;
}
.input-icon-wrap svg { position: absolute; left: 14px; pointer-events: none; }
.input-icon-wrap .input { padding-left: 44px; }
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
