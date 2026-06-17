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
    <section className="glass-card sticky top-3 z-20 p-4 sm:p-5">
      <div className="mb-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Question</p>
          <p className="font-display text-xl font-bold text-slate-900">
            {Math.min(currentIndex + 1, totalQuestions)}/{totalQuestions}
          </p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Score en cours</p>
          <p className="font-display text-xl font-bold text-success">{scoreEstimate}%</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Chrono de la question</p>
          <p className={`font-display text-xl font-bold ${questionTimeLeft <= 10 ? 'text-danger' : 'text-warning'}`}>
            {questionTimeLeft}s / {questionTimeLimit}s
          </p>
        </div>
        <div className="rounded-xl bg-slate-50 p-3">
          <p className="text-[11px] uppercase tracking-[0.16em] text-slate-500">Réponses</p>
          <p className="font-display text-xl font-bold text-primary">{answeredQuestions}</p>
        </div>
      </div>

      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs text-slate-500">
          <span>Progression quiz</span>
          <span>{progress}%</span>
        </div>
        <div className="progress-track">
          <div className="h-full rounded-full bg-gradient-to-r from-primary via-secondary to-success" style={{ width: `${progress}%` }} />
        </div>
      </div>
    </section>
  )
}
