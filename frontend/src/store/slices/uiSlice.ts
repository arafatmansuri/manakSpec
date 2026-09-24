import { createSlice, type PayloadAction } from '@reduxjs/toolkit'

interface ToastNotification {
  id: string
  message: string
  type: 'success' | 'error' | 'info'
}

interface UiState {
  isSidebarOpen: boolean
  activeModal: string | null
  toasts: ToastNotification[]
}

const initialState: UiState = {
  isSidebarOpen: true,
  activeModal: null,
  toasts: [],
}

export const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    toggleSidebar: (state) => {
      state.isSidebarOpen = !state.isSidebarOpen
    },
    setSidebarOpen: (state, action: PayloadAction<boolean>) => {
      state.isSidebarOpen = action.payload
    },
    setActiveModal: (state, action: PayloadAction<string | null>) => {
      state.activeModal = action.payload
    },
    addToast: (state, action: PayloadAction<Omit<ToastNotification, 'id'>>) => {
      state.toasts.push({
        ...action.payload,
        id: Math.random().toString(36).substring(2, 9),
      })
    },
    removeToast: (state, action: PayloadAction<string>) => {
      state.toasts = state.toasts.filter((t) => t.id !== action.payload)
    },
  },
})

export const {
  toggleSidebar,
  setSidebarOpen,
  setActiveModal,
  addToast,
  removeToast,
} = uiSlice.actions
export default uiSlice.reducer
