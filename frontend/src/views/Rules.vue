<template>
  <div class="page">
    <div class="page-header">
      <button class="btn-icon" @click="$router.back()">←</button>
      <h1>社区守则</h1>
    </div>

    <div class="rule-card">
      <h3>🤝 友好交流</h3>
      <p>尊重每一位社区成员，禁止骚扰、侮辱、歧视性言论。</p>
    </div>
    <div class="rule-card">
      <h3>🚫 禁止金钱交易</h3>
      <p>湛对网是一个以物换物和兴趣交友平台，禁止任何形式的金钱交易。</p>
    </div>
    <div class="rule-card">
      <h3>📖 真实故事</h3>
      <p>发布的物品故事应真实可信，不虚构、不抄袭。</p>
    </div>
    <div class="rule-card">
      <h3>📍 线下安全</h3>
      <p>线下交换时选择公共场所，注意人身安全，建议结伴而行。</p>
    </div>
    <div class="rule-card">
      <h3>🔒 隐私保护</h3>
      <p>不随意透露他人的个人信息，未经允许不截图传播聊天内容。</p>
    </div>
    <div class="rule-card">
      <h3>🛡️ 举报机制</h3>
      <p>如遇违规行为，请联系管理员（19375887542）进行举报处理。</p>
    </div>

    <p class="footer-note">湛对网 — 永远免费 · 让校园连接更简单</p>
  </div>
</template>

<script>
export default { name: 'Rules' }
</script>

<style scoped>
.rule-card {
  background: #fff; border-radius: 14px; padding: 16px; margin-bottom: 10px;
  border: 1px solid rgba(0,0,0,0.06);
}
.rule-card h3 { font-size: 16px; font-weight: 600; margin-bottom: 6px; color: #1e293b; }
.rule-card p { font-size: 14px; color: #64748b; line-height: 1.6; }
.footer-note { text-align: center; color: #94a3b8; font-size: 13px; margin-top: 24px; padding-bottom: 20px; }
</style>
