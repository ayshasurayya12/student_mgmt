from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from .models import Profile, Student, Course, Enrollment, EnrollmentRequest, DEPARTMENT_CHOICES


def send_email(to_email, subject, message):
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=True,
        )
    except Exception:
        pass


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
        student = Student.objects.create(user=user)
        messages.success(request, 'Account created! Please log in.')

        # Send welcome email
        if email:
            send_email(
                to_email=email,
                subject='Welcome to Learnthru!',
                message=f"""Hi {first_name or username},

Welcome to Learnthru! Your account has been created successfully.

Your login details:
Username: {username}
Roll Number: {student.roll_number}

You can now log in and browse available courses. Once you find a course you like, request enrollment and the principal will review your request.

— Learnthru Team"""
            )

        return redirect('login')
    return render(request, 'registration/register.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.role != 'student':
            messages.error(request, "Access denied.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@student_required
def student_dashboard(request):
    student = getattr(request.user, 'student', None)
    user_courses = list(
        Enrollment.objects.filter(student=student).select_related('course')
    ) if student else []
    all_courses = Course.objects.all().order_by('-created_at')[:6]
    return render(request, 'students/dashboard.html', {
        'student': student,
        'user_courses': user_courses,
        'all_courses': all_courses,
        'enrolled_count': len(user_courses),
        'total_courses': Course.objects.count(),
    })


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
    my_requests = EnrollmentRequest.objects.filter(
        student=student
    ).select_related('course').order_by('-requested_at')

    pending_count = my_requests.filter(status='pending').count()
    approved_count = my_requests.filter(status='approved').count()

    return render(request, 'students/profile.html', {
        'student': student,
        'enrolled_count': enrolled_count,
        'user_courses': user_courses,
        'my_requests': my_requests,
        'pending_count': pending_count,
        'approved_count': approved_count,
    })


@login_required
def course_list(request):
    query = request.GET.get('q', '')
    dept_filter = request.GET.get('dept', '')
    courses_qs = Course.objects.all()
    if query:
        courses_qs = courses_qs.filter(title__icontains=query)
    if dept_filter:
        courses_qs = courses_qs.filter(department=dept_filter)
    paginator = Paginator(courses_qs, 9)
    courses = paginator.get_page(request.GET.get('page'))

    enrolled_courses = []
    student_dept = None
    student_dept_display = None
    requested_course_ids = set()

    try:
        student = request.user.student
        enrolled_courses = [e.course for e in student.enrollment_set.all()]
        student_dept = student.department
        student_dept_display = student.get_department_display() if student.department else None
        requested_course_ids = set(
            EnrollmentRequest.objects.filter(student=student).values_list('course_id', flat=True)
        )
    except:
        pass

    return render(request, 'students/course_list.html', {
        'courses': courses,
        'enrolled_courses': enrolled_courses,
        'departments': DEPARTMENT_CHOICES,
        'selected_dept': dept_filter,
        'student_dept': student_dept,
        'student_dept_display': student_dept_display,
        'requested_course_ids': requested_course_ids,
    })


@login_required
def course_detail(request, pk):
    course = get_object_or_404(Course, pk=pk)
    is_enrolled = False
    is_locked = False
    request_status = None
    try:
        student = request.user.student
        is_enrolled = Enrollment.objects.filter(student=student, course=course).exists()
        if not is_enrolled and student.department and course.department:
            is_locked = student.department != course.department
        req = EnrollmentRequest.objects.filter(student=student, course=course).first()
        if req:
            request_status = req.status
    except:
        pass
    return render(request, 'students/course_detail.html', {
        'course': course,
        'is_enrolled': is_enrolled,
        'is_locked': is_locked,
        'request_status': request_status,
    })


@login_required
def request_enrollment(request, pk):
    if request.method == 'POST':
        course = get_object_or_404(Course, pk=pk)
        try:
            student = request.user.student
        except:
            messages.error(request, 'Student profile not found.')
            return redirect('course_list')

        if Enrollment.objects.filter(student=student, course=course).exists():
            messages.info(request, 'You are already enrolled.')
            return redirect('course_list')

        if EnrollmentRequest.objects.filter(student=student, course=course).exists():
            messages.info(request, 'You have already requested enrollment for this course.')
            return redirect('course_list')

        if student.department and course.department and student.department != course.department:
            messages.error(request, f'You can only enroll in {student.get_department_display()} courses.')
            return redirect('course_list')

        EnrollmentRequest.objects.create(student=student, course=course)
        messages.success(request, f'Enrollment request sent for {course.title}. Awaiting principal approval.')

        # Send email to student
        if student.user.email:
            send_email(
                to_email=student.user.email,
                subject='Enrollment Request Submitted — Learnthru',
                message=f"""Hi {student.user.get_full_name() or student.user.username},

Your enrollment request for "{course.title}" has been submitted successfully.

You will receive an email once the principal reviews your request.

Roll Number: {student.roll_number}
Course: {course.title}
Department: {course.get_department_display() if course.department else '—'}

— Learnthru Team"""
            )

        return redirect('course_list')

    return redirect('course_list')