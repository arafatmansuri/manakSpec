import { configureStore } from '@reduxjs/toolkit'
import sessionReducer from './slices/sessionSlice'
import uiReducer from './slices/uiSlice'

export const store = configureStore({
  reducer: {
    session: sessionReducer,
    ui: uiReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
