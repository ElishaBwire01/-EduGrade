from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
User = get_user_model()
from core.models import Role, UserProfile
from teachers.models import TeacherProfile
from core.access import send_notification, send_approval_reminder
from datetime import datetime

def register(request):
    """User registration view"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validation
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'authentication/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already registered.')
            return render(request, 'authentication/register.html')
        
        # Create user
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        
        # Create user profile with default role
        role, created = Role.objects.get_or_create(
            name='TEACHER', 
            defaults={'description': 'Teacher Role'}
        )
        UserProfile.objects.create(user=user, role=role)
        
        # Create teacher profile automatically
        teacher = TeacherProfile.objects.create(
            user=user,
            staff_number=username,
            first_name=first_name,
            last_name=last_name,
            middle_name='',
            gender='M',
            date_of_birth='2000-01-01',
            phone_number='',
            email=email,
            address='',
            employment_date=datetime.now().date(),
            qualification='',
            specialization='',
            status='INACTIVE',
            is_active=False,
            created_via='SELF_REGISTER',
        )
        
        # Notify admins about new teacher
        send_approval_reminder(user)
        
        # Send welcome notification to teacher
        send_notification(
            user,
            title="Welcome to EduGrade!",
            message=(
                f"Welcome, {first_name}! Your account has been created successfully.\n\n"
                f"Next steps:\n"
                f"1. Complete your profile\n"
                f"2. Request admin approval to activate your account\n"
                f"3. Once approved, you can start entering marks and viewing reports\n\n"
                f"Click below to request approval now."
            ),
            notification_type="SYSTEM",
            url="/teachers/request-approval/",
        )
        
        # Log the user in
        login(request, user)
        messages.success(request, 'Registration successful! Welcome to EduGrade.')
        return redirect('core:dashboard')
    
    return render(request, 'authentication/register.html')


@login_required
def profile(request):
    """User profile view"""
    return render(request, 'authentication/profile.html', {'user': request.user})


@login_required
def profile_edit(request):
    teacher = TeacherProfile.objects.filter(user=request.user).first()
    if request.method == 'POST':
        request.user.first_name = request.POST.get('first_name', '').strip()
        request.user.last_name = request.POST.get('last_name', '').strip()
        request.user.email = request.POST.get('email', '').strip()
        request.user.save(update_fields=['first_name', 'last_name', 'email'])
        if teacher:
            old_tsc = teacher.tsc_number
            teacher.phone_number = request.POST.get('phone_number', '').strip()
            teacher.email = request.POST.get('email', '').strip()
            teacher.address = request.POST.get('address', '').strip()
            teacher.tsc_number = request.POST.get('tsc_number', '').strip() or None
            teacher.save(update_fields=['phone_number', 'email', 'address', 'tsc_number', 'updated_at'])
            if old_tsc != teacher.tsc_number:
                from core.models import AuditLog
                AuditLog.objects.create(
                    user=request.user,
                    action='UPDATE',
                    model_name='TeacherProfile',
                    object_id=str(teacher.id),
                    object_repr=teacher.full_name,
                    changes={'tsc_number': {'old': old_tsc, 'new': teacher.tsc_number}},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', ''),
                )
        messages.success(request, 'Profile updated successfully.')
        return redirect('authentication:profile')
    return render(request, 'authentication/profile_edit.html', {'user': request.user, 'teacher': teacher})
