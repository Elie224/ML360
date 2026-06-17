import type { Category, QuizDetail, QuizListItem, SubmissionResponse } from './types'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    ...init,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status}`)
  }

  return response.json() as Promise<T>
}

export function fetchCategories() {
  return request<Category[]>('/categories/')
}

export function fetchQuizzes(category?: string, level?: string) {
  const params = new URLSearchParams()
  if (category) {
    params.set('category', category)
  }
  if (level) {
    params.set('level', level)
  }
  const query = params.toString() ? `?${params.toString()}` : ''
  return request<QuizListItem[]>(`/quizzes/${query}`)
}

export function fetchQuizDetail(slug: string) {
  return request<QuizDetail>(`/quizzes/${slug}/`)
}

export function submitQuiz(slug: string, answers: Array<{ question_id: number; choice_id: number }>) {
  return request<SubmissionResponse>(`/quizzes/${slug}/submit/`, {
    method: 'POST',
    body: JSON.stringify({ answers }),
  })
}