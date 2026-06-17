from django.contrib import admin

from .models import Category, Choice, Level, Question, Quiz


class LevelInline(admin.TabularInline):
	model = Level
	extra = 4


class ChoiceInline(admin.TabularInline):
	model = Choice
	extra = 1


class QuestionInline(admin.StackedInline):
	model = Question
	extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('title', 'slug')
	prepopulated_fields = {'slug': ('title',)}
	search_fields = ('title',)
	inlines = [LevelInline]


@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'objective', 'order')
	list_filter = ('category',)
	search_fields = ('title', 'objective')
	prepopulated_fields = {'slug': ('title',)}


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
	list_display = ('title', 'category', 'level', 'source_level_name', 'is_published', 'updated_at')
	list_filter = ('category', 'level', 'is_published')
	prepopulated_fields = {'slug': ('title',)}
	search_fields = ('title', 'description')
	inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
	list_display = ('quiz', 'order', 'question_type', 'presentation_type', 'difficulty')
	list_filter = ('quiz__category', 'question_type', 'presentation_type', 'difficulty')
	search_fields = ('prompt',)
	inlines = [ChoiceInline]
