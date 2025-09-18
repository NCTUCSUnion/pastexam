import { api } from './client'

export const memeService = {
  getRandomMeme() {
    return api.get('/meme')
  },
}
