import React from 'react'
import { Outlet } from 'react-router-dom'
import { Header } from './Header'
import { Sidebar } from './Sidebar'
import { ToastContainer } from '../common/ToastContainer'
import { IngestModal } from '../features/ingestion/IngestModal'

export const AppLayout: React.FC = () => {
  return (
    <div className="h-screen w-screen overflow-hidden flex flex-col bg-slate-50 text-slate-900 selection:bg-amber-400 selection:text-slate-950">
      <Header />
      <div className="flex-1 flex overflow-hidden relative">
        <Sidebar />
        <main className="flex-1 h-full overflow-y-auto relative flex flex-col bg-slate-50">
          <Outlet />
        </main>
      </div>
      <ToastContainer />
      <IngestModal />
    </div>
  )
}
