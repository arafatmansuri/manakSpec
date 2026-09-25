import { createBrowserRouter } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ChatPage } from '@/pages/ChatPage'
// import { StandardsPage } from '@/pages/StandardsPage'
import { HistoryPage } from '@/pages/HistoryPage'
import { NotFoundPage } from '@/pages/NotFoundPage'

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      {
        index: true,
        element: <ChatPage />,
      },
      {
        path: 'chat/:sessionId',
        element: <ChatPage />,
      },
      // {
      //   path: 'standards',
      //   element: <StandardsPage />,
      // },
      {
        path: 'history',
        element: <HistoryPage />,
      },
      {
        path: '*',
        element: <NotFoundPage />,
      },
    ],
  },
])
