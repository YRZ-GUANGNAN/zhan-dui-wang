<template>
  <div class="page page-center">
    <div class="login-wrap">
      <div class="login-header">
        <div class="logo-wrap">
          <svg viewBox="0 0 100 100" width="100" height="100" class="planet-svg">
            <defs>
              <radialGradient id="planetGrad3" cx="40%" cy="40%">
                <stop offset="0%" stop-color="#60a5fa"/>
                <stop offset="50%" stop-color="#3b82f6"/>
                <stop offset="100%" stop-color="#1d4ed8"/>
              </radialGradient>
              <linearGradient id="ringGrad3" x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stop-color="#38bdf8" stop-opacity="0"/>
                <stop offset="40%" stop-color="#38bdf8" stop-opacity="0.8"/>
                <stop offset="60%" stop-color="#818cf8" stop-opacity="0.8"/>
                <stop offset="100%" stop-color="#818cf8" stop-opacity="0"/>
              </linearGradient>
            </defs>
            <circle cx="50" cy="50" r="28" fill="url(#planetGrad3)"/>
            <ellipse cx="50" cy="50" rx="38" ry="10" fill="none" stroke="url(#ringGrad3)" stroke-width="3" transform="rotate(-15, 50, 50)" class="orbit-ring"/>
          </svg>
        </div>
        <h1 class="soul-title">手机登录</h1>
        <p class="login-sub">输入手机号获取验证码</p>
      </div>

      <Transition name="msg-slide">
        <div v-if="error" class="msg-box msg-error shake">{{ error }}</div>
        <div v-if="success" class="msg-box msg-success">{{ success }}</div>
      </Transition>

      <!-- 步骤1: 输入手机号 -->
      <div v-if="step === 1" class="login-form">
        <div class="input-group">
          <label>手机号</label>
          <input v-model="phone" class="input" placeholder="请输入手机号" type="tel" maxlength="11" />
        </div>
        <button class="btn btn-primary btn-block btn-lg" @click="sendCode" :disabled="sending || !phone" style="margin-top:8px">
          <span v-if="sending" class="spinner-sm"></span>
          {{ sending ? '发送中...' : '获取验证码' }}
        </button>
      </div>

      <!-- 步骤2: 输入验证码 -->
      <div v-else class="login-form">
        <div class="input-group">
          <label>手机号</label>
          <div class="phone-display">{{ phone }}</div>
        </div>
        <div class="input-group">
          <label>验证码</label>
          <input v-model="code" class="input code-input" placeholder="6位验证码" type="tel" maxlength="6" inputmode="numeric" autofocus />
        </div>

        <div class="countdown-row">
          <span v-if="countdown > 0" class="countdown">{{ countdown }}秒后可重发</span>
          <button v-else class="btn-resend" @click="sendCode">重新发送</button>
        </div>

        <button class="btn btn-primary btn-block btn-lg" @click="verifyAndLogin" :disabled="verifying || code.length < 4" style="margin-top:8px">
          <span v-if="verifying" class="spinner-sm"></span>
          {{ verifying ? '验证中...' : '登录/注册' }}
        </button>

        <div class="login-footer">
          <button class="btn-ghost-text" @click="step = 1; code = ''">更换手机号</button>
        </div>
      </div>

      <div class="login-footer">
        <router-link to="/login">密码登录</router-link>
        &nbsp;|&nbsp;
        <router-link to="/register">注册账号</router-link>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PhoneLogin',
  data() {
    return {
      step: 1,
      phone: '',
      code: '',
      error: '',
      success: '',
      sending: false,
      verifying: false,
      countdown: 0,
      timer: null
    }
  },
  beforeUnmount() {
    if (this.timer) clearInterval(this.timer)
  },
  methods: {
    async sendCode() {
      if (!this.phone || this.phone.length < 11) {
        this.error = '请输入正确的手机号'; return
      }
      this.sending = true; this.error = ''; this.success = ''

      try {
        const res = await fetch('/api/auth/send-code', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone: this.phone })
        })
        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.detail || '发送失败')
        }
        this.success = '验证码已发送（测试模式：查看手机页面提示）'
        this.step = 2
        this.startCountdown()
      } catch (e) {
        this.error = e.message || '发送失败，请重试'
      } finally {
        this.sending = false
      }
    },

    startCountdown() {
      this.countdown = 60
      this.timer = setInterval(() => {
        this.countdown--
        if (this.countdown <= 0) {
          clearInterval(this.timer)
        }
      }, 1000)
    },

    async verifyAndLogin() {
      if (!this.code || this.code.length < 4) {
        this.error = '请输入验证码'; return
      }
      this.verifying = true; this.error = ''

      try {
        // 1. 先验证验证码
        const verifyRes = await fetch('/api/auth/phone-verify', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ phone: this.phone, code: this.code })
        })
        if (!verifyRes.ok) {
          const data = await verifyRes.json()
          throw new Error(data.detail || '验证失败')
        }

        // 2. 尝试用手机号登录
        const { default: api } = await import('../api/index.js')
        try {
          const loginRes = await api.auth.login({
            username: this.phone,
            password: this.code
          })
          this.saveAndGo(loginRes.data)
          return
        } catch (e) {
          // 登录失败，尝试注册
          if (e.response?.status === 401 || e.response?.status === 400) {
            try {
              const regRes = await api.auth.register({
                username: this.phone,
                password: this.code,
                email: `${this.phone}@phone.zhandui.com`,
                nickname: '用户' + this.phone.slice(-4)
              })
              this.saveAndGo(regRes.data)
              return
            } catch (e2) {
              // 可能已注册但密码不对，用验证码登录就是密码
              const respData = e2.response?.data
              if (typeof respData === 'string' && respData.includes('已存在')) {
                throw new Error('该手机号已注册，密码错误')
              }
              throw new Error(respData?.error || respData || '注册失败')
            }
          }
          throw e
        }
      } catch (e) {
        this.error = e.message || e.response?.data?.error || '登录失败'
      } finally {
        this.verifying = false
      }
    },

    saveAndGo(data) {
      localStorage.setItem('token', data.token)
      localStorage.setItem('userId', data.userId)
      localStorage.setItem('username', data.username)
      this.$router.push('/square')
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
@keyframes orbitSpin { from { transform: rotate(-15deg) rotate(0deg); } to { transform: rotate(-15deg) rotate(360deg); } }
@keyframes planetFloat {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
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

.phone-display {
  font-size: 20px; font-weight: 700; color: var(--primary-light);
  padding: 12px 0; letter-spacing: 2px;
}
.code-input {
  font-size: 24px; letter-spacing: 8px; text-align: center; font-weight: 700;
}
.countdown-row { text-align: center; margin: 8px 0; }
.countdown { font-size: 13px; color: #94a3b8; }
.btn-resend {
  background: none; border: none; color: var(--primary-light);
  font-size: 14px; font-weight: 600; cursor: pointer; padding: 4px 8px;
}
.btn-ghost-text {
  background: none; border: none; color: var(--text-secondary);
  font-size: 13px; cursor: pointer; text-decoration: underline;
}
.spinner-sm { display: inline-block; width: 18px; height: 18px; border: 2px solid rgba(255,255,255,0.2); border-top-color: white; border-radius: 50%; animation: spin 0.6s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.msg-slide-enter-active, .msg-slide-leave-active { transition: all 0.3s ease; }
.msg-slide-enter-from { opacity: 0; transform: translateY(-10px); }
.msg-slide-leave-to { opacity: 0; transform: translateY(-10px); }
</style>
