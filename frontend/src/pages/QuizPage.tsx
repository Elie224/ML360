import { useEffect, useMemo, useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useParams } from 'react-router-dom'
import { fetchQuizDetail, fetchQuizzes, submitQuiz } from '../api'
import { AnswerCard } from '../components/AnswerCard'
import { QuizStatsBar } from '../components/QuizStatsBar'
import { normalizeFrenchText } from '../frenchText'
import { useAsyncData } from '../hooks'
import { clearQuizSession, getQuizSession, isQuizCompleted, markQuizCompleted, saveQuizSession } from '../progression'
import type { SubmissionResponse } from '../types'

function difficultyLabel(difficulty: 'easy' | 'medium' | 'hard') {
  if (difficulty === 'easy') {
    return 'Facile'
  }
  if (difficulty === 'medium') {
    return 'Moyen'
  }
  return 'Difficile'
}

function questionTimeLimit(difficulty: 'easy' | 'medium' | 'hard') {
  if (difficulty === 'hard') {
    return 80
  }
  return 60
}

export function QuizPage() {
  const { slug } = useParams()
  const [selectedAnswers, setSelectedAnswers] = useState<Record<number, number>>({})
  const [submission, setSubmission] = useState<SubmissionResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [quizStarted, setQuizStarted] = useState(false)
  const [startConfirmed, setStartConfirmed] = useState(false)
  const [questionTimeLeft, setQuestionTimeLeft] = useState(60)
  const [canResume, setCanResume] = useState(false)

  const { data: quiz, error, loading } = useAsyncData(() => fetchQuizDetail(slug ?? ''), [slug])
  const { data: categoryQuizzes } = useAsyncData(
    () => (quiz?.category.slug ? fetchQuizzes(quiz.category.slug) : Promise.resolve([])),
    [quiz?.category.slug],
  )

  useEffect(() => {
    if (!slug) {
      return
    }

    const session = getQuizSession(slug)
    if (!session) {
      setSubmission(null)
      setSelectedAnswers({})
      setCurrentQuestion(0)
      setQuizStarted(false)
      setStartConfirmed(false)
      setQuestionTimeLeft(60)
      setCanResume(false)
      return
    }

    setSubmission(null)
    setSelectedAnswers(
      Object.fromEntries(Object.entries(session.selectedAnswers).map(([questionId, choiceId]) => [Number(questionId), choiceId])),
    )
    setCurrentQuestion(session.currentQuestion)
    setQuizStarted(false)
    setStartConfirmed(false)
    setQuestionTimeLeft(60)
    setCanResume(Boolean(session.quizStarted) || Object.keys(session.selectedAnswers).length > 0)
  }, [slug])

  useEffect(() => {
    setSubmission(null)
  }, [slug])

  useEffect(() => {
    if (!quiz) {
      return
    }
    setCurrentQuestion((current) => Math.min(current, Math.max(quiz.questions.length - 1, 0)))
  }, [quiz])

  const answeredQuestions = useMemo(() => Object.keys(selectedAnswers).length, [selectedAnswers])

  const scoreEstimate = useMemo(() => {
    if (!quiz || answeredQuestions === 0) {
      return 0
    }
    const answeredQuestionIds = new Set(Object.keys(selectedAnswers).map(Number))
    const potentiallyCorrect = quiz.questions.filter((question) => answeredQuestionIds.has(question.id)).length
    return Math.round((potentiallyCorrect / quiz.questions.length) * 100)
  }, [answeredQuestions, quiz, selectedAnswers])

  const activeQuestion = useMemo(() => {
    if (!quiz) return null
    return quiz.questions[currentQuestion] ?? null
  }, [currentQuestion, quiz])

  const activeQuestionLimit = useMemo(() => {
    if (!activeQuestion) return 60
    return questionTimeLimit(activeQuestion.difficulty)
  }, [activeQuestion])

  const moduleIsUnlocked = useMemo(() => {
    if (!quiz) {
      return true
    }

    if (!categoryQuizzes) {
      return false
    }

    if (categoryQuizzes.length === 0) {
      return true
    }

    const levelModules = categoryQuizzes
      .filter((item) => item.level.slug === quiz.level.slug)
      .sort((a, b) => a.id - b.id)

    const currentIndex = levelModules.findIndex((item) => item.slug === quiz.slug)
    if (currentIndex <= 0) {
      return true
    }

    const previousModule = levelModules[currentIndex - 1]
    return isQuizCompleted(previousModule.slug)
  }, [categoryQuizzes, quiz])

  const isLastQuestion = useMemo(() => {
    if (!quiz) return false
    return currentQuestion >= quiz.questions.length - 1
  }, [currentQuestion, quiz])

  useEffect(() => {
    if (!quizStarted || !activeQuestion || submission) {
      return
    }
    setQuestionTimeLeft(questionTimeLimit(activeQuestion.difficulty))
  }, [activeQuestion, quizStarted, submission])

  useEffect(() => {
    if (!quizStarted || !activeQuestion || submission) {
      return
    }
    if (selectedAnswers[activeQuestion.id] !== undefined) {
      return
    }
    if (questionTimeLeft <= 0) {
      return
    }

    const timer = window.setInterval(() => {
      setQuestionTimeLeft((prev) => Math.max(prev - 1, 0))
    }, 1000)

    return () => window.clearInterval(timer)
  }, [activeQuestion, questionTimeLeft, quizStarted, selectedAnswers, submission])

  useEffect(() => {
    if (!quizStarted || !activeQuestion || submission) {
      return
    }
    if (selectedAnswers[activeQuestion.id] !== undefined) {
      return
    }
    if (questionTimeLeft > 0) {
      return
    }

    if (!isLastQuestion && quiz) {
      setCurrentQuestion((prev) => Math.min(prev + 1, quiz.questions.length - 1))
    }
  }, [activeQuestion, isLastQuestion, questionTimeLeft, quiz, quizStarted, selectedAnswers, submission])

  useEffect(() => {
    if (!slug || submission || !moduleIsUnlocked) {
      return
    }

    const hasProgress = quizStarted || currentQuestion > 0 || Object.keys(selectedAnswers).length > 0
    if (!hasProgress) {
      return
    }

    saveQuizSession(slug, {
      currentQuestion,
      selectedAnswers: Object.fromEntries(Object.entries(selectedAnswers).map(([questionId, choiceId]) => [String(questionId), choiceId])),
      quizStarted,
    })
  }, [currentQuestion, moduleIsUnlocked, quizStarted, selectedAnswers, slug, submission])

  if (!slug) {
    return <p className="error">Quiz introuvable.</p>
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!quiz) {
      return
    }

    try {
      setSubmitting(true)
      setSubmitError(null)
      const answers = Object.entries(selectedAnswers).map(([questionId, choiceId]) => ({
        question_id: Number(questionId),
        choice_id: choiceId,
      }))
      const result = await submitQuiz(quiz.slug, answers)
      setSubmission(result)
      if (result.percentage >= 90) {
        markQuizCompleted(quiz.slug)
      }
      clearQuizSession(quiz.slug)
      setCanResume(false)
    } catch (reason) {
      setSubmitError(reason instanceof Error ? reason.message : 'Erreur inconnue')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="ml-shell space-y-5">
      <header className="glass-card relative overflow-hidden p-5 sm:p-7">
        <div className="pointer-events-none absolute inset-0 data-grid-bg opacity-40" />
        <div className="relative space-y-4">
          <Link
            to="/"
            className="inline-flex items-center gap-2 rounded-full border border-stroke bg-white px-3 py-1.5 text-sm font-medium text-slate-600 transition hover:text-primary"
          >
            ← Retour au catalogue
          </Link>
        {quiz ? (
            <div className="space-y-2">
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">{normalizeFrenchText(quiz.category.title)}</p>
              <h1 className="font-display text-3xl font-extrabold text-slate-900 sm:text-4xl">{normalizeFrenchText(quiz.title)}</h1>
              <p className="max-w-3xl text-sm text-slate-600 sm:text-base">{normalizeFrenchText(quiz.description)}</p>
            </div>
          ) : null}
        </div>
      </header>

      {quiz && moduleIsUnlocked ? (
        <QuizStatsBar
          totalQuestions={quiz.questions.length}
          answeredQuestions={answeredQuestions}
          currentIndex={currentQuestion}
          scoreEstimate={scoreEstimate}
          questionTimeLeft={questionTimeLeft}
          questionTimeLimit={activeQuestionLimit}
        />
      ) : null}

      {loading ? <p className="text-sm text-slate-500">Chargement du quiz...</p> : null}
      {error ? <p className="text-sm font-medium text-danger">{error}</p> : null}

      {quiz && !moduleIsUnlocked ? (
        <section className="glass-card p-5 sm:p-6">
          <div className="space-y-4 text-center">
            <p className="text-sm text-slate-600">Vous devez terminer le niveau ou le module précédent.</p>
            <Link
              to={`/category/${quiz.category.slug}/level/${quiz.level.slug}`}
              className="inline-flex items-center justify-center rounded-xl bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-primary"
            >
              Retour au niveau
            </Link>
          </div>
        </section>
      ) : null}

      {quiz && moduleIsUnlocked && !startConfirmed ? (
        <section className="glass-card p-5 sm:p-6">
          <div className="space-y-4 text-center">
            <p className="text-sm text-slate-600">
              Le quiz se fait question par question. Réponds, puis la suivante s'affiche automatiquement.
            </p>
            <div className="flex flex-wrap items-center justify-center gap-3">
              <button
                type="button"
                onClick={() => {
                  setSelectedAnswers({})
                  setCurrentQuestion(0)
                  setQuizStarted(true)
                  setStartConfirmed(true)
                  setQuestionTimeLeft(60)
                  setCanResume(false)
                }}
                className="inline-flex items-center justify-center rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700"
              >
                Commencer
              </button>
              {canResume ? (
                <button
                  type="button"
                  onClick={() => {
                    setQuizStarted(true)
                    setStartConfirmed(true)
                  }}
                  className="inline-flex items-center justify-center rounded-xl border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-primary hover:text-primary"
                >
                  Reprendre
                </button>
              ) : null}
            </div>
          </div>
        </section>
      ) : null}

      {quiz && moduleIsUnlocked && quizStarted && startConfirmed ? (
        <form className="space-y-4" onSubmit={handleSubmit}>
          {activeQuestion ? (
            <article key={activeQuestion.id} className="glass-card animate-fade-in p-4 sm:p-6">
              <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
                <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-slate-600">
                  Question {currentQuestion + 1}
                </span>
                <div className="flex items-center gap-2">
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      activeQuestion.difficulty === 'easy'
                        ? 'bg-emerald-100 text-emerald-700'
                        : activeQuestion.difficulty === 'medium'
                          ? 'bg-amber-100 text-amber-700'
                          : 'bg-rose-100 text-rose-700'
                    }`}
                  >
                    {difficultyLabel(activeQuestion.difficulty)}
                  </span>
                  <span
                    className={`rounded-full px-3 py-1 text-xs font-semibold ${
                      questionTimeLeft <= 10 ? 'bg-rose-100 text-rose-700' : 'bg-slate-100 text-slate-700'
                    }`}
                  >
                    Chrono: {questionTimeLeft}s
                  </span>
                </div>
              </div>

              <h2 className="font-display text-xl font-semibold text-slate-900 sm:text-2xl">{normalizeFrenchText(activeQuestion.prompt)}</h2>

              {activeQuestion.presentation_type === 'image' && activeQuestion.image_url ? (
                <div className="mt-4 overflow-hidden rounded-2xl border border-stroke bg-slate-50">
                  <img
                    src={activeQuestion.image_url}
                    alt={`Illustration question ${currentQuestion + 1}`}
                    className="max-h-80 w-full object-cover"
                    loading="lazy"
                  />
                </div>
              ) : null}

              <div className="mt-4 grid gap-3">
                {activeQuestion.choices.map((choice) => {
                  const selectedChoiceId = selectedAnswers[activeQuestion.id]
                  const correctedAnswer = submission?.answers.find((answer) => answer.question_id === activeQuestion.id)
                  const isSelected = selectedChoiceId === choice.id
                  const state = correctedAnswer
                    ? choice.id === correctedAnswer.correct_choice_id
                      ? 'correct'
                      : isSelected
                        ? 'incorrect'
                        : 'idle'
                    : isSelected
                      ? 'selected'
                      : 'idle'

                  return (
                    <AnswerCard
                      key={choice.id}
                      selected={isSelected}
                      disabled={submitting || Boolean(submission)}
                      state={state}
                      onSelect={() => {
                        setSelectedAnswers((current) => ({
                          ...current,
                          [activeQuestion.id]: choice.id,
                        }))
                        if (!submission && !isLastQuestion) {
                          setCurrentQuestion((prev) => Math.min(prev + 1, quiz.questions.length - 1))
                        }
                      }}
                    >
                      {normalizeFrenchText(choice.label)}
                    </AnswerCard>
                  )
                })}
              </div>
            </article>
          ) : null}

          <div className="glass-card flex flex-col gap-3 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5">
            <div>
              <p className="text-sm font-medium text-slate-700">{answeredQuestions}/{quiz.questions.length} réponses sélectionnées</p>
              {submitError ? <p className="mt-1 text-sm font-medium text-danger">{submitError}</p> : null}
            </div>
            <button
              type="submit"
              className="inline-flex items-center justify-center rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-white transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={submitting}
            >
              {submitting ? 'Soumission...' : 'Terminer le quiz'}
            </button>
          </div>
        </form>
      ) : null}

      {submission ? (
        <section className="glass-card p-5 sm:p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold uppercase tracking-[0.2em] text-primary">Résultat</p>
              <h2 className="font-display text-2xl font-bold text-slate-900">{normalizeFrenchText(submission.quiz)}</h2>
            </div>
            <span className="rounded-2xl bg-slate-900 px-4 py-2 font-display text-2xl font-bold text-white">
              {submission.percentage}%
            </span>
          </div>

          {submission.percentage >= 90 ? (
            <p className="mt-3 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700">
              Module validé. Le suivant est débloqué.
            </p>
          ) : (
            <p className="mt-3 rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-sm font-semibold text-amber-700">
              Module non validé. Il faut au moins 90% de bonnes réponses pour débloquer le suivant.
            </p>
          )}

          <p className="mt-3 text-slate-700">
            Score: {submission.score}/{submission.total_questions}
          </p>

          <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {submission.answers.map((answer, index) => (
              <div
                key={answer.question_id}
                className={`rounded-2xl border p-4 ${
                  answer.is_correct ? 'border-success/30 bg-emerald-50' : 'border-danger/30 bg-rose-50'
                }`}
              >
                <p className="text-xs font-bold uppercase tracking-[0.12em] text-slate-500">Q{index + 1}</p>
                <p className={`mt-1 font-semibold ${answer.is_correct ? 'text-success' : 'text-danger'}`}>
                  {answer.is_correct ? 'Correcte' : 'Incorrecte'}
                </p>
                <p className="mt-1 text-sm text-slate-700">{normalizeFrenchText(answer.explanation)}</p>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  )
}