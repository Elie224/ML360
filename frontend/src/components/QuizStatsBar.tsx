import { motion } from 'framer-motion'

type QuizStatsBarProps = {
  totalQuestions: number
  answeredQuestions: number
  currentIndex: number
  scoreEstimate: number
  questionTimeLeft: number
  questionTimeLimit: number
}

export function QuizStatsBar({
  totalQuestions,
  answeredQuestions,
  currentIndex,
  scoreEstimate,
  questionTimeLeft,
  questionTimeLimit,
}: QuizStatsBarProps) {
  const progress = totalQuestions > 0 ? Math.round((answeredQuestions / totalQuestions) * 100) : 0

  return (
    <section className="panel sticky top-3 z-20 border border-slate-200 p-4 sm:p-5">
      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <div className="stat-card">
          <p className="stat-label">Question</p>
          <p className="stat-value">
            {Math.min(currentIndex + 1, totalQuestions)}/{totalQuestions}
          </p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Score live</p>
          <p className="stat-value text-emerald-600">{scoreEstimate}%</p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Chronometre</p>
          <p className={`stat-value ${questionTimeLeft <= 10 ? 'text-rose-600' : 'text-orange-600'}`}>
            {questionTimeLeft}s / {questionTimeLimit}s
          </p>
        </div>
        <div className="stat-card">
          <p className="stat-label">Reponses</p>
          <p className="stat-value text-ml-600">{answeredQuestions}</p>
        </div>
      </div>

      <div className="mt-4 space-y-1">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Progression du quiz</span>
          <span>{progress}%</span>
        </div>
        <div className="h-2.5 w-full overflow-hidden rounded-full bg-slate-200">
          <motion.div
            initial={{ width: 0 }}
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.35, ease: 'easeOut' }}
            className="h-full rounded-full bg-gradient-to-r from-ml-500 via-violet-500 to-cyan-500"
          />
        </div>
      </div>
    </section>
  )
}
