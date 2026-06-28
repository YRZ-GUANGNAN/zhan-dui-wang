import { WS_URL } from '../config.js'

let socket = null
let authenticated = false
let reconnectTimer = null
let heartbeatTimer = null
let reconnectAttempt = 0
let activeToken = null
let allowReconnect = true

const chatListeners = new Set()
const notificationListeners = new Set()
const connectionListeners = new Set()

function emit(listeners, payload) {
  for (const listener of listeners) {
    try { listener(payload) } catch (_) {}
  }
}

function setAuthenticated(value) {
  if (authenticated === value) return
  authenticated = value
  emit(connectionListeners, value)
}

function clearTimers() {
  if (reconnectTimer) clearTimeout(reconnectTimer)
  if (heartbeatTimer) clearInterval(heartbeatTimer)
  reconnectTimer = null
  heartbeatTimer = null
}

function scheduleReconnect() {
  if (!allowReconnect || reconnectTimer || !localStorage.getItem('token')) return
  const delay = Math.min(1000 * (2 ** reconnectAttempt), 30000) + Math.random() * 500
  reconnectAttempt += 1
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null
    connect()
  }, delay)
}

function handleMessage(event) {
  let payload
  try { payload = JSON.parse(event.data) } catch (_) { return }

  if (payload.type === 'ready') {
    reconnectAttempt = 0
    setAuthenticated(true)
    heartbeatTimer = setInterval(() => {
      if (socket?.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }))
      }
    }, 20000)
    return
  }

  if (payload.type === 'message') {
    emit(chatListeners, payload)
    emit(notificationListeners, payload.message)
    return
  }

  if (['ack', 'sent', 'read', 'error'].includes(payload.type)) {
    emit(chatListeners, payload)
  }
}

export function connect() {
  const token = localStorage.getItem('token')
  if (!token) {
    disconnect()
    return
  }
  if (
    socket &&
    activeToken === token &&
    [WebSocket.CONNECTING, WebSocket.OPEN].includes(socket.readyState)
  ) return

  clearTimers()
  if (socket) socket.close()
  allowReconnect = true
  activeToken = token
  const currentSocket = new WebSocket(WS_URL)
  socket = currentSocket

  currentSocket.addEventListener('open', () => {
    currentSocket.send(JSON.stringify({ type: 'auth', token }))
  })
  currentSocket.addEventListener('message', handleMessage)
  currentSocket.addEventListener('close', (event) => {
    if (socket !== currentSocket) return
    socket = null
    setAuthenticated(false)
    clearTimers()
    if (event.code === 4401) {
      allowReconnect = false
      localStorage.clear()
      if (window.location.pathname !== '/login') window.location.assign('/login')
      return
    }
    scheduleReconnect()
  })
  currentSocket.addEventListener('error', () => currentSocket.close())
}

export function disconnect() {
  allowReconnect = false
  clearTimers()
  setAuthenticated(false)
  activeToken = null
  if (socket) {
    const current = socket
    socket = null
    current.close()
  }
}

export function isConnected() {
  return authenticated && socket?.readyState === WebSocket.OPEN
}

export function newClientId() {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

export function sendMessage(receiverId, content, clientId) {
  if (!isConnected()) return false
  socket.send(JSON.stringify({
    type: 'message',
    receiverId,
    content,
    clientId
  }))
  return true
}

export function markRead(messageId) {
  if (!isConnected()) return false
  socket.send(JSON.stringify({ type: 'read', messageId }))
  return true
}

export function onChatMessage(handler) { chatListeners.add(handler) }
export function offChatMessage(handler) {
  if (handler) chatListeners.delete(handler)
  else chatListeners.clear()
}
export function onNotification(handler) { notificationListeners.add(handler) }
export function offNotification(handler) {
  if (handler) notificationListeners.delete(handler)
  else notificationListeners.clear()
}
export function onConnectionChange(handler) { connectionListeners.add(handler) }
export function offConnectionChange(handler) {
  if (handler) connectionListeners.delete(handler)
  else connectionListeners.clear()
}
