<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <component :is="Component" />
    </router-view>
    <nav class="bottom-nav" v-if="$route.path !== '/'">
      <router-link to="/" class="nav-item" :class="{ active: $route.path === '/' }">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/></svg>
        <span>首页</span>
      </router-link>
      <router-link to="/square" class="nav-item" :class="{ active: $route.path === '/square' }">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 7h-6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2z"/><path d="M4 3h6a1 1 0 0 1 1 1v16a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V4a1 1 0 0 1 1-1z"/></svg>
        <span>忆涟</span>
      </router-link>
      <router-link to="/planet" class="nav-item" :class="{ active: $route.path === '/planet' }">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/></svg>
        <span>星球</span>
      </router-link>
      <router-link to="/chats" class="nav-item" :class="{ active: $route.path.startsWith('/chat') }">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
        <span>消息</span>
        <span v-if="unreadMessages > 0" class="badge-msg">{{ unreadMessages > 99 ? '99+' : unreadMessages }}</span>
      </router-link>
      <router-link to="/profile" class="nav-item" :class="{ active: $route.path === '/profile' }">
        <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
        <span>我的</span>
      </router-link>
      <div class="nav-glow" :style="navGlowStyle"></div>
    </nav>
  </div>
</template>

<script>
import { connect, onNotification, offNotification } from './api/websocket.js'
export default {
  name: 'App',
  data() { return { requestCount: 0, unreadMessages: 0, navIndex: 0 } },
  computed: {
    isLoggedIn() { return !!localStorage.getItem('token') },
    navGlowStyle() {
      const paths = ['/', '/square', '/planet', '/chats', '/profile']
      const idx = paths.findIndex(p => {
        if (p === '/') return this.$route.path === '/'
        return this.$route.path.startsWith(p)
      })
      if (idx < 0 && this.$route.path.startsWith('/chat/')) {
        return { transform: 'translateX(300%)', width: '20%', opacity: 1 }
      }
      return idx >= 0 ? { transform: `translateX(${idx * 100}%)`, width: '20%', opacity: 1 } : { opacity: 0 }
    }
  },
  watch: {
    '$route'(to) {
      if (this.isLoggedIn) { this.fetchRequestCount(); connect() }
      // Clear unread when entering chat
      if (to.path.startsWith('/chat/')) this.unreadMessages = 0
    }
  },
  mounted() {
    if (this.isLoggedIn) {
      this.fetchRequestCount()
      connect()
      this.setupNotification()
    }
    if (window.__wxjs_environment === 'miniprogram' || navigator.userAgent.indexOf('miniProgram') > -1) {
      if (location.search.indexOf('_t=') === -1) {
        var sep = location.search ? '&' : '?';
        location.replace(location.href + sep + '_t=' + Date.now());
      }
    }
  },
  beforeUnmount() { offNotification() },
  methods: {
    setupNotification() {
      onNotification((msg) => {
        this.unreadMessages++
        // Skip if already on this chat
        if (this.$route.path === '/chat/' + msg.sender.id) {
          this.unreadMessages = Math.max(0, this.unreadMessages - 1)
        }
      })
    },
    async fetchRequestCount() {
      try {
        const { default: api } = await import('./api/index.js')
        const res = await api.friends.requests(localStorage.getItem('userId'))
        this.requestCount = res.data.length
      } catch(e) { /* ignore */ }
    }
  }
}
</script>

