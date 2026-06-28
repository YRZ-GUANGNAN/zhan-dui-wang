<template>
  <div style="display:flex;flex-direction:column;height:100dvh;max-width:500px;margin:0 auto;background:var(--bg);padding-bottom:env(safe-area-inset-bottom)">
    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--bg-card);border-bottom:1px solid var(--border);flex-shrink:0">
      <button @click="$router.push('/chats')" style="background:none;border:none;font-size:20px;cursor:pointer;padding:4px 8px">←</button>
      <span style="font-weight:600;font-size:16px">{{ friendName || '聊天' }}</span>
    </div>

    <div ref="msgBox" style="flex:1;overflow-y:auto;padding:12px">
      <div v-if="loading" style="text-align:center;padding:40px;color:#999">加载中...</div>
      <div v-else-if="messages.length===0" style="text-align:center;padding:60px 20px;color:#999">
        <div style="font-size:48px">✨</div><div style="margin-top:8px">打个招呼吧</div>
      </div>
      <div v-for="msg in messages" :key="msg.id" :style="{display:'flex',flexDirection:'column',alignItems:(msg.sender&&msg.sender.id)==myId?'flex-end':'flex-start',marginBottom:'10px'}">
        <img v-if="msg.imageUrl&&!msg.content" :src="imgUrl(msg.imageUrl)" style="max-width:200px;max-height:160px;border-radius:12px;cursor:pointer" @click="openImage(imgUrl(msg.imageUrl))" />
        <div v-if="msg.content" :style="{
          padding:'10px 14px',borderRadius:'16px',fontSize:'15px',maxWidth:'75%',wordBreak:'break-word',
          background:(msg.sender&&msg.sender.id)==myId?'#3b82f6':'#fff',
          color:(msg.sender&&msg.sender.id)==myId?'#fff':'#333',
          border:(msg.sender&&msg.sender.id)==myId?'none':'1px solid #e5e5e5'
        }">{{ msg.content }}</div>
      </div>
    </div>

    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--bg-card);border-top:1px solid var(--border);flex-shrink:0">
      <label style="cursor:pointer;color:#94a3b8;font-size:20px;padding:4px">
        📷<input type="file" accept="image/*" @change="onImage" hidden ref="imgInput" />
      </label>
      <input v-model="content" @keyup.enter="send" placeholder="说点啥..." inputmode="text" style="flex:1;padding:10px 14px;border:1px solid var(--border);border-radius:20px;outline:none;font-size:15px;background:var(--bg);color:var(--text)">
      <button @click="send" :disabled="!content.trim()" style="width:38px;height:38px;border-radius:50%;border:none;background:#3b82f6;color:#fff;font-size:16px;cursor:pointer;flex-shrink:0">➤</button>
    </div>
  </div>
</template>

<script>
import api from '../api/index.js'
import { IMG_BASE } from '../config.js'

export default {
  name: 'Chat',
  data() {
    return { messages: [], content: '', myId: null, otherUserId: null, friendName: '', loading: true, pollTimer: null }
  },
  async mounted() {
    const uid = this.$route.params.userId
    const myId = localStorage.getItem('userId')
    this.myId = myId ? Number(myId) : null
    this.otherUserId = uid ? Number(uid) : null
    if (!uid || !myId) { this.loading = false; return }
    try {
      const res = await api.users.get(uid)
      if (res && res.data) this.friendName = res.data.nickname || res.data.username
    } catch(e) {}
    await this.loadMessages()
    this.loading = false
    // Mark messages as read
    this.markRead()
    // Poll for new messages every 5 seconds
    this.pollTimer = setInterval(() => this.pollNewMessages(), 2000)
  },
  beforeUnmount() {
    if (this.pollTimer) clearInterval(this.pollTimer)
  },
  methods: {
    imgUrl(url) { return url && url.startsWith('/') ? IMG_BASE + url : url },
    openImage(url) { if (url) window.open(url, '_blank') },
    async loadMessages() {
      try {
        const res = await api.messages.conversation(this.myId, this.otherUserId)
        this.messages = res.data || []
      } catch(e) {}
    },
    async pollNewMessages() {
      try {
        const res = await api.messages.conversation(this.myId, this.otherUserId)
        const newMsgs = res.data || []
        // Only update if there are actually new messages (by count)
        if (newMsgs.length > this.messages.length) {
          // Keep local messages that don't exist on server yet
          const serverIds = new Set(newMsgs.map(m => m.id))
          const localOnly = this.messages.filter(m => m.id > 999999999999 || !serverIds.has(m.id))
          this.messages = [...newMsgs, ...localOnly]
          this.markRead()
        }
      } catch(e) {}
    },
    async markRead() {
      try {
        const unread = await api.messages.unread(this.myId)
        for (const msg of (unread.data || [])) {
          if (msg.sender_id == this.otherUserId || (msg.sender && msg.sender.id == this.otherUserId)) {
            await api.messages.markRead(msg.id, this.myId)
          }
        }
      } catch(e) {}
    },
    async send() {
      const text = this.content.trim()
      if (!text || !this.myId) return
      this.content = ''
      this.messages.push({ id: Date.now(), content: text, sender: { id: this.myId }, createTime: new Date().toISOString() })
      try { await api.messages.send(this.myId, this.otherUserId, text) } catch(e) {}
    },
    onImage(e) {
      const file = e.target.files[0]
      if (!file || !this.myId) return
      this.messages.push({ id: Date.now(), content: '', sender: { id: this.myId }, imageUrl: URL.createObjectURL(file), createTime: new Date().toISOString() })
      api.messages.sendImage(this.myId, this.otherUserId, file).catch(() => {})
      if (this.$refs.imgInput) this.$refs.imgInput.value = ''
    }
  }
}
</script>
