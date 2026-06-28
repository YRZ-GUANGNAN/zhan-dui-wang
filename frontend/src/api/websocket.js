import { WS_URL } from '../config.js'

// WebSocket disabled - using REST API for messaging
let connected = false
const listeners = {}

export function connect() { connected = false }
export function disconnect() { connected = false }
export function onChatMessage(handler) { listeners['chat'] = handler }
export function offChatMessage() { delete listeners['chat'] }
export function onNotification(handler) {}
export function offNotification() {}
export function sendMessage(senderId, receiverId, content) { return false }
