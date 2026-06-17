import type { QuizListItem } from './types'

export type QuizSession = {
  currentQuestion: number
  selectedAnswers: Record<string, number>
  quizStarted: boolean
}

export const PROGRESS_UPDATED_EVENT = 'ml360-progress-updated'

type LearningProgress = {
  completedQuizzes: string[]
  quizSessions: Record<string, QuizSession>
}

const STORAGE_KEY = 'ml360_learning_progress_v1'

const EMPTY_PROGRESS: LearningProgress = {
  completedQuizzes: [],
  quizSessions: {},
}

function readProgress(): LearningProgress {
  if (typeof window === 'undefined') {
    return EMPTY_PROGRESS
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY)
    if (!raw) {
      return EMPTY_PROGRESS
    }

    const parsed = JSON.parse(raw) as Partial<LearningProgress>
    const completed = Array.isArray(parsed.completedQuizzes)
      ? parsed.completedQuizzes.filter((value): value is string => typeof value === 'string')
      : []
    const sessions = parsed.quizSessions && typeof parsed.quizSessions === 'object' ? parsed.quizSessions : {}

    const normalizedSessions: Record<string, QuizSession> = {}
    for (const [slug, session] of Object.entries(sessions)) {
      if (!session || typeof session !== 'object') {
        continue
      }

      const candidate = session as Partial<QuizSession>
      normalizedSessions[slug] = {
        currentQuestion: typeof candidate.currentQuestion === 'number' ? Math.max(0, candidate.currentQuestion) : 0,
        selectedAnswers:
          candidate.selectedAnswers && typeof candidate.selectedAnswers === 'object'
            ? Object.fromEntries(
                Object.entries(candidate.selectedAnswers).filter(
                  ([key, value]) => typeof key === 'string' && typeof value === 'number',
                ),
              )
            : {},
        quizStarted: Boolean(candidate.quizStarted),
      }
    }

    return {
      completedQuizzes: completed,
      quizSessions: normalizedSessions,
    }
  } catch {
    return EMPTY_PROGRESS
  }
}

function writeProgress(progress: LearningProgress) {
  if (typeof window === 'undefined') {
    return
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(progress))
  window.dispatchEvent(new Event(PROGRESS_UPDATED_EVENT))
}

export function readCompletedQuizSlugs() {
  return new Set(readProgress().completedQuizzes)
}

export function isQuizCompleted(quizSlug: string) {
  return readCompletedQuizSlugs().has(quizSlug)
}

export function markQuizCompleted(quizSlug: string) {
  const progress = readProgress()
  if (!progress.completedQuizzes.includes(quizSlug)) {
    progress.completedQuizzes.push(quizSlug)
  }
  delete progress.quizSessions[quizSlug]
  writeProgress(progress)
}

export function getQuizSession(quizSlug: string): QuizSession | null {
  const session = readProgress().quizSessions[quizSlug]
  return session ?? null
}

export function saveQuizSession(quizSlug: string, session: QuizSession) {
  const progress = readProgress()
  progress.quizSessions[quizSlug] = session
  writeProgress(progress)
}

export function clearQuizSession(quizSlug: string) {
  const progress = readProgress()
  if (!(quizSlug in progress.quizSessions)) {
    return
  }
  delete progress.quizSessions[quizSlug]
  writeProgress(progress)
}

export function hasQuizInProgress(quizSlug: string) {
  const session = getQuizSession(quizSlug)
  if (!session) {
    return false
  }
  return session.quizStarted || Object.keys(session.selectedAnswers).length > 0
}

export function areAllQuizzesCompleted(quizzes: QuizListItem[], completedQuizSlugs: Set<string>) {
  if (quizzes.length === 0) {
    return false
  }
  return quizzes.every((quiz) => completedQuizSlugs.has(quiz.slug))
}
