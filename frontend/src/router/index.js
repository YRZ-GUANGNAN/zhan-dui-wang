import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '../views/Welcome.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import PhoneLogin from '../views/PhoneLogin.vue'
import Home from '../views/Home.vue'
import Square from '../views/Square.vue'
import Profile from '../views/Profile.vue'
import Friends from '../views/Friends.vue'
import Chat from '../views/Chat.vue'
import ChatList from '../views/ChatList.vue'
import ProfileEdit from '../views/ProfileEdit.vue'
import UserProfile from '../views/UserProfile.vue'

import Rules from '../views/Rules.vue'

import NotFound from '../views/NotFound.vue'

const routes = [
  { path: '/', component: Welcome, meta: { title: '湛对网 - 交换故事，遇见同频的人' } },
  { path: '/login', component: Login, meta: { title: '登录 - 湛对网' } },
  { path: '/phone-login', component: PhoneLogin, meta: { title: '手机登录 - 湛对网' } },
  { path: '/register', component: Register, meta: { title: '注册 - 湛对网' } },
  { path: '/home', redirect: '/' },
  { path: '/planet', component: Home, meta: { title: '星球 - 湛对网' } },
  { path: '/square', component: Square, meta: { title: '忆涟 - 湛对网' } },
  { path: '/profile', component: Profile, meta: { title: '我的 - 湛对网' } },
  { path: '/profile/edit', component: ProfileEdit, meta: { title: '编辑资料 - 湛对网' } },
  { path: '/user/:userId', component: UserProfile, meta: { title: '用户主页 - 湛对网' } },
  { path: '/friends', component: Friends, meta: { title: '好友 - 湛对网' } },
  { path: '/chat/:userId', component: Chat, meta: { title: '聊天 - 湛对网' } },
  { path: '/chats', component: ChatList, meta: { title: '消息 - 湛对网' } },
  { path: '/requests', redirect: '/friends' },
  { path: '/rules', component: Rules, meta: { title: '社区守则 - 湛对网' } },
  { path: '/:pathMatch(.*)*', component: NotFound, meta: { title: '404 - 湛对网' } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  next()
})

router.afterEach((to) => {
  document.title = to.meta.title || '湛对网'
})

export default router
