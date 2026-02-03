from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.views import (
    signup,
    signup_page,
    login_page,
    dashboard,
    habits_page,
    habits_api,
    toggle_habit_done,
    player_xp,

    # 🔽 SAFE ADDITIONS
    daily_habit_progress,
    weekly_progress,
    monthly_heatmap,
    daily_reflection,
    reflection_history_page,
)

urlpatterns = [

    # 🔐 ROOT → LOGIN (FIRST PAGE ALWAYS)
    path('', login_page, name='login'),

    path('admin/', admin.site.urls),

    # Auth pages
    path('signup/', signup_page),
    path('login/', login_page),

    # App pages
    path('dashboard/', dashboard),
    path('habits/', habits_page),
    path('reflections/', reflection_history_page),

    # Habits APIs
    path('api/habits/', habits_api),
    path('api/habits/<int:habit_id>/toggle/', toggle_habit_done),
    path('api/xp/', player_xp),

    # Progress APIs
    path('api/habits/progress/daily/', daily_habit_progress),
    path('api/habits/progress/weekly/', weekly_progress),
    path('api/habits/progress/monthly/', monthly_heatmap),

    # Reflection API
    path('api/reflection/', daily_reflection),

    # Auth APIs
    path('api/signup/', signup),
    path('api/login/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]
