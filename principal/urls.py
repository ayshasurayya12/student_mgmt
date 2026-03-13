from django.urls import path
from . import views

urlpatterns = [
    path('principal/dashboard/',                    views.principal_dashboard, name='principal_dashboard'),
    path('principal/profile/',                      views.principal_profile,   name='principal_profile'),

    # Student management
    path('principal/students/',                     views.student_list,    name='principal_student_list'),
    path('principal/students/create/',              views.student_create,  name='principal_student_create'),
    path('principal/students/<int:pk>/',            views.student_detail,  name='principal_student_detail'),
    path('principal/students/<int:pk>/edit/',       views.student_edit,    name='principal_student_edit'),
    path('principal/students/<int:pk>/delete/',     views.student_delete,  name='principal_student_delete'),

    # Course management
    path('principal/courses/',                      views.course_list,    name='principal_course_list'),
    path('principal/courses/create/',               views.course_create,  name='principal_course_create'),
    path('principal/courses/<int:pk>/',             views.course_detail,  name='principal_course_detail'),
    path('principal/courses/<int:pk>/edit/',        views.course_edit,    name='principal_course_edit'),
    path('principal/courses/<int:pk>/delete/',      views.course_delete,  name='principal_course_delete'),
]