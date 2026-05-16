from django.db import models

class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    treatment = models.CharField(max_length=200)

    total_amount = models.FloatField(default=0)
    paid_amount = models.FloatField(default=0)

    next_appointment = models.DateField(null=True, blank=True)
    is_manual_debt = models.BooleanField(default=False)
    is_appointment = models.BooleanField(default=False)
    is_today = models.BooleanField(default=False)
    has_appointment = models.BooleanField(default=False)
    added_to_today = models.BooleanField(default=False)
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('done', 'Done'),
        ('not_done', 'Not Done'),
    ]

    session_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    @property
    def remaining_amount(self):
        return self.total_amount - self.paid_amount