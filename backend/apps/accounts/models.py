from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """用户模型"""
    ROLE_CHOICES = [
        ('user', '使用方'),
        ('admin', '管理方'),
        ('manager', '承建方-项目经理'),
        ('employee', '承建方-员工'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='user', verbose_name='角色')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name='手机号')
    department = models.CharField(max_length=100, blank=True, null=True, verbose_name='部门')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name='头像')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    
    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_user(self):
        """是否为使用方"""
        return self.role == 'user'
    
    @property
    def is_admin(self):
        """是否为管理方"""
        return self.role == 'admin'
    
    @property
    def is_manager(self):
        """是否为项目经理"""
        return self.role == 'manager'
    
    @property
    def is_employee(self):
        """是否为员工"""
        return self.role == 'employee'
    
    @property
    def full_name(self):
        """完整姓名"""
        if self.first_name or self.last_name:
            return f"{self.last_name or ''}{self.first_name or ''}".strip() or self.username
        return self.username

