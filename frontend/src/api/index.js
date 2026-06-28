import axios from 'axios'
import { API_BASE } from '../config.js'

const api = axios.create({
  baseURL: API_BASE
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  response => response,
  error => {
    const isAuthRequest = error.config?.url?.startsWith('/auth/')
    if (error.response?.status === 401 && !isAuthRequest) {
      localStorage.clear()
      window.location.assign('/login')
    }
    return Promise.reject(error)
  }
)

export default {
  auth: {
    login(data) { return api.post('/auth/login', data) },
    register(data) { return api.post('/auth/register', data) }
  },
  users: {
    list(excludeId) { return api.get('/users/list', { params: { excludeId } }) },
    get(id) { return api.get(`/users/${id}`) },
    update(id, data) { return api.put(`/users/${id}/profile`, data) },
    avatar(id, file) {
      const formData = new FormData()
      formData.append('file', file)
      return api.post(`/users/${id}/avatar`, formData)
    },
    background(id, file) {
      const formData = new FormData()
      formData.append('file', file)
      return api.post(`/users/${id}/background`, formData)
    },
    search(keyword) { return api.get('/users/search', { params: { keyword } }) },
    recommend(userId) { return api.get('/users/recommend', { params: { userId } }) },
    showOnPlanet(userId, value) { return api.put(`/users/${userId}/showOnPlanet`, null, { params: { value } }) }
  },
  friends: {
    request(friendId, userId) { return api.post(`/friends/request/${friendId}`, null, { params: { userId } }) },
    accept(friendshipId, userId) { return api.post(`/friends/accept/${friendshipId}`, null, { params: { userId } }) },
    reject(friendshipId, userId) { return api.delete(`/friends/reject/${friendshipId}`, { params: { userId } }) },
    remove(friendId, userId) { return api.delete(`/friends/remove/${friendId}`, { params: { userId } }) },
    list(userId) { return api.get(`/friends/my/${userId}`) },
    requests(userId) { return api.get(`/friends/requests/${userId}`) }
  },
  messages: {
    send(senderId, receiverId, content) {
      return api.post('/messages', { content }, { params: { senderId, receiverId } })
    },
    sendImage(senderId, receiverId, file) {
      const formData = new FormData()
      formData.append('senderId', senderId)
      formData.append('receiverId', receiverId)
      formData.append('file', file)
      return api.post('/messages/image', formData)
    },
    conversation(userId, otherUserId) {
      return api.get('/messages/conversation', { params: { userId, otherUserId } })
    },
    conversations(userId) { return api.get('/conversations', { params: { userId } }) },
    deleteConversation(userId, otherUserId) {
      return api.delete('/messages/conversation', { params: { userId, otherUserId } })
    },
    unread(userId) { return api.get(`/messages/unread/${userId}`) },
    markRead(messageId, userId) { return api.put(`/messages/read/${messageId}`, null, { params: { userId } }) }
  },
  posts: {
    create(userId, content, imageFile) {
      const formData = new FormData()
      formData.append('userId', userId)
      formData.append('content', content)
      if (imageFile) formData.append('image', imageFile)
      return api.post('/posts', formData)
    },
    list(userId) { return api.get(`/posts/user/${userId}`) },
    feed() { return api.get('/posts/feed') },
    like(postId, userId) { return api.post(`/posts/${postId}/like`, null, { params: { userId } }) },
    unlike(postId, userId) { return api.delete(`/posts/${postId}/like`, { params: { userId } }) },
    likes(postId, userId) { return api.get(`/posts/${postId}/likes`, { params: { userId } }) },
    comment(postId, userId, content) { return api.post(`/posts/${postId}/comment`, { userId, content }) },
    comments(postId) { return api.get(`/posts/${postId}/comments`) },
    delete(postId, userId) { return api.delete(`/posts/${postId}`, { params: { userId } }) }
  },
  stats: {
    overview() { return api.get('/stats/overview') }
  }
}
