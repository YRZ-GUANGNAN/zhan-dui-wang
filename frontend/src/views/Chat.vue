<template>
  <div style="display:flex;flex-direction:column;height:100dvh;max-width:500px;margin:0 auto;background:var(--bg);padding-bottom:env(safe-area-inset-bottom)">
    <div style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:var(--bg-card);border-bottom:1px solid var(--border);flex-shrink:0">
      <button @click="$router.push('/chats')" style="background:none;border:none;font-size:20px;cursor:pointer;padding:4px 8px">←</button>
      <span style="font-weight:600;font-size:16px">{{ friendName || '聊天' }}</span>
      <span :title="socketReady ? '已连接' : '连接中'" :style="{width:'8px',height:'8px',borderRadius:'50%',background:socketReady?'#22c55e':'#f59e0b'}"></span>
    </div>

    <div ref="msgBox" style="flex:1;overflow-y:auto;padding:12px">
      <div v-if="loading" style="text-align:center;padding:40px;color:#999">加载中...</div>
      <div v-else-if="messages.length===0" style="text-align:center;padding:60px 20px;color:#999">
        <div style="font-size:48px">✨</div><div style="margin-top:8px">打个招呼吧</div>
      </div>
      <div v-for="msg in messages" :key="msg.id" :style="{display:'flex',flexDirection:'column',alignItems:(msg.sender&&msg.sender.id)==myId?'flex-end':'flex-start',marginBottom:'10px'}">
        <img v-if="msg.imageUrl" :src="imgUrl(msg.imageUrl)" style="max-width:200px;max-height:160px;border-radius:12px;cursor:pointer" @click="openImage(imgUrl(msg.imageUrl))" />
        <div v-if="msg.content && (!msg.imageUrl || msg.content !== '[图片]')" :style="{
          padding:'10px 14px',borderRadius:'16px',fontSize:'15px',maxWidth:'75%',wordBreak:'break-word',
          background:(msg.sender&&msg.sender.id)==myId?'#3b82f6':'#fff',
          color:(msg.sender&&msg.sender.id)==myId?'#fff':'#333',
          border:(msg.sender&&msg.sender.id)==myId?'none':'1px solid #e5e5e5'
        }">{{ msg.content }}</div>
        <span v-if="msg.pending" style="font-size:11px;color:#94a3b8;margin-top:3px">发送中...</span>
        <button v-else-if="msg.failed" @click="retryMessage(msg)" style="border:none;background:none;color:#ef4444;font-size:11px;cursor:pointer;margin-top:3px">发送失败，重试</button>
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
import {
  connect,
  isConnected,
  markRead as markReadSocket,
  newClientId,
  offChatMessage,
  offConnectionChange,
  onChatMessage,
  onConnectionChange,
  sendMessage as sendSocketMessage
} from '../api/websocket.js'

