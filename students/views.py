from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Q
from .models import Profile, Student, Course, Enrollment


# ── SHARED LOGIN / REGISTER / LOGOUT ──────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        if request.user.profile.role == 'principal':
            return redirect('principal_dashboard')
        return redirect('student_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            if user.profile.role == 'principal':
                return redirect('principal_dashboard')
            return redirect('student_dashboard')
        else:
            messages.error(request, "Invalid username or password.")

    return render(request, 'registration/login.html')


# In register_view, change the Student creation:
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        email = request.POST.get('email', '')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')

        if password1 != password2:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'registration/register.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already taken.')
            return render(request, 'registration/register.html')

        user = User.objects.create_user(
            username=username, password=password1,
            email=email, first_name=first_name, last_name=last_name
        )
        user.profile.role = 'student'
        user.profile.save()

        # Student is created with auto roll_number and year — no department
        Student.objects.create(user=user)

        messages.success(request, 'Account created! Please log in.')
        return redirect('login')

    return render(request, 'registration/register.html')




def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out.")
    return redirect('login')


# ── STUDENT ONLY DECORATOR ────────────────────────────────────────────

def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.role != 'student':
            messages.error(request, "Access denied.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── STUDENT DASHBOARD ─────────────────────────────────────────────────

@student_required
def student_dashboard(request):
    student = getattr(request.user, 'student', None)
    user_courses = list(
        Enrollment.objects.filter(student=student).select_related('course')
    ) if student else []
    all_courses = Course.objects.all().order_by('-created_at')[:6]

    return render(request, 'students/dashboard.html', {
        'student':        student,
        'user_courses':   user_courses,
        'all_courses':    all_courses,
        'enrolled_count': len(user_courses),
        'total_courses':  Course.objects.count(),
    })


# ── STUDENT PROFILE ───────────────────────────────────────────────────

# In student_profile view, remove department from POST handling:
@login_required
def student_profile(request):
    try:
        student = request.user.student
    except:
        student = Student.objects.create(user=request.user)

    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()

        if 'profile_picture' in request.FILES:
            student.profile_picture = request.FILES['profile_picture']
        student.save()

        messages.success(request, 'Profile updated successfully.')
        return redirect('student_profile')

    enrolled_count = student.enrollment_set.count()
    user_courses = student.enrollment_set.select_related('course').all()

    return render(request, 'students/profile.html', {
        'student': student,
        'enrolled_count': enrolled_count,
        'user_courses': user_courses,
    })


# ── COURSE BROWSING & ENROLLMENT (students only) ──────────────────────

@login_required
def course_list(request):
    from .models import Course, DEPARTMENT_CHOICES
    from django.core.paginator import Paginator

    query = request.GET.get('q', '')
    dept_filter = request.GET.get('dept', '')

    courses_qs = Course.objects.all()

    if query:
        courses_qs = courses_qs.filter(title__icontains=query)

    if dept_filter:
        courses_qs = courses_qs.filter(department=dept_filter)

    paginator = Paginator(courses_qs, 9)
    page = request.GET.get('page')
    courses = paginator.get_page(page)

    enrolled_courses = []
    try:
        student = request.user.student
        enrolled_courses = [e.course for e in student.enrollment_set.all()]
    except:
        pass

    return render(request, 'students/course_list.html', {
        'courses': courses,
        'enrolled_courses': enrolled_courses,
        'departments': DEPARTMENT_CHOICES,
        'selected_dept': dept_filter,
    })



@student_required
def course_detail(request, pk):
    course  = get_object_or_404(Course, pk=pk)
    student = getattr(request.user, 'student', None)
    is_enrolled = Enrollment.objects.filter(
        student=student, course=course
    ).exists() if student else False

    return render(request, 'students/course_detail.html', {
        'course': course, 'is_enrolled': is_enrolled,
    })


@login_required
def enroll_course(request, pk):
    from .models import Course, Enrollment
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=pk)
        try:
            student = request.user.student
        except:
            messages.error(request, 'Student profile not found.')
            return redirect('course_list')

        # Check if already enrolled
        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.info(request, 'Already enrolled in this course.')
            return redirect('course_list')

        # Create enrollment — department auto-updates inside Enrollment.save()
        Enrollment.objects.create(student=student, course=course)
        messages.success(request, f'Enrolled in {course.title}! Your department is now set to {course.get_department_display()}.')
        return redirect('course_list')

    return redirect('course_list')