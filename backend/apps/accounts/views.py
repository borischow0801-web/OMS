from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.db import transaction
import threading
from .models import User
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer, ChangePasswordSerializer
)
from .bspplus_service import BspplusService


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """自定义Token序列化器，添加用户信息"""
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['role'] = user.role
        token['username'] = user.username
        return token
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        import logging
        logger = logging.getLogger(__name__)
        
        # 调用Bspplus登录接口
        bspplus_result = BspplusService.login(username, password)
        
        # 判断Bspplus接口是否可用
        # 如果接口调用失败（网络不通、超时等），回退到本地Django认证
        # 如果接口返回失败（账号密码错误），则不回退，直接返回错误
        is_network_error = bspplus_result.get('is_network_error', False) or \
                          bspplus_result.get('msg', '').startswith('登录服务异常') or \
                          bspplus_result.get('msg', '').startswith('登录处理异常')
        
        if not bspplus_result.get('success'):
            if is_network_error:
                # Bspplus接口不通，回退到本地Django认证
                logger.warning(f"Bspplus接口不可用，回退到本地认证: {bspplus_result.get('msg', '')}")
                
                # 使用Django的authenticate进行本地认证
                user = authenticate(username=username, password=password)
                
                if user is None or not user.is_active:
                    from rest_framework.exceptions import AuthenticationFailed
                    raise AuthenticationFailed('账号或密码错误')
                
                # 本地认证成功，设置用户对象
                self.user = user
                
                # 生成token
                refresh = self.get_token(user)
                data = {
                    'refresh': str(refresh),
                    'access': str(refresh.access_token),
                }
                
                # 添加用户信息到响应中
                from .serializers import UserSerializer
                user_serializer = UserSerializer(user)
                data.update(user_serializer.data)
                
                return data
            else:
                # Bspplus接口返回失败（账号密码错误），直接返回错误
                msg = bspplus_result.get('msg', '账号或密码错误')
                from rest_framework.exceptions import AuthenticationFailed
                raise AuthenticationFailed(msg)
        
        # Bspplus登录成功，获取Bspplus返回的用户信息
        if not bspplus_result.get('flag'):
            # 登录失败，返回错误信息
            msg = bspplus_result.get('msg', '账号或密码错误')
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed(msg)
        
        # 登录成功，获取Bspplus返回的用户信息
        bspplus_user_data = bspplus_result.get('user', {})
        
        # 获取或创建本地用户（同步执行，确保用户存在）
        user = BspplusService.sync_user_from_bspplus(bspplus_user_data)
        
        if not user:
            from rest_framework.exceptions import AuthenticationFailed
            raise AuthenticationFailed('用户信息同步失败')
        
        # 设置用户对象，供后续使用
        self.user = user
        
        # 同步用户信息到本地数据库（后台异步执行，不阻塞登录）
        # 这里再次同步是为了确保信息是最新的，但不会阻塞登录响应
        def sync_user_async():
            try:
                BspplusService.sync_user_from_bspplus(bspplus_user_data)
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"后台同步用户信息失败: {str(e)}")
        
        # 在后台线程中执行同步，不阻塞登录响应
        sync_thread = threading.Thread(target=sync_user_async)
        sync_thread.daemon = True
        sync_thread.start()
        
        # 生成token
        refresh = self.get_token(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        
        # 添加用户信息到响应中
        from .serializers import UserSerializer
        user_serializer = UserSerializer(user)
        data.update(user_serializer.data)
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """自定义Token获取视图"""
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    """用户视图集"""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer
    
    def get_permissions(self):
        if self.action == 'create':
            return [IsAdminUser()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """获取当前用户信息"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def employees(self, request):
        """获取员工列表（用于任务指派）"""
        employees = User.objects.filter(role='employee', is_active=True)
        serializer = self.get_serializer(employees, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def contractors(self, request):
        """获取承建方用户列表（项目经理和员工）"""
        contractors = User.objects.filter(role__in=['manager', 'employee'], is_active=True)
        serializer = self.get_serializer(contractors, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def change_password(self, request):
        """修改密码"""
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        if not user.check_password(serializer.validated_data['old_password']):
            return Response(
                {'error': '原密码错误'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'message': '密码修改成功'})

