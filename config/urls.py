from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from core.views import (
    # Pages
    login_page,
    signup_page,
    dashboard,
    habits_page,
    reflection_history_page,
    body_page,

    # Auth / Users
    signup,
    player_xp,

    # Habits
    habits_api,
    toggle_habit_done,
    daily_habit_progress,
    weekly_progress,
    monthly_heatmap,

    # Reflection
    daily_reflection,

    # Body
    log_gym,
    weekly_symmetry,
    weekly_trend,
    recovery_score,
    steps_api,
    weekly_steps,
)

urlpatterns = [

    # =========================
    # ROOT / ADMIN
    # =========================
    path("", login_page, name="login"),
    path("admin/", admin.site.urls),
    path("api/body/steps/weekly/", weekly_steps),

    # =========================
    # AUTH PAGES
    # =========================
    path("login/", login_page),
    path("signup/", signup_page),

    # =========================
    # APP PAGES
    # =========================
    path("dashboard/", dashboard),
    path("habits/", habits_page),
    path("reflections/", reflection_history_page),
    path("body/", body_page),

    # =========================
    # AUTH APIs (JWT)
    # =========================
    path("api/signup/", signup),
    path("api/login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # =========================
    # HABITS APIs
    # =========================
    path("api/habits/", habits_api),
    path("api/habits/<int:habit_id>/toggle/", toggle_habit_done),
    path("api/xp/", player_xp),

    # =========================
    # HABIT PROGRESS APIs
    # =========================
    path("api/habits/progress/daily/", daily_habit_progress),
    path("api/habits/progress/weekly/", weekly_progress),
    path("api/habits/progress/monthly/", monthly_heatmap),

    # =========================
    # REFLECTION API
    # =========================
    path("api/reflection/", daily_reflection),

    # =========================
    # BODY APIs
    # =========================
    path("api/body/gym/", log_gym),
    path("api/body/symmetry/", weekly_symmetry),
    path("api/body/trend/", weekly_trend),      # 📈 weekly load trend
    path("api/body/recovery/", recovery_score), # 🧠 recovery score
    path("api/body/steps/", steps_api),
]
