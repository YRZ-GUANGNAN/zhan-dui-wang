<template>
  <div class="welcome">
    <div class="hero">
      <div class="logo">
        <svg viewBox="0 0 80 80" width="80" height="80">
          <defs>
            <radialGradient id="hg" cx="40%" cy="35%"><stop offset="0%" stop-color="#60a5fa"/><stop offset="100%" stop-color="#1d4ed8"/></radialGradient>
          </defs>
          <circle cx="40" cy="40" r="28" fill="url(#hg)"/>
          <ellipse cx="40" cy="40" rx="36" ry="9" fill="none" stroke="rgba(59,130,246,0.3)" stroke-width="2" transform="rotate(-15,40,40)"/>
          <circle cx="32" cy="34" r="3" fill="rgba(255,255,255,0.25)"/>
          <circle cx="46" cy="38" r="2" fill="rgba(255,255,255,0.2)"/>
        </svg>
      </div>
      <h1>交换故事<br>遇见同频的人</h1>
      <p class="sub">每一件物品，都藏着一段故事</p>
    </div>

    <div class="split">
      <router-link to="/square" class="card yilian">
        <div class="card-icon">📦</div>
        <h2>忆涟</h2>
        <p>以物换物<br>用故事交换故事</p>
        <span class="arrow">→</span>
      </router-link>
      <router-link to="/planet" class="card planet">
        <div class="card-icon">🌍</div>
        <h2>星球</h2>
        <p>发现同频的人<br>从一句打招呼开始</p>
        <span class="arrow">→</span>
      </router-link>
    </div>

    <div class="stats-bar" v-if="stats">
      {{ stats.users }} 人在社区 · {{ stats.items }} 件物品 · {{ stats.friendships }} 次连接
    </div>

    <div class="recent" v-if="stats && stats.recent.length">
      <div v-for="r in stats.recent.slice(0,3)" :key="r.time" class="recent-item">
        <span>{{ r.nickname }} 发布了「{{ r.name }}」</span>
      </div>
    </div>

    <div class="guest-hint" v-if="!isLoggedIn">
      <router-link to="/login">登录</router-link>
      <span>·</span>
      <router-link to="/register">注册</router-link>
    </div>
    <router-link to="/rules" class="rules-link">社区守则</router-link>
    <a href="https://beian.mps.gov.cn/#/query/webSearch?code=44081102000117" rel="noreferrer" target="_blank" class="beian-link">
      <img src="/icons.svg#gongan-icon" style="width:14px;height:14px;vertical-align:middle;margin-right:4px" />粤公网安备44081102000117号
    </a>
  </div>
</template>

<script>
export default {
  name: 'Welcome',
  data() { return { stats: null } },
  computed: {
    isLoggedIn() { return !!localStorage.getItem('token') }
  },
  mounted() { this.loadStats() },
  methods: {
    async loadStats() {
      try {
        const res = await fetch('/api/public/stats')
        if (res.ok) this.stats = await res.json()
      } catch(e) {}
    }
  }
}
</script>

<style scoped>
.welcome {
  min-height: 100dvh; display: flex; flex-direction: column; align-items: center;
  padding: 40px 24px 100px; max-width: 480px; margin: 0 auto; text-align: center;
  background: #fff;
}
.hero { margin: 60px 0 40px; }
.logo { margin-bottom: 20px; display: inline-block; }
.logo svg { filter: drop-shadow(0 0 24px rgba(59,130,246,0.3)); animation: float 3s ease-in-out infinite; }
@keyframes float { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-6px) } }
.hero h1 { font-size: 32px; font-weight: 700; line-height: 1.4; color: #1e293b; letter-spacing: -0.3px; }
.hero .sub { color: #94a3b8; font-size: 15px; margin-top: 10px; }

.split { display: flex; gap: 14px; width: 100%; margin-bottom: 28px; }
.card {
  flex: 1; padding: 24px 18px; border-radius: 20px; text-decoration: none;
  display: flex; flex-direction: column; align-items: center; gap: 8px;
  transition: transform 0.2s, box-shadow 0.2s; position: relative; overflow: hidden;
}
.card:active { transform: scale(0.97); }
.card-icon { font-size: 36px; }
.card h2 { font-size: 18px; font-weight: 700; color: #1e293b; }
.card p { font-size: 13px; color: #64748b; line-height: 1.5; }
.arrow { position: absolute; bottom: 14px; right: 16px; font-size: 18px; opacity: 0.3; }

.yilian { background: linear-gradient(135deg, #fef9c3, #fef3c7); border: 1px solid rgba(245,158,11,0.15); }
.yilian:hover { box-shadow: 0 8px 24px rgba(245,158,11,0.12); }
.planet { background: linear-gradient(135deg, #e8f0ff, #dbeafe); border: 1px solid rgba(59,130,246,0.12); }
.planet:hover { box-shadow: 0 8px 24px rgba(59,130,246,0.1); }




.guest-hint { font-size: 14px; color: #94a3b8; }
.guest-hint a { color: #3b82f6; text-decoration: none; font-weight: 600; }
.guest-hint span { margin: 0 8px; }

.stats-bar { font-size: 13px; color: #94a3b8; margin-bottom: 20px; }


.recent { width: 100%; margin-bottom: 12px; }

.recent-item { font-size: 13px; color: #94a3b8; padding: 3px 0; }

.rules-link{font-size:13px;color:#94a3b8;text-decoration:none;margin-top:8px}
.beian-link{font-size:12px;color:#94a3b8;text-decoration:none;display:inline-flex;align-items:center;margin-top:8px}
</style>
