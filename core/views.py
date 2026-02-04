from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import (
    Habit,
    HabitLog,
    PlayerProfile,
    DailyReflection,
    GymLog,
    StepsLog,
    WorkoutSet,
    FoodLog,
    FoodTarget,
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

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def log_gym(request):
    import json
    data = json.loads(request.body)

    gym_log, _ = GymLog.objects.get_or_create(
        user=request.user,
        body_part=data["body_part"],
        date=timezone.now().date()
    )

    WorkoutSet.objects.create(
        gym_log=gym_log,
        sets=int(data.get("sets", 0)),
        reps=int(data.get("reps", 0)),
        weight=float(data.get("weight") or 0),
        duration_minutes=int(data.get("duration_minutes", 0)),
        intensity=data.get("intensity", "medium")
    )

    return JsonResponse({"status": "logged"})

# ======================================================
# MUSCLE SYMMETRY (WORKING)
# ======================================================

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def weekly_symmetry(request):
    start = timezone.now().date() - timedelta(days=6)
    loads = {}
    total = 0

    for part, _ in GymLog.BODY_PARTS:
        load = sum(
            s.training_load()
            for s in WorkoutSet.objects.filter(
                gym_log__user=request.user,
                gym_log__body_part=part,
                gym_log__date__gte=start
            )
        )
        loads[part] = load
        total += load

    return JsonResponse({
        part: {
            "percent": int((load / total) * 100) if total else 0,
            "status": "balanced" if 10 <= (load / total * 100 if total else 0) <= 25
            else "under" if load else "over"
        }
        for part, load in loads.items()
    })

# ======================================================
# ✅ WEEKLY LOAD (FIXED, FINAL)
# ======================================================
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def weekly_trend(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    data = {}
    for i in range(7):
        day = start + timedelta(days=i)
        load = sum(
            s.training_load()
            for s in WorkoutSet.objects.filter(
                gym_log__user=request.user,
                gym_log__date=day
            )
        )
        data[day.strftime("%a")] = load

    return JsonResponse(data)

# ======================================================
# ✅ RECOVERY SCORE (FIXED – THIS WAS THE ISSUE)
# ======================================================
def body_page(request):
    return render(request, "body.html")
@api_view(["GET"])
@permission_classes([IsAuthenticated])
def recovery_score(request):
    today = timezone.now().date()

    today_load = sum(
        s.training_load()
        for s in WorkoutSet.objects.filter(
            gym_log__user=request.user,
            gym_log__date=today
        )
    )

    past_sets = WorkoutSet.objects.filter(
        gym_log__user=request.user,
        gym_log__date__lt=today,
        gym_log__date__gte=today - timedelta(days=6)
    )

    past_load = sum(s.training_load() for s in past_sets)
    avg_load = past_load / 6 if past_load else 0

    if avg_load == 0:
        score = 100
    else:
        fatigue = today_load / avg_load
        score = int(max(0, min(100, 100 - fatigue * 40)))

    loads = weekly_load_array(request.user)

    warning = None
    if loads[-1] > sum(loads[:-1]) / 6 * 1.6:
        warning = "⚠ Sudden spike — injury risk"
    elif all(l < 50 for l in loads):
        warning = "⚠ Load too low — no progression"

    return Response({
        "score": score,
        "warning": warning
    })
# ======================================================
# STEPS (ALREADY WORKING)
# ======================================================

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def steps_api(request):
    today = timezone.now().date()

    if request.method == "POST":
        StepsLog.objects.update_or_create(
            user=request.user,
            date=today,
            defaults={
                "steps": int(request.data["steps"]),
                "target": int(request.data.get("target", 8000))
            }
        )
        return Response({"status": "saved"})

    log = StepsLog.objects.filter(user=request.user, date=today).first()
    return Response({
        "steps": log.steps if log else 0,
        "target": log.target if log else 8000
    })


@login_required(login_url="/")
def weekly_steps(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    data = {}

    for i in range(7):
        day = start + timedelta(days=i)
        log = StepsLog.objects.filter(user=request.user, date=day).first()
        data[day.strftime("%a")] = log.steps if log else 0

    return JsonResponse(data)

def weekly_load_array(user):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    loads = []
    for i in range(7):
        day = start + timedelta(days=i)
        sets = WorkoutSet.objects.filter(
            gym_log__user=user,
            gym_log__date=day
        )
        loads.append(sum(s.training_load() for s in sets))
    return loads

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def food_api(request):
    today = timezone.now().date()

    if request.method == "POST":
        FoodLog.objects.update_or_create(
            user=request.user,
            date=today,
            defaults=request.data
        )
        return Response({"status": "saved"})

    log = FoodLog.objects.filter(user=request.user, date=today).first()

    if not log:
        return Response({"empty": True})

    return Response({
        "calories": log.calories,
        "protein": log.protein,
        "carbs": log.carbs,
        "fats": log.fats,
        "targets": {
            "calories": log.target_calories,
            "protein": log.target_protein,
            "carbs": log.target_carbs,
            "fats": log.target_fats,
        },
        "micros": {
            "fiber": log.fiber,
            "iron": log.iron,
            "calcium": log.calcium,
            "vitamin_d": log.vitamin_d,
            "b12": log.b12,
        }
    })

def food_page(request):
    return render(request, "food.html")


def safe_int(val, default):
    try:
        return int(val)
    except (TypeError, ValueError):
        return default


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def food_today(request):
    today = timezone.now().date()

    log, _ = FoodLog.objects.get_or_create(
        user=request.user,
        date=today
    )

    target, _ = FoodTarget.objects.get_or_create(
        user=request.user
    )

    profile = PlayerProfile.objects.get(user=request.user)
    xp_awarded = False

    if request.method == "POST":
        # ---------- SAVE VALUES ----------
        log.calories = safe_int(request.data.get("calories"), log.calories)
        log.protein  = safe_int(request.data.get("protein"), log.protein)
        log.carbs    = safe_int(request.data.get("carbs"), log.carbs)
        log.fats     = safe_int(request.data.get("fats"), log.fats)

        log.micronutrients = request.data.get(
            "micronutrients", log.micronutrients
        ) or log.micronutrients

        log.vitamins = request.data.get(
            "vitamins", log.vitamins
        ) or log.vitamins

        log.save()

        # ---------- PROTEIN STREAK ----------
        yesterday = today - timedelta(days=1)

        if log.protein >= target.protein:
            if FoodLog.objects.filter(
                user=request.user,
                date=yesterday,
                protein__gte=target.protein
            ).exists():
                profile.protein_streak += 1
            else:
                profile.protein_streak = 1
        else:
            profile.protein_streak = 0

        # ---------- FOOD XP (ONCE PER DAY) ----------
        food_xp = 0

        if log.calories >= int(target.calories * 0.95):
            food_xp += 20

        if log.protein >= int(target.protein * 0.90):
            food_xp += 20

        if food_xp > 0 and not log.food_xp_awarded:
            profile.xp += food_xp
            log.food_xp_awarded = True
            xp_awarded = True

        profile.save()
        log.save()

    return Response({
        "log": {
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fats": log.fats,
            "micronutrients": log.micronutrients,
            "vitamins": log.vitamins,
        },
        "target": {
            "calories": target.calories,
            "protein": target.protein,
            "carbs": target.carbs,
            "fats": target.fats,
        },
        "xp_awarded": xp_awarded,
        "protein_streak": profile.protein_streak
    })



@api_view(["POST"])
@permission_classes([IsAuthenticated])
def food_target(request):
    FoodTarget.objects.update_or_create(
        user=request.user,
        defaults={
            "calories": request.data.get("calories", 2000),
            "protein": request.data.get("protein", 100),
            "carbs": request.data.get("carbs", 250),
            "fats": request.data.get("fats", 70),
        }
    )
    return Response({"status": "target_saved"})

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def weekly_food_compliance(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)
    target = FoodTarget.objects.get(user=request.user)

    data = {}

    for i in range(7):
        day = start + timedelta(days=i)
        log = FoodLog.objects.filter(user=request.user, date=day).first()

        if not log:
            data[day.strftime("%a")] = 0
            continue

        calorie_ok = abs(log.calories - target.calories) <= target.calories * 0.05
        protein_ok = log.protein >= target.protein

        data[day.strftime("%a")] = 1 if calorie_ok and protein_ok else 0

    return Response(data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def food_weekly_average(request):
    today = timezone.now().date()
    start = today - timedelta(days=6)

    logs = FoodLog.objects.filter(
        user=request.user,
        date__gte=start
    )

    total = sum(l.calories for l in logs)
    days = logs.count() or 1

    return Response({
        "average": int(total / days)
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def food_daily_comparison(request):
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)

    today_log = FoodLog.objects.filter(user=request.user, date=today).first()
    yesterday_log = FoodLog.objects.filter(user=request.user, date=yesterday).first()

    today_cal = today_log.calories if today_log else 0
    yest_cal  = yesterday_log.calories if yesterday_log else 0

    diff = today_cal - yest_cal

    if diff > 0:
        trend = "up"
    elif diff < 0:
        trend = "down"
    else:
        trend = "same"

    return Response({
        "today": today_cal,
        "yesterday": yest_cal,
        "difference": diff,
        "trend": trend
    })

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def food_monthly_heatmap(request):
    today = timezone.now().date()
    start = today.replace(day=1)

    target = FoodTarget.objects.get(user=request.user)
    logs = FoodLog.objects.filter(
        user=request.user,
        date__gte=start,
        date__lte=today
    )

    data = {}

    for log in logs:
        diff = log.calories - target.calories

        if abs(diff) <= target.calories * 0.05:
            level = "perfect"
        elif abs(diff) <= target.calories * 0.15:
            level = "ok"
        else:
            level = "bad"

        data[str(log.date)] = {
            "calories": log.calories,
            "level": level
        }

    return Response(data)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def food_by_date(request):
    date_str = request.GET.get("date")
    if not date_str:
        return Response({"error": "date required"}, status=400)

    try:
        date = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return Response({"error": "invalid date"}, status=400)

    log = FoodLog.objects.filter(user=request.user, date=date).first()
    target = FoodTarget.objects.get(user=request.user)

    if not log:
        return Response({"empty": True, "date": date_str})

    return Response({
        "date": date_str,
        "log": {
            "calories": log.calories,
            "protein": log.protein,
            "carbs": log.carbs,
            "fats": log.fats,
            "micronutrients": log.micronutrients,
            "vitamins": log.vitamins,
        },
        "target": {
            "calories": target.calories,
            "protein": target.protein,
            "carbs": target.carbs,
            "fats": target.fats,
        }
    })
