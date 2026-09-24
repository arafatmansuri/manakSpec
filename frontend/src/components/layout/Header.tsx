import React from 'react'
import { useAppDispatch, useAppSelector } from '@/store/hooks'
import { toggleSidebar, setActiveModal } from '@/store/slices/uiSlice'
import { setPreferredLanguage } from '@/store/slices/sessionSlice'
import { Menu, Globe, ShieldCheck, Sparkles, BookOpen, Clock, UploadCloud } from 'lucide-react'
import { Link, useLocation } from 'react-router-dom'

export const LANGUAGES = [
  { code: 'English', label: 'English' },
  { code: 'Hindi', label: 'हिंदी (Hindi)' },
  { code: 'Gujarati', label: 'ગુજરાતી (Gujarati)' },
  { code: 'Tamil', label: 'தமிழ் (Tamil)' },
  { code: 'Telugu', label: 'తెలుగు (Telugu)' },
  { code: 'Bengali', label: 'বাংলা (Bengali)' },
  { code: 'Marathi', label: 'मराठी (Marathi)' },
]

export const Header: React.FC = () => {
  const dispatch = useAppDispatch()
  const preferredLanguage = useAppSelector((state) => state.session.preferredLanguage)
  const location = useLocation()

  return (
    <header className="h-16 px-4 md:px-6 bg-white border-b border-slate-200/90 flex items-center justify-between sticky top-0 z-30 shadow-xs">
      <div className="flex items-center gap-3">
        <button
          onClick={() => dispatch(toggleSidebar())}
          className="p-2 rounded-xl text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
          title="Toggle Navigation"
        >
          <Menu className="w-5 h-5" />
        </button>

        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-amber-500 to-blue-600 flex items-center justify-center shadow-sm group-hover:scale-105 transition-transform duration-200">
            <ShieldCheck className="w-5 h-5 text-white font-bold" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-extrabold text-base tracking-tight text-slate-900">
                MANAK<span className="text-amber-500">SPEC</span>
              </span>
              <span className="text-[10px] font-bold tracking-wider uppercase px-1.5 py-0.5 rounded bg-blue-50 text-blue-700 border border-blue-200">
                BIS AI
              </span>
            </div>
            <p className="text-[10px] text-slate-500 hidden sm:block">
              Bureau of Indian Standards • Smart Procurement Advisor
            </p>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-2 md:gap-3">
        <nav className="hidden lg:flex items-center gap-1 mr-2">
          <Link
            to="/"
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
              location.pathname === '/' || location.pathname.startsWith('/chat')
                ? 'bg-amber-50 text-amber-800 font-semibold border border-amber-200/60'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-amber-500" />
            <span>Assistant</span>
          </Link>
          <Link
            to="/standards"
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
              location.pathname === '/standards'
                ? 'bg-amber-50 text-amber-800 font-semibold border border-amber-200/60'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <BookOpen className="w-3.5 h-3.5 text-blue-600" />
            <span>BIS Catalog</span>
          </Link>
          <Link
            to="/history"
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors flex items-center gap-1.5 ${
              location.pathname === '/history'
                ? 'bg-amber-50 text-amber-800 font-semibold border border-amber-200/60'
                : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            <Clock className="w-3.5 h-3.5 text-amber-600" />
            <span>Procurement History</span>
          </Link>
        </nav>

        {/* Ingest Standards button */}
        <button
          onClick={() => dispatch(setActiveModal('ingest'))}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-800 border border-slate-300 transition-colors cursor-pointer"
          title="Ingest Indian Standards into Database"
        >
          <UploadCloud className="w-3.5 h-3.5 text-blue-600" />
          <span className="hidden sm:inline">Ingest Standards</span>
        </button>

        {/* Language selector */}
        {/* <div className="flex items-center gap-1.5 bg-slate-50 border border-slate-300 px-2.5 py-1.5 rounded-xl text-xs shadow-2xs">
          <Globe className="w-3.5 h-3.5 text-amber-600 shrink-0" />
          <select
            value={preferredLanguage}
            onChange={(e) => dispatch(setPreferredLanguage(e.target.value))}
            className="bg-transparent text-slate-800 text-xs font-medium focus:outline-none cursor-pointer"
          >
            {LANGUAGES.map((lang) => (
              <option key={lang.code} value={lang.code} className="bg-white text-slate-900">
                {lang.label}
              </option>
            ))}
          </select>
        </div> */}
      </div>
    </header>
  )
}
