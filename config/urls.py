from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from core.views import home, signup, signup_page, login_page, dashboard,habits_page,habits_api, toggle_habit_done,player_xp 



urlpatterns = [
    
    path('', login_view, name='login'),
    path('admin/', admin.site.urls),
    path('signup/', signup_page),
    path('login/', login_page),
    path('dashboard/', dashboard),
    path('habits/', habits_page),
    path('api/habits/', habits_api),
    path('api/habits/<int:habit_id>/toggle/', toggle_habit_done),
    path('api/xp/', player_xp),

    path('api/signup/', signup),  # 👈 ADD THIS
    path('api/login/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
]
