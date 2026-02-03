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
