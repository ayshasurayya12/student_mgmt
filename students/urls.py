from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Shared auth
    path('',          views.login_view,    name='login'),
    path('login/',    views.login_view,    name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/',   views.logout_view,   name='logout'),

    # Password reset
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset.html'),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('password-reset-complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # Student pages
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/profile/',   views.student_profile,   name='student_profile'),
    path('student/courses/',   views.course_list,        name='course_list'),
    path('student/courses/<int:pk>/',        views.course_detail,  name='course_detail'),
    path('student/courses/<int:pk>/enroll/', views.enroll_course,  name='enroll_course'),
]