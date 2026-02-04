from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver



class Habit(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    time = models.TimeField()
    difficulty = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

class HabitLog(models.Model):
    habit = models.ForeignKey(Habit, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("habit","date")

class PlayerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    xp = models.IntegerField(default=0)
    daily_streak = models.IntegerField(default=0)
    weekly_streak = models.IntegerField(default=0)
    last_completed_date = models.DateField(null=True, blank=True)

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        PlayerProfile.objects.create(user=instance)

class DailyReflection(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)
    mood = models.IntegerField()
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ("user","date")



class GymLog(models.Model):
    BODY_PARTS = [
        ("chest", "Chest"),
        ("back", "Back"),
        ("shoulders", "Shoulders"),
        ("arms", "Arms"),
        ("legs", "Legs"),
        ("core", "Core"),
        ("calves", "Calves"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    body_part = models.CharField(max_length=20, choices=BODY_PARTS)
    date = models.DateField(default=timezone.now)

    class Meta:
        unique_together = ("user", "body_part", "date")

    def __str__(self):
        return f"{self.user} - {self.body_part} - {self.date}"


class WorkoutSet(models.Model):
    INTENSITY = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
    ]

    gym_log = models.ForeignKey(
        GymLog,
        on_delete=models.CASCADE,
        related_name="sets"
    )

    sets = models.IntegerField()
    reps = models.IntegerField()
    weight = models.FloatField(null=True, blank=True)
    duration_minutes = models.IntegerField(default=0)
    intensity = models.CharField(max_length=10, choices=INTENSITY)

    created_at = models.DateTimeField(auto_now_add=True)

    def training_load(self):
        """Simple scientific volume proxy"""
        return (self.sets * self.reps) * (self.weight or 1)

class StepsLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(default=timezone.now)

    steps = models.IntegerField()
    target = models.IntegerField(default=8000)

    class Meta:
        unique_together = ("user", "date")
