from datetime import timedelta

def update_streak(profile, today):
    if profile.last_completed_date == today - timedelta(days=1):
        profile.daily_streak += 1
    elif profile.last_completed_date != today:
        profile.daily_streak = 1

    profile.last_completed_date = today

    if profile.daily_streak % 7 == 0:
        profile.weekly_streak += 1

    profile.save()