export default {
  name: 'Chat',
  data() {
    return {
      messages: [],
      content: '',
      myId: null,
      otherUserId: null,
      friendName: '',
      loading: true,
      pollTimer: null,
      socketReady: false,
      pendingTimers: new Map(),
      chatHandler: null,
      connectionHandler: null
    }
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
    this.markRead()
    this.chatHandler = event => this.handleSocketEvent(event)
    this.connectionHandler = ready => { this.socketReady = ready }
    onChatMessage(this.chatHandler)
    onConnectionChange(this.connectionHandler)
    connect()
    this.socketReady = isConnected()
    this.pollTimer = setInterval(() => {
      if (!isConnected()) this.pollNewMessages()
    }, 10000)
  },
  beforeUnmount() {
    if (this.pollTimer) clearInterval(this.pollTimer)
    for (const timer of this.pendingTimers.values()) clearTimeout(timer)
    offChatMessage(this.chatHandler)
    offConnectionChange(this.connectionHandler)
  },
  methods: {
    imgUrl(url) { return url && url.startsWith('/') ? IMG_BASE + url : url },
    openImage(url) { if (url) window.open(url, '_blank') },
    async loadMessages() {
      try {
        const res = await api.messages.conversation(this.myId, this.otherUserId)
        this.messages = res.data || []
        this.scrollToBottom()
      } catch(e) {}
    },
    async pollNewMessages() {
      try {
        const res = await api.messages.conversation(this.myId, this.otherUserId)
        for (const message of (res.data || [])) this.mergeMessage(message)
        this.markRead()
      } catch(e) {}
    },
    belongsToConversation(message) {
      const sender = Number(message?.sender?.id)
      const receiver = Number(message?.receiver?.id)
      return (
        (sender === this.myId && receiver === this.otherUserId) ||
        (sender === this.otherUserId && receiver === this.myId)
      )
    },
    mergeMessage(message, clientId = message?.clientId) {
      if (!message || !this.belongsToConversation(message)) return
      const index = this.messages.findIndex(item =>
        (message.id && item.id === message.id) ||
        (clientId && item.clientId === clientId)
      )
      const merged = { ...message, clientId, pending: false, failed: false }
      if (index >= 0) this.messages.splice(index, 1, { ...this.messages[index], ...merged })
      else this.messages.push(merged)
      if (clientId && this.pendingTimers.has(clientId)) {
        clearTimeout(this.pendingTimers.get(clientId))
        this.pendingTimers.delete(clientId)
      }
      this.scrollToBottom()
    },
    handleSocketEvent(event) {
      if (event.type === 'message') {
        const message = event.message
        if (!this.belongsToConversation(message)) return
        this.mergeMessage(message)
        if (Number(message.sender?.id) === this.otherUserId) {
          if (!markReadSocket(message.id)) {
            api.messages.markRead(message.id, this.myId).catch(() => {})
          }
        }
      } else if (event.type === 'ack' || event.type === 'sent') {
        this.mergeMessage(event.message, event.clientId)
      } else if (event.type === 'read') {
        const message = this.messages.find(item => item.id === event.messageId)
        if (message) message.read = true
      }
    },
    scrollToBottom() {
      this.$nextTick(() => {
        if (this.$refs.msgBox) this.$refs.msgBox.scrollTop = this.$refs.msgBox.scrollHeight
      })
    },
    async markRead() {
      try {
        const unread = await api.messages.unread(this.myId)
        for (const msg of (unread.data || [])) {
          if (msg.sender_id == this.otherUserId || (msg.sender && msg.sender.id == this.otherUserId)) {
            if (!markReadSocket(msg.id)) await api.messages.markRead(msg.id, this.myId)
          }
        }
      } catch(e) {}
    },
    async sendViaRest(message) {
      try {
        const res = await api.messages.send(
          this.myId,
          this.otherUserId,
          message.content,
          message.clientId
        )
        this.mergeMessage(res.data, message.clientId)
      } catch(e) {
        message.pending = false
        message.failed = true
      }
    },
    async send() {
      const text = this.content.trim()
      if (!text || !this.myId) return
      this.content = ''
      const clientId = newClientId()
      const message = {
        id: `local-${clientId}`,
        clientId,
        content: text,
        sender: { id: this.myId },
        receiver: { id: this.otherUserId },
        createTime: new Date().toISOString(),
        pending: true
      }
      this.messages.push(message)
      this.scrollToBottom()
      if (sendSocketMessage(this.otherUserId, text, clientId)) {
        this.pendingTimers.set(clientId, setTimeout(() => this.sendViaRest(message), 7000))
      } else {
        await this.sendViaRest(message)
      }
    },
    async onImage(e) {
      const file = e.target.files[0]
      if (!file || !this.myId) return
      const clientId = newClientId()
      const message = {
        id: `local-${clientId}`,
        clientId,
        content: '[图片]',
        sender: { id: this.myId },
        receiver: { id: this.otherUserId },
        imageUrl: URL.createObjectURL(file),
        createTime: new Date().toISOString(),
        pending: true,
        imageFile: file
      }
      this.messages.push(message)
      this.scrollToBottom()
      try {
        const res = await api.messages.sendImage(
          this.myId,
          this.otherUserId,
          file,
          clientId
        )
        this.mergeMessage(res.data, clientId)
      } catch(e) {
        message.pending = false
        message.failed = true
      }
      if (this.$refs.imgInput) this.$refs.imgInput.value = ''
    },
    retryMessage(message) {
      message.failed = false
      message.pending = true
      if (message.imageFile) {
        api.messages.sendImage(
          this.myId,
          this.otherUserId,
          message.imageFile,
          message.clientId
        ).then(res => this.mergeMessage(res.data, message.clientId))
          .catch(() => { message.pending = false; message.failed = true })
      } else if (sendSocketMessage(this.otherUserId, message.content, message.clientId)) {
        this.pendingTimers.set(
          message.clientId,
          setTimeout(() => this.sendViaRest(message), 7000)
        )
      } else {
        this.sendViaRest(message)
      }
    }
  }
}
</script>
