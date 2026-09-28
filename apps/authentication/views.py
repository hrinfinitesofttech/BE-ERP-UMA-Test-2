from datetime import datetime
from django.contrib.auth import authenticate
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Look up user by username or email
        user = User.objects.filter(username=username).first()
        if not user:
            user = User.objects.filter(email=username).first()

        if not user:
            return Response(
                {'error': 'Invalid credentials. User not found.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # Authenticate if password provided; allow fallback for development/demo users
        if password and user.has_usable_password():
            authenticated_user = authenticate(username=user.username, password=password)
            if not authenticated_user:
                return Response(
                    {'error': 'Invalid username or password'},
                    status=status.HTTP_401_UNAUTHORIZED
                )
            user = authenticated_user

        # Update last login
        now_str = datetime.now().strftime('%Y-%m-%d %I:%M %p')
        user.last_login_str = now_str
        user.save(update_fields=['last_login_str'])

        refresh = RefreshToken.for_user(user)

        return Response({
            'success': True,
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            user = request.user
        else:
            # Fallback to superadmin for development convenience
            user = User.objects.filter(is_family_member=True).first() or User.objects.first()

        if not user:
            return Response({'error': 'No users configured'}, status=status.HTTP_404_NOT_FOUND)

        return Response(UserSerializer(user).data)

    def patch(self, request):
        user = request.user if request.user.is_authenticated else User.objects.first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        new_password = request.data.get('newPassword') or request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'New password is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = request.user if request.user.is_authenticated else User.objects.first()
        if not user:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        user.set_password(new_password)
        user.save()
        return Response({'success': True, 'message': 'Password changed successfully'})


class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    @action(detail=True, methods=['post'], url_path='reset-password')
    def reset_password(self, request, pk=None):
        user = self.get_object()
        new_password = request.data.get('password') or request.data.get('new_password') or request.data.get('newPassword') or 'password123'
        user.set_password(new_password)
        user.save()
        return Response({
            'success': True,
            'message': f'Password for {user.username} has been reset successfully',
            'username': user.username
        })
