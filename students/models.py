from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import datetime


DEPARTMENT_CHOICES = [
    ('CS', 'Computer Application'),
    ('ENG', 'Communication & Language'),
    ('EC', 'Electronics & Communication'),
    ('MATH', 'Mathematics'),
    ('COM', 'Commerce'),
    ('BA', 'Business Administration'),
    ('AI', 'AI & ML'),
    ('DS','Data Science'),
]


def generate_roll_number():
    year = datetime.datetime.now().year
    count = Student.objects.filter(year_of_admission=year).count() + 1
    return f"LT{year}{count:04d}"


class Profile(models.Model):
    ROLE_CHOICES = [('principal', 'Principal'), ('student', 'Student')]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')

    def __str__(self):
        return f"{self.user.username} - {self.role}"


@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()





class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    roll_number = models.CharField(max_length=20, unique=True, blank=True)
    year_of_admission = models.IntegerField(blank=True, null=True)
    department = models.CharField(
        max_length=10,
        choices=DEPARTMENT_CHOICES,
        blank=True,
        null=True
    )
    profile_picture = models.ImageField(upload_to='student_pics/', blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.year_of_admission:
            self.year_of_admission = datetime.datetime.now().year
        if not self.roll_number:
            self.roll_number = generate_roll_number()
        super().save(*args, **kwargs)

    def get_department_display_name(self):
        return dict(DEPARTMENT_CHOICES).get(self.department, '—')

    def __str__(self):
        return f"{self.user.username} - {self.roll_number}"

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, blank=True, null=True)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.00)  
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def is_free(self):
        return self.price == 0


class Enrollment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'course')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # save first
        # Then update student department if course has one
        if self.course.department and not self.student.department:
            self.student.department = self.course.department
            self.student.save()

    def __str__(self):
        return f"{self.student} enrolled in {self.course}"
    
class EnrollmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student} → {self.course} ({self.status})"
    

