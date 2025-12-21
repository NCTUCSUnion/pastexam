import { api } from './client'

export const userService = {
  getMe() {
    return api.get('/users/me')
  },

  updateMyNickname(nickname) {
    return api.patch('/users/me/nickname', { nickname })
  },
}
