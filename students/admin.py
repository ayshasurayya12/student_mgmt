from django.contrib import admin
from .models import Profile, Student, Principal, Course, Enrollment, DEPARTMENT_CHOICES


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_filter = ('role',)
    search_fields = ('user__username', 'user__email')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'roll_number', 'department', 'year_of_admission')
    search_fields = ('user__username', 'user__first_name', 'roll_number')
    list_filter = ('department', 'year_of_admission')


@admin.register(Principal)
class PrincipalAdmin(admin.ModelAdmin):
    list_display = ('user', 'employee_id', 'designation', 'phone')
    search_fields = ('user__username', 'employee_id')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'department', 'created_by', 'created_at', 'enrollment_count')
    search_fields = ('title',)
    list_filter = ('department',)

    def enrollment_count(self, obj):
        return obj.enrollment_set.count()
    enrollment_count.short_description = 'Enrolled'


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'enrolled_at')
    list_filter = ('course__department',)
    search_fields = ('student__user__username', 'course__title')