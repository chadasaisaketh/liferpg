from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.utils import timezone
from .models import Habit, HabitLog
from datetime import datetime


def home(request):
    return render(request, 'home.html')


@api_view(['POST'])
def signup(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')

    if not username or not password:
        return Response(
            {"error": "Username and password required"},
            status=status.HTTP_400_BAD_REQUEST
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {"error": "Username already exists"},
            status=status.HTTP_400_BAD_REQUEST
        )

    User.objects.create_user(
        username=username,
        email=email,
        password=password
    )

    return Response(
        {"message": "User created successfully"},
        status=status.HTTP_201_CREATED
    )

def signup_page(request):
    return render(request, 'signup.html')

def login_page(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, "login.html")

def dashboard(request):
    return render(request, 'dashboard.html')




from datetime import datetime
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Habit, HabitLog

from .models import PlayerProfile

@api_view(['GET', 'POST', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def habits_api(request):

    # ---------- GET ----------
    if request.method == 'GET':
        today = timezone.now().date()
        habits = Habit.objects.filter(user=request.user).order_by('time')

        data = []
        for habit in habits:
            is_done = HabitLog.objects.filter(habit=habit, date=today).exists()

            data.append({
                'id': habit.id,
                'name': habit.name,
                'time': habit.time.strftime('%H:%M'),
                'difficulty': habit.difficulty,
                'done': is_done
            })

        return Response(data)

    # ---------- POST (CREATE) ----------
    if request.method == 'POST':
        name = request.data.get('name')
        time = request.data.get('time')
        difficulty = request.data.get('difficulty')

        time_obj = datetime.strptime(time, "%H:%M").time()

        habit = Habit.objects.create(
            user=request.user,
            name=name,
            time=time_obj,
            difficulty=difficulty
        )

        return Response({'status': 'created'})

    # ---------- PUT (EDIT) ----------
    if request.method == 'PUT':
        habit_id = request.data.get('id')
        habit = Habit.objects.get(id=habit_id, user=request.user)

        habit.name = request.data.get('name')
        habit.time = datetime.strptime(request.data.get('time'), "%H:%M").time()
        habit.difficulty = request.data.get('difficulty')

        habit.save()
        return Response({'status': 'updated'})

    # ---------- DELETE ----------
    if request.method == 'DELETE':
        habit_id = request.data.get('id')
        habit = Habit.objects.get(id=habit_id, user=request.user)
        habit.delete()

        return Response({'status': 'deleted'})

def habits_page(request):
    return render(request, 'habits.html')

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def toggle_habit_done(request, habit_id):

    today = timezone.now().date()
    habit = Habit.objects.get(id=habit_id, user=request.user)
    profile = PlayerProfile.objects.get(user=request.user)

    XP_MAP = {
        'easy': 10,
        'medium': 20,
        'hard': 30
    }

    log = HabitLog.objects.filter(habit=habit, date=today).first()
    xp_value = XP_MAP.get(habit.difficulty, 0)

    if log:
        # UNDO → REMOVE XP
        log.delete()
        profile.xp = max(0, profile.xp - xp_value)
        profile.save()

        return Response({
            "status": "undone",
            "xp": profile.xp
        })

    else:
        # DONE → ADD XP
        HabitLog.objects.create(habit=habit, date=today)
        profile.xp += xp_value
        profile.save()

        return Response({
            "status": "done",
            "xp": profile.xp
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def player_xp(request):
    profile, _ = PlayerProfile.objects.get_or_create(user=request.user)

    return Response({
        "xp": profile.xp
    })
