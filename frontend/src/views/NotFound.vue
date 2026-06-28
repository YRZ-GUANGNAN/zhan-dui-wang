<template>
  <div class="notfound">
    <div class="code">404</div>
    <h1>页面不见了</h1>
    <p>也许它被交换走了</p>
    <router-link to="/">← 回首页</router-link>
  </div>
</template>
<style scoped>
.notfound { display:flex; flex-direction:column; align-items:center; justify-content:center; min-height:80vh; text-align:center; }
.code { font-size: 80px; font-weight: 200; color: #cbd5e1; line-height: 1; }
h1 { font-size: 20px; color: #64748b; margin: 8px 0; }
p { color: #94a3b8; font-size: 14px; margin-bottom: 24px; }
a { color: #3b82f6; text-decoration: none; }
</style>
