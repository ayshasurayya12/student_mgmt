from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from students.models import Principal, Student, Course, Enrollment, Profile
from students.models import DEPARTMENT_CHOICES


# ── PRINCIPAL ONLY DECORATOR ──────────────────────────────────────────

def principal_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.profile.role != 'principal':
            messages.error(request, "Access denied. Principals only.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


# ── PRINCIPAL DASHBOARD ───────────────────────────────────────────────

@principal_required
def principal_dashboard(request):
    principal = getattr(request.user, 'principal', None)
    return render(request, 'principal/dashboard.html', {
        'principal':         principal,
        'total_students':    Student.objects.count(),
        'total_courses':     Course.objects.count(),
        'total_enrollments': Enrollment.objects.count(),
        'recent_students':   Student.objects.select_related('user').order_by('-id')[:5],
        'recent_courses':    Course.objects.order_by('-created_at')[:5],
    })


# ── PRINCIPAL PROFILE ─────────────────────────────────────────────────

@principal_required
def principal_profile(request):
    principal = getattr(request.user, 'principal', None)

    if request.method == 'POST':
        u = request.user
        u.first_name = request.POST.get('first_name', u.first_name)
        u.last_name  = request.POST.get('last_name',  u.last_name)
        u.email      = request.POST.get('email',      u.email)
        u.save()
        if principal:
            principal.employee_id = request.POST.get('employee_id', principal.employee_id)
            principal.designation = request.POST.get('designation', principal.designation)
            principal.phone       = request.POST.get('phone',       principal.phone)
            # ← removed principal.department (field doesn't exist)
            if 'profile_picture' in request.FILES:
                principal.profile_picture = request.FILES['profile_picture']
            principal.save()
        messages.success(request, "Profile updated!")
        return redirect('principal_profile')

    return render(request, 'principal/profile.html', {'principal': principal})


# ── STUDENT MANAGEMENT ────────────────────────────────────────────────

@principal_required
def student_list(request):
    q  = request.GET.get('q', '')
    qs = Student.objects.select_related('user').order_by('-id')
    if q:
        qs = qs.filter(
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q) |
            Q(user__username__icontains=q)   | Q(roll_number__icontains=q) |
            Q(department__icontains=q)
        )
    students = Paginator(qs, 10).get_page(request.GET.get('page'))
    return render(request, 'principal/student_list.html', {'students': students})


@principal_required
def student_detail(request, pk):
    student     = get_object_or_404(Student, pk=pk)
    enrollments = Enrollment.objects.filter(student=student).select_related('course')
    return render(request, 'principal/student_detail.html', {
        'student': student, 'enrollments': enrollments
    })


# In student_create view:
@principal_required
def student_create(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        password = request.POST.get('password', 'changeme123')

        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'principal/student_form.html', {'action': 'Create'})

        user = User.objects.create_user(
            username=username, password=password,
            email=email, first_name=first_name, last_name=last_name
        )
        user.profile.role = 'student'
        user.profile.save()

        # Auto roll_number + year generated in Student.save()
        Student.objects.create(user=user)

        messages.success(request, f'Student {username} created. Roll: {user.student.roll_number}')
        return redirect('principal_student_list')

    return render(request, 'principal/student_form.html', {'action': 'Create'})



# In student_edit view, remove department:
@principal_required
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    if request.method == 'POST':
        student.user.first_name = request.POST.get('first_name', '')
        student.user.last_name = request.POST.get('last_name', '')
        student.user.email = request.POST.get('email', '')
        student.user.save()

        # Don't overwrite roll_number or year — they're auto-set
        if 'profile_picture' in request.FILES:
            student.profile_picture = request.FILES['profile_picture']
        student.save()

        messages.success(request, 'Student updated successfully.')
        return redirect('principal_student_list')

    return render(request, 'principal/student_form.html', {
        'action': 'Edit',
        'student': student
    })

@principal_required
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    name = student.user.get_full_name() or student.user.username
    student.user.delete()
    messages.success(request, f"Student '{name}' deleted.")
    return redirect('principal_student_list')


# ── COURSE MANAGEMENT ─────────────────────────────────────────────────

@principal_required
def course_list(request):
    q = request.GET.get('q', '')
    dept_filter = request.GET.get('dept', '')
    qs = Course.objects.order_by('-created_at')
    
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    if dept_filter:
        qs = qs.filter(department=dept_filter)
    
    courses = Paginator(qs, 9).get_page(request.GET.get('page'))
    return render(request, 'principal/course_list.html', {
        'courses': courses,
        'departments': DEPARTMENT_CHOICES,   # ← was missing
        'selected_dept': dept_filter,         # ← was missing
    })


@principal_required
def course_detail(request, pk):
    course      = get_object_or_404(Course, pk=pk)
    enrollments = Enrollment.objects.filter(course=course).select_related('student__user')
    return render(request, 'principal/course_detail.html', {
        'course': course, 'enrollments': enrollments
    })


@principal_required
def course_create(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description', '')
        department = request.POST.get('department', '')

        Course.objects.create(
            title=title,
            description=description,
            department=department,
            created_by=request.user
        )
        messages.success(request, 'Course created successfully.')
        return redirect('principal_course_list')

    return render(request, 'principal/course_form.html', {
        'action': 'Create',
        'departments': DEPARTMENT_CHOICES,
    })

@principal_required
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description', '')
        course.department = request.POST.get('department', '')
        course.save()
        messages.success(request, 'Course updated successfully.')
        return redirect('principal_course_list')

    return render(request, 'principal/course_form.html', {
        'action': 'Edit',
        'course': course,
        'departments': DEPARTMENT_CHOICES,
    })



@principal_required
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    title  = course.title
    course.delete()
    messages.success(request, f"Course '{title}' deleted.")
    return redirect('principal_course_list')