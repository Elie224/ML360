import type { ReactNode } from 'react'
import { motion } from 'framer-motion'

type AnswerState = 'idle' | 'selected' | 'correct' | 'incorrect'

type AnswerCardProps = {
  children: ReactNode
  selected: boolean
  disabled: boolean
  state: AnswerState
  onSelect: () => void
}

function stateClasses(state: AnswerState) {
  if (state === 'correct') {
    return 'border-success bg-emerald-50 ring-2 ring-emerald-200'
  }
  if (state === 'incorrect') {
    return 'border-danger bg-rose-50 ring-2 ring-rose-200'
  }
  if (state === 'selected') {
    return 'border-primary bg-blue-50 ring-2 ring-blue-200'
  }
  return 'border-stroke bg-white hover:border-primary/40 hover:bg-blue-50/30'
}

export function AnswerCard({ children, selected, disabled, state, onSelect }: AnswerCardProps) {
  return (
    <motion.button
      type="button"
      onClick={onSelect}
      disabled={disabled}
      whileHover={disabled ? undefined : { y: -2 }}
      whileTap={disabled ? undefined : { scale: 0.995 }}
      className={`w-full rounded-2xl border p-4 text-left transition-all duration-200 ${stateClasses(state)} ${
        disabled ? 'cursor-default opacity-95' : 'cursor-pointer'
      }`}
      aria-pressed={selected}
    >
      <span className="flex items-start gap-3">
        <span
          className={`mt-1 inline-flex h-5 w-5 shrink-0 items-center justify-center rounded-full border text-[11px] font-bold ${
            selected ? 'border-primary bg-primary text-white' : 'border-slate-300 text-slate-400'
          }`}
        >
          {selected ? '✓' : ''}
        </span>
        <span className="text-sm text-slate-700 sm:text-base">{children}</span>
      </span>
    </motion.button>
  )
}
