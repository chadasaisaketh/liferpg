from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta

from .models import (
    Habit, HabitLog,
    PlayerProfile,
    DailyReflection
)

# ======================================================
# AUTH / PAGES
# ======================================================

def login_page(request):
    return render(request, "login.html")

def signup_page(request):
    return render(request, "signup.html")


def dashboard(request):
    return render(request, "dashboard.html")


def habits_page(request):
    return render(request, "habits.html")

def reflection_history_page(request):
    return render(request, "reflection_history.html")


# ======================================================
# AUTH API
# ======================================================

@api_view(["POST"])
def signup(request):
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response({"error": "Missing fields"}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({"error": "Username exists"}, status=400)

    User.objects.create_user(username=username, password=password)
    return Response({"status": "created"}, status=201)


# ======================================================
# STREAK UTILS
# ======================================================

def update_streak(profile, today):
    if profile.last_completed_date == today - timedelta(days=1):
        profile.daily_streak += 1
    elif profile.last_completed_date != today:
        profile.daily_streak = 1

    profile.last_completed_date = today

    if profile.daily_streak % 7 == 0:
        profile.weekly_streak += 1

    profile.save()


# ======================================================
# HABITS API
# ======================================================

@api_view(["GET", "POST", "PUT", "DELETE"])
@permission_classes([IsAuthenticated])
def habits_api(request):
    today = timezone.now().date()

    if request.method == "GET":
        data = []
        for h in Habit.objects.filter(user=request.user).order_by("time"):
            done = HabitLog.objects.filter(habit=h, date=today).exists()
            data.append({
                "id": h.id,
                "name": h.name,
                "time": h.time.strftime("%H:%M"),
                "difficulty": h.difficulty,
                "done": done
            })
        return Response(data)

    if request.method == "POST":
        Habit.objects.create(
            user=request.user,
            name=request.data["name"],
            time=datetime.strptime(request.data["time"], "%H:%M").time(),
            difficulty=request.data["difficulty"]
        )
        return Response({"status": "created"})

    if request.method == "PUT":
        h = Habit.objects.get(id=request.data["id"], user=request.user)
        h.name = request.data["name"]
        h.time = datetime.strptime(request.data["time"], "%H:%M").time()
        h.difficulty = request.data["difficulty"]
        h.save()
        return Response({"status": "updated"})

    if request.method == "DELETE":
        Habit.objects.get(id=request.data["id"], user=request.user).delete()
        return Response({"status": "deleted"})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def toggle_habit_done(request, habit_id):
    today = timezone.now().date()
    habit = Habit.objects.get(id=habit_id, user=request.user)
    profile = PlayerProfile.objects.get(user=request.user)

    XP = {"easy": 10, "medium": 20, "hard": 30}.get(habit.difficulty, 0)

    log = HabitLog.objects.filter(habit=habit, date=today).first()

    if log:
        log.delete()
        profile.xp = max(0, profile.xp - XP)
        profile.save()
        return Response({"status": "undone", "xp": profile.xp})

    HabitLog.objects.create(habit=habit, date=today)
    profile.xp += XP
    update_streak(profile, today)
    return Response({"status": "done", "xp": profile.xp})


# ======================================================
# XP + PROGRESS
# ======================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def player_xp(request):
    return Response({"xp": PlayerProfile.objects.get(user=request.user).xp})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def daily_habit_progress(request):
    today = timezone.now().date()
    total = Habit.objects.filter(user=request.user).count()
    done = HabitLog.objects.filter(habit__user=request.user, date=today).count()
    return Response({"percent": int((done / total) * 100) if total else 0})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def weekly_progress(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    days = {}
    for i in range(7):
        day = start + timedelta(days=i)
        days[day.strftime("%a")] = HabitLog.objects.filter(
            habit__user=request.user,
            date=day
        ).count()

    p = PlayerProfile.objects.get(user=request.user)
    return Response({
        "days": days,
        "daily_streak": p.daily_streak,
        "weekly_streak": p.weekly_streak
    })


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def monthly_heatmap(request):
    today = timezone.now().date()
    start = today.replace(day=1)

    heatmap = {}
    for log in HabitLog.objects.filter(
        habit__user=request.user,
        date__gte=start,
        date__lte=today
    ):
        key = str(log.date)
        heatmap[key] = heatmap.get(key, 0) + 1

    return Response(heatmap)


# ======================================================
# REFLECTION
# ======================================================

@api_view(["POST", "GET"])
@permission_classes([IsAuthenticated])
def daily_reflection(request):
    today = timezone.now().date()

    if request.method == "POST":
        DailyReflection.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={
                "mood": request.data["mood"],
                "note": request.data.get("note", "")
            }
        )
        return Response({"status": "saved"})

    reflections = DailyReflection.objects.filter(user=request.user).order_by("-date")
    return Response([
        {"date": r.date, "mood": r.mood, "note": r.note}
        for r in reflections
    ])