<style>
:root {
  --primary: #3b82f6;
  --primary-light: #60a5fa;
  --primary-glow: rgba(59,130,246,0.15);
  --primary-gradient: linear-gradient(135deg, #3b82f6, #60a5fa);
  --text: #1e293b;
  --text-secondary: #94a3b8;
  --bg: #e0ecf8;
  --bg-card: #fff;
  --border: rgba(0,0,0,0.06);
  --shadow: 0 1px 3px rgba(0,0,0,0.04);
  --radius: 16px;
  --radius-sm: 12px;
  --safe-bottom: env(safe-area-inset-bottom, 0px);
  --nav-height: 56px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
  font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  background: #e0ecf8;
  color: var(--text); min-height: 100vh;
  padding-bottom: var(--safe-bottom);
  -webkit-font-smoothing: antialiased;
  overflow-x: hidden;
  overflow-y: auto;
}

/* Dark mode */
@media (prefers-color-scheme: dark) {
  :root {
    --text: #e2e8f0;
    --text-secondary: #94a3b8;
    --bg: #0f172a;
    --bg-card: #1e293b;
    --border: rgba(255,255,255,0.1);
    --shadow: 0 1px 3px rgba(0,0,0,0.3);
    color-scheme: dark;
  }
  body { background: #0f172a; }
  input, textarea, select { background: #1e293b; color: #e2e8f0; border-color: rgba(255,255,255,0.1); }
}

.page {
  max-width: 480px; margin: 0 auto; padding: 16px;
  position: relative; z-index: 1;
}
.fade-enter-active, .fade-leave-active {
  transition: all 0.25s ease;
}
.fade-enter-from { opacity: 0; transform: translateY(8px); }
.fade-leave-to { opacity: 0; transform: translateY(-8px); }

.slide-up-enter-active, .slide-up-leave-active {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.slide-up-enter-from { opacity: 0; transform: translateY(30px); }
.slide-up-leave-to { opacity: 0; transform: translateY(-20px); }

.slide-right-enter-active, .slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.slide-right-enter-from { opacity: 0; transform: translateX(60px); }
.slide-right-leave-to { opacity: 0; transform: translateX(-30px); }

.slide-left-enter-active, .slide-left-leave-active {
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
}
.slide-left-enter-from { opacity: 0; transform: translateX(-60px); }
.slide-left-leave-to { opacity: 0; transform: translateX(30px); }

.page {
  max-width: 480px; margin: 0 auto; padding: 16px;
  position: relative; z-index: 1;
  min-height: calc(100vh - var(--nav-height) - 28px);
  padding-bottom: calc(16px + var(--safe-bottom));
}

/* Header */
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  padding: 20px 0 16px; margin-bottom: 8px;
  position: relative; z-index: 2;
}
.page-header h1 {
  font-size: 22px; font-weight: 700; color: var(--text);
}
.page-header .btn-icon {
  width: 40px; height: 40px; border-radius: 50%; border: 1px solid var(--border);
  background: var(--bg-card); color: var(--text-secondary); font-size: 18px;
  cursor: pointer; display: flex; align-items: center; justify-content: center;
  backdrop-filter: blur(10px); transition: all 0.2s;
}
.page-header .btn-icon:hover {
  background: var(--bg-card-hover); color: var(--text);
  box-shadow: var(--shadow-glow);
}

/* Card */
.card {
  background: var(--bg-card); border-radius: var(--radius); padding: 16px;
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border);
  box-shadow: var(--shadow); margin-bottom: 12px;
}

/* Glass morphism helper */
.glass {
  background: var(--bg-card);
  backdrop-filter: blur(20px); -webkit-backdrop-filter: blur(20px);
  border: 1px solid var(--border);
}

/* Button */
.btn { min-height: 44px; min-width: 44px;
  display: inline-flex; align-items: center; justify-content: center; gap: 6px;
  padding: 12px 24px; border-radius: 12px; border: none; font-size: 15px;
  font-weight: 600; cursor: pointer; transition: all 0.25s;
  text-decoration: none; letter-spacing: 0.3px;
}
.btn:active { transform: scale(0.96); }
.btn-primary {
  background: var(--primary-gradient); color: white;
  box-shadow: 0 4px 15px var(--primary-glow);
  position: relative; overflow: hidden;
}
.btn-primary:hover { box-shadow: 0 6px 25px var(--primary-glow); transform: translateY(-1px); }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; box-shadow: none; }
.btn-primary::after {
  content: ''; position: absolute; top: 0; left: -100%; width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.15), transparent);
  transition: left 0.5s;
}
.btn-primary:hover::after { left: 100%; }
.btn-outline {
  background: transparent; color: var(--primary-light);
  border: 1.5px solid var(--primary-light);
}
.btn-outline:hover { background: rgba(59,130,246,0.1); }
.btn-ghost { background: transparent; color: var(--primary-light); padding: 8px 16px; }
.btn-ghost:hover { background: rgba(59,130,246,0.1); }
.btn-block { display: flex; width: 100%; }
.btn-sm { padding: 8px 16px; font-size: 13px; border-radius: 10px; }
.btn-lg { padding: 14px 32px; font-size: 16px; border-radius: 14px; }

