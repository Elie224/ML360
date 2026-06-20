export type Level = {
  id: number
  title: string
  slug: string
  objective: string
  order: number
}

export type Category = {
  id: number
  title: string
  slug: string
  description: string
  quizzes_count: number
  levels: Level[]
}

export type QuizListItem = {
  id: number
  title: string
  slug: string
  description: string
  source_level_name: string
  is_published: boolean
  question_count: number
  level: Level
  category: Category
}

export type QuestionChoice = {
  id: number
  label: string
  order: number
}

export type QuizQuestion = {
  id: number
  prompt: string
  order: number
  question_type: string
  presentation_type: 'text' | 'image'
  image_url: string
  difficulty: 'easy' | 'medium' | 'hard'
  choices: QuestionChoice[]
}

export type QuizDetail = {
  id: number
  title: string
  slug: string
  description: string
  source_level_name: string
  level: Level
  category: Category
  questions: QuizQuestion[]
}

export type SubmissionResponse = {
  quiz: string
  score: number
  total_questions: number
  percentage: number
  answers: Array<{
    question_id: number
    selected_choice_id: number | null
    correct_choice_id: number
    is_correct: boolean
    explanation: string
  }>
}