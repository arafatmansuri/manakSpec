import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch } from '@/store/hooks'
import { setActiveModal } from '@/store/slices/uiSlice'
import { Card } from '@/components/common/Card'
import { Badge } from '@/components/common/Badge'
import { Button } from '@/components/common/Button'
import { Search, BookOpen, ShieldAlert, Sparkles, UploadCloud } from 'lucide-react'

// Curated prominent Indian Standards across major procurement sectors
const STANDARDS_CATALOG = [
  {
    is_number: 'IS 16106:2023',
    title: 'Self-Ballasted LED Lamps for General Lighting Services - Performance Requirements',
    publication_year: 2023,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'CRS Scheme-II',
    committee_code: 'LITD 27',
    scope: 'Safety and performance limits for domestic and street LED lamps, including luminous efficacy and surge limits.',
  },
  {
    is_number: 'IS 1786:2008',
    title: 'High Strength Deformed Steel Bars and Wires for Concrete Reinforcement',
    publication_year: 2008,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'ISI Scheme-I',
    committee_code: 'CED 54',
    scope: 'Covers physical, mechanical, and chemical properties of Fe 415, Fe 500, Fe 550, and Fe 600 grade TMT steel bars.',
  },
  {
    is_number: 'IS 15683:2018',
    title: 'Portable Fire Extinguishers - Performance and Construction - Specification',
    publication_year: 2018,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'ISI Scheme-I',
    committee_code: 'CED 22',
    scope: 'Requirements for portable fire extinguishers including water, foam, powder, and clean agent types.',
  },
  {
    is_number: 'IS 14543:2016',
    title: 'Packaged Drinking Water (Other Than Packaged Natural Mineral Water) - Specification',
    publication_year: 2016,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'ISI Scheme-I',
    committee_code: 'FAD 14',
    scope: 'Microbiological and chemical quality parameters for commercial and public packaged drinking water.',
  },
  {
    is_number: 'IS 1554 (Part 1):1988',
    title: 'PVC Insulated (Heavy Duty) Electric Cables for Working Voltages up to 1100 V',
    publication_year: 1988,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'ISI Scheme-I',
    committee_code: 'ETD 09',
    scope: 'Requirements of single, twin, three, four-core PVC insulated and sheathed cables for electricity supply.',
  },
  {
    is_number: 'IS 4985:2021',
    title: 'Unplasticized Polyvinyl Chloride (uPVC) Pipes for Potable Water Supplies',
    publication_year: 2021,
    status: 'Active',
    is_mandatory_qco: true,
    scheme_type: 'ISI Scheme-I',
    committee_code: 'CED 50',
    scope: 'Specification for uPVC pipes intended for human consumption water supply under pressure.',
  },
]

export const StandardsPage: React.FC = () => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const [searchTerm, setSearchTerm] = useState('')
  const [qcoOnly, setQcoOnly] = useState(false)

  const filteredStandards = STANDARDS_CATALOG.filter((std) => {
    const matchesSearch =
      std.is_number.toLowerCase().includes(searchTerm.toLowerCase()) ||
      std.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      std.scope.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesQco = !qcoOnly || std.is_mandatory_qco
    return matchesSearch && matchesQco
  })

  // Point 9: Put standard in input box on chat page
  const handleConsultStandard = (is_number: string, title: string) => {
    navigate(`/?consult=${encodeURIComponent(is_number + ' - ' + title)}`)
  }

  return (
    <div className="flex-1 p-4 md:p-8 max-w-6xl mx-auto w-full space-y-6 bg-slate-50">
      {/* Page Title & Ingest Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl sm:text-2xl font-extrabold text-slate-900 flex items-center gap-2">
            <BookOpen className="w-6 h-6 text-amber-600" />
            <span>BIS Standards & Quality Control Orders</span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse active Indian Standards (IS), mandatory certification schemes, and technical scope parameters.
          </p>
        </div>

        {/* Ingest Standards button (Point 8) */}
        <Button
          variant="amber"
          size="sm"
          onClick={() => dispatch(setActiveModal('ingest'))}
          leftIcon={<UploadCloud className="w-4 h-4" />}
        >
          Ingest New Standard
        </Button>
      </div>

      {/* Search & Filter Bar */}
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
        <div className="relative flex-1">
          <Search className="w-4 h-4 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search standard by IS Number (e.g. IS 16106) or keyword (LED, Steel, Cable)..."
            className="w-full bg-white border border-slate-300 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:border-amber-500 shadow-2xs"
          />
        </div>

        <button
          onClick={() => setQcoOnly(!qcoOnly)}
          className={`flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-xs font-bold border transition-all cursor-pointer ${
            qcoOnly
              ? 'bg-amber-100 text-amber-900 border-amber-300 shadow-xs'
              : 'bg-white text-slate-600 border-slate-300 hover:text-slate-900 hover:bg-slate-50'
          }`}
        >
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span>Mandatory QCO Only</span>
        </button>
      </div>

      {/* Standards List */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredStandards.map((std) => (
          <Card key={std.is_number} hoverEffect className="space-y-3 flex flex-col justify-between bg-white border-slate-200">
            <div className="space-y-2">
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono font-bold text-sm text-amber-700">
                  {std.is_number}
                </span>
                <div className="flex items-center gap-1.5">
                  {std.is_mandatory_qco && (
                    <Badge variant="qco" size="sm">
                      Mandatory QCO
                    </Badge>
                  )}
                  <Badge variant="crs" size="sm">
                    {std.scheme_type}
                  </Badge>
                </div>
              </div>

              <h3 className="text-sm font-bold text-slate-900">{std.title}</h3>
              <p className="text-xs text-slate-600 leading-relaxed">{std.scope}</p>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-[11px] text-slate-500 font-mono">
                TC: {std.committee_code} • {std.publication_year}
              </span>
              <Button
                size="sm"
                variant="outline"
                onClick={() => handleConsultStandard(std.is_number, std.title)}
                className="text-xs"
                rightIcon={<Sparkles className="w-3.5 h-3.5 text-amber-600" />}
              >
                Draft Clause
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  )
}