/* Input */
.input-group { margin-bottom: 18px; }
.input-group label {
  display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600;
  color: var(--text-secondary); letter-spacing: 0.5px;
}
.input {
  width: 100%; padding: 14px 16px; border: 1.5px solid var(--border);
  border-radius: var(--radius-sm); font-size: 16px; outline: none;
  transition: all 0.25s; background: white; color: var(--text);
  font-family: inherit;
}
.input:focus {
  border-color: var(--primary-light);
  box-shadow: 0 0 0 3px var(--primary-glow);
  background: white;
}
.input::placeholder { color: #94a3b8; }
textarea.input { resize: vertical; min-height: 80px; }
select.input {
  appearance: none;
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 24 24' fill='none' stroke='%2394a3b8' stroke-width='2'%3E%3Cpolyline points='6 9 12 15 18 9'/%3E%3C/svg%3E");
  background-repeat: no-repeat; background-position: right 12px center; padding-right: 36px;
}
select.input option { background: white; color: var(--text); }

/* Avatar */
.avatar {
  width: 52px; height: 52px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  color: white; font-size: 22px; font-weight: 700; letter-spacing: 0;
  position: relative; overflow: hidden;
  box-shadow: 0 0 20px rgba(59,130,246,0.3);
}
.avatar-lg { width: 80px; height: 80px; font-size: 32px; }
.avatar-sm { width: 40px; height: 40px; font-size: 16px; }

/* Bottom Navigation */
.bottom-nav { position: fixed; bottom: 0; left: 0; right: 0; z-index: 100;
  position: fixed; bottom: 12px; left: 50%; transform: translateX(-50%);
  width: calc(100% - 32px); max-width: 440px; height: var(--nav-height);
  background: rgba(255,255,255,0.9);
  backdrop-filter: blur(25px); -webkit-backdrop-filter: blur(25px);
  border: 1px solid var(--border);
  border-radius: 22px;
  display: flex;
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  padding-bottom: 0; z-index: 100;
  position: relative; overflow: hidden;
}

.nav-glow {
  position: absolute; bottom: 0; left: 0;
  width: 20%; height: 3px;
  background: var(--primary-gradient);
  border-radius: 2px;
  transition: transform 0.3s cubic-bezier(0.22, 1, 0.36, 1), opacity 0.3s;
  box-shadow: 0 0 12px rgba(59,130,246,0.6), 0 0 25px rgba(59,130,246,0.3);
}

.nav-item {
  flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center;
  text-decoration: none; color: var(--text-secondary); font-size: 10px;
  gap: 2px; transition: all 0.3s; position: relative;
  font-weight: 500; letter-spacing: 0.2px;
  z-index: 1;
}
.nav-item svg { transition: all 0.3s; }
.nav-item.active { color: var(--primary-light); }
.nav-item.active svg {
  stroke: var(--primary-light);
  filter: drop-shadow(0 0 6px var(--primary-glow));
  animation: navPulse 2s ease-in-out infinite;
}
.nav-item:hover { color: var(--text); }

@keyframes navPulse {
  0%, 100% { filter: drop-shadow(0 0 6px var(--primary-glow)); }
  50% { filter: drop-shadow(0 0 12px var(--primary-glow), 0 0 20px rgba(59,130,246,0.3)); }
}

.badge-dot {
  position: absolute; top: 2px; right: calc(50% - 22px);
  background: #3b82f6; color: white; font-size: 10px; font-weight: 700;
  min-width: 18px; height: 18px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 8px rgba(59,130,246,0.4);
}

.badge-msg {
  position: absolute; top: 0px; right: calc(50% - 12px);
  background: #ef4444; color: white; font-size: 9px; font-weight: 700;
  min-width: 16px; height: 16px; border-radius: 8px;
  padding: 0 4px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 2px 6px rgba(239,68,68,0.5);
  z-index: 2;
}

/* User Row */
.user-row {
  display: flex; align-items: center; gap: 14px; padding: 10px 0;
  border-bottom: 1px solid var(--border); text-decoration: none; color: inherit;
}
.user-row:last-child { border-bottom: none; }
.user-info { flex: 1; min-width: 0; }
.user-info .name { font-weight: 600; font-size: 16px; display: flex; align-items: center; gap: 6px; color: var(--text); }
.user-info .detail { font-size: 13px; color: var(--text-secondary); margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Tags & Badges */
.tag {
  display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px;
  font-size: 12px; font-weight: 500;
}
.tag-male { background: rgba(59,130,246,0.1); color: #3b82f6; }
.tag-female { background: rgba(244,114,182,0.1); color: #f472b6; }
.tag-location { background: rgba(0,0,0,0.04); color: var(--text-secondary); }

/* Toast */
.toast {
  position: fixed; top: 50px; left: 50%; transform: translateX(-50%);
  background: rgba(255,255,255,0.95); color: var(--text); padding: 12px 24px;
  border-radius: 12px; font-size: 14px; font-weight: 500;
  z-index: 999; backdrop-filter: blur(20px); border: 1px solid var(--border);
  box-shadow: 0 8px 30px rgba(0,0,0,0.1);
  animation: toastIn 0.3s ease; max-width: 90%;
}
@keyframes toastIn { from { opacity: 0; transform: translateX(-50%) translateY(-20px); } to { opacity: 1; transform: translateX(-50%) translateY(0); } }

/* States */
.loading-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; color: var(--text-secondary); gap: 12px; }
.loading-state .spinner {
  width: 32px; height: 32px;
  border: 2px solid rgba(255,255,255,0.08);
  border-top-color: var(--primary-light);
  border-radius: 50%; animation: spin 0.8s linear infinite;
  box-shadow: 0 0 15px var(--primary-glow);
}
@keyframes spin { to { transform: rotate(360deg); } }
.empty-state { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 60px 20px; color: var(--text-secondary); gap: 8px; }
.empty-state .empty-icon { font-size: 48px; opacity: 0.6; }
.empty-state .empty-text { font-size: 15px; font-weight: 500; }
.empty-state .empty-sub { font-size: 13px; }

/* Animations */
@keyframes fadeUp { from { opacity: 0; transform: translateY(12px); } to { opacity: 1; transform: translateY(0); } }
.fade-up { animation: fadeUp 0.35s ease both; }
.fade-up:nth-child(2) { animation-delay: 0.05s; }
.fade-up:nth-child(3) { animation-delay: 0.1s; }
.fade-up:nth-child(4) { animation-delay: 0.15s; }
.fade-up:nth-child(5) { animation-delay: 0.2s; }

@keyframes glowPulse {
  0%, 100% { box-shadow: 0 0 10px var(--primary-glow); }
  50% { box-shadow: 0 0 25px var(--primary-glow), 0 0 40px rgba(59,130,246,0.2); }
}

/* Scale In */
@keyframes scaleIn { from { opacity: 0; transform: scale(0.9); } to { opacity: 1; transform: scale(1); } }
.scale-in { animation: scaleIn 0.3s ease both; }

/* Shake (for form errors) */
@keyframes shake {
  0%, 100% { transform: translateX(0); }
  10%, 30%, 50%, 70%, 90% { transform: translateX(-4px); }
  20%, 40%, 60%, 80% { transform: translateX(4px); }
}
.shake { animation: shake 0.5s ease both; }

/* Divider */
.divider { height: 1px; background: var(--border); margin: 16px 0; }

/* Error / Success */
.msg-box { padding: 12px 16px; border-radius: var(--radius-sm); font-size: 14px; font-weight: 500; margin-bottom: 16px; }
.msg-error { background: rgba(239,68,68,0.1); color: #fca5a5; border: 1px solid rgba(239,68,68,0.2); }
.msg-success { background: rgba(34,197,94,0.1); color: #86efac; border: 1px solid rgba(34,197,94,0.2); }

/* Scrollbar */
::-webkit-scrollbar { width: 3px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: var(--border); border-radius: 10px; }

</style>
