from django.urls import path

from .views import (
    CategoryListAPIView,
    HealthCheckAPIView,
    QuizDetailAPIView,
    QuizListAPIView,
    QuizSubmitAPIView,
)

urlpatterns = [
    path('health/', HealthCheckAPIView.as_view(), name='health-check'),
    path('categories/', CategoryListAPIView.as_view(), name='category-list'),
    path('quizzes/', QuizListAPIView.as_view(), name='quiz-list'),
    path('quizzes/<slug:slug>/', QuizDetailAPIView.as_view(), name='quiz-detail'),
    path('quizzes/<slug:slug>/submit/', QuizSubmitAPIView.as_view(), name='quiz-submit'),
]