import { forwardRef } from 'react'
import { NormeType, NORME_LABELS, NORME_FLAGS } from '@/types'

interface NormeSelectorProps {
  value: NormeType
  onChange: (value: NormeType) => void
  disabled?: boolean
  showFlags?: boolean
  className?: string
  label?: string
  description?: string
}

const AVAILABLE_NORMES: NormeType[] = ['EC2', 'ACI318', 'BAEL91']
const UPCOMING_NORMES: NormeType[] = ['BS8110', 'CSA_A23']

export const NormeSelector = forwardRef<HTMLSelectElement, NormeSelectorProps>(
  ({ value, onChange, disabled, showFlags = true, className = '', label, description }, ref) => {
    return (
      <div className={`flex flex-col gap-1 ${className}`}>
        {label && (
          <label className="text-sm font-medium text-gray-700">
            {label}
          </label>
        )}
        <div className="relative">
          <select
            ref={ref}
            value={value}
            onChange={(e) => onChange(e.target.value as NormeType)}
            disabled={disabled}
            className="w-full px-3 py-2 pr-10 text-sm border border-gray-300 rounded-md
                     focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent
                     disabled:bg-gray-100 disabled:cursor-not-allowed
                     appearance-none bg-white"
          >
            <optgroup label="Normes disponibles">
              {AVAILABLE_NORMES.map((norme) => (
                <option key={norme} value={norme}>
                  {showFlags ? `${NORME_FLAGS[norme]} ` : ''}{NORME_LABELS[norme]}
                </option>
              ))}
            </optgroup>
            <optgroup label="Bientot disponibles" disabled>
              {UPCOMING_NORMES.map((norme) => (
                <option key={norme} value={norme} disabled>
                  {showFlags ? `${NORME_FLAGS[norme]} ` : ''}{NORME_LABELS[norme]} (bientot)
                </option>
              ))}
            </optgroup>
          </select>
          <div className="absolute inset-y-0 right-0 flex items-center pr-2 pointer-events-none">
            <svg className="w-5 h-5 text-gray-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
        {description && (
          <p className="text-xs text-gray-500">{description}</p>
        )}
      </div>
    )
  }
)

NormeSelector.displayName = 'NormeSelector'

interface NormeBadgeProps {
  norme: NormeType
  size?: 'sm' | 'md' | 'lg'
  showFlag?: boolean
}

export const NormeBadge = ({ norme, size = 'md', showFlag = true }: NormeBadgeProps) => {
  const sizeClasses = {
    sm: 'text-xs px-1.5 py-0.5',
    md: 'text-sm px-2 py-1',
    lg: 'text-base px-3 py-1.5',
  }

  const colorClasses: Record<NormeType, string> = {
    'EC2': 'bg-blue-100 text-blue-800 border-blue-200',
    'ACI318': 'bg-red-100 text-red-800 border-red-200',
    'BAEL91': 'bg-indigo-100 text-indigo-800 border-indigo-200',
    'BS8110': 'bg-purple-100 text-purple-800 border-purple-200',
    'CSA_A23': 'bg-orange-100 text-orange-800 border-orange-200',
  }

  return (
    <span
      className={`inline-flex items-center gap-1 font-medium rounded border ${sizeClasses[size]} ${colorClasses[norme]}`}
    >
      {showFlag && <span>{NORME_FLAGS[norme]}</span>}
      <span>{norme}</span>
    </span>
  )
}

export default NormeSelector
