import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

interface SessionState {
  userId: string
  activeSessionId: string | null
  preferredLanguage: string
}

const getStoredUserId = (): string => {
  try {
    const existing = localStorage.getItem('manak_user_id')
    if (existing) return existing
    const generated = `user_${Math.random().toString(36).substring(2, 9)}_${Date.now().toString(36)}`
    localStorage.setItem('manak_user_id', generated)
    return generated
  } catch {
    return 'default_user'
  }
}

const initialState: SessionState = {
  userId: getStoredUserId(),
  activeSessionId: null,
  preferredLanguage: 'English',
}

export const sessionSlice = createSlice({
  name: 'session',
  initialState,
  reducers: {
    setUserId: (state, action: PayloadAction<string>) => {
      state.userId = action.payload
      try {
        localStorage.setItem('manak_user_id', action.payload)
      } catch {
        // ignore storage errors
      }
    },
    setActiveSessionId: (state, action: PayloadAction<string | null>) => {
      state.activeSessionId = action.payload
    },
    setPreferredLanguage: (state, action: PayloadAction<string>) => {
      state.preferredLanguage = action.payload
    },
  },
})

export const { setUserId, setActiveSessionId, setPreferredLanguage } = sessionSlice.actions
export default sessionSlice.reducer
