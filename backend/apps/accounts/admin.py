import os
import tempfile
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import HttpResponse, FileResponse
from django.conf import settings
from django.utils.html import format_html
from django.urls import reverse
from .models import User
from .import_service import UserImportService


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'department', 'is_active', 'created_at')
    list_filter = ('role', 'is_active', 'is_staff', 'created_at')
    search_fields = ('username', 'first_name', 'last_name', 'email', 'phone')
    fieldsets = BaseUserAdmin.fieldsets + (
        ('额外信息', {'fields': ('role', 'phone', 'department', 'avatar')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('额外信息', {'fields': ('role', 'phone', 'department', 'email')}),
    )
    
    def get_urls(self):
        """添加自定义URL"""
        urls = super().get_urls()
        custom_urls = [
            path('import/', self.admin_site.admin_view(self.import_users_view), name='accounts_user_import'),
            path('download-template/', self.admin_site.admin_view(self.download_template_view), name='accounts_user_download_template'),
        ]
        return custom_urls + urls
    
    def import_users_view(self, request):
        """用户批量导入视图"""
        if request.method == 'POST':
            if 'excel_file' not in request.FILES:
                messages.error(request, '请选择要导入的Excel文件')
                return render(request, 'admin/accounts/user/import.html', {
                    'title': '批量导入用户',
                    'opts': self.model._meta,
                })
            
            excel_file = request.FILES['excel_file']
            
            # 验证文件格式
            if not excel_file.name.endswith(('.xlsx', '.xls')):
                messages.error(request, '请上传Excel文件（.xlsx或.xls格式）')
                return render(request, 'admin/accounts/user/import.html', {
                    'title': '批量导入用户',
                    'opts': self.model._meta,
                })
            
            # 保存上传的文件到临时目录
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp_file:
                for chunk in excel_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name
            
            try:
                # 执行导入
                result = UserImportService.import_users(tmp_file_path)
                
                # 显示结果
                if result['success_count'] > 0:
                    messages.success(
                        request,
                        f'成功导入 {result["success_count"]} 个用户'
                    )
                
                if result['failed_count'] > 0:
                    error_msg = f'失败 {result["failed_count"]} 个用户'
                    if result['errors']:
                        error_details = '<br>'.join(result['errors'][:10])  # 最多显示10条错误
                        if len(result['errors']) > 10:
                            error_details += f'<br>...还有 {len(result["errors"]) - 10} 条错误未显示'
                        messages.error(request, format_html(f'{error_msg}<br>{error_details}'))
                    else:
                        messages.error(request, error_msg)
                
                # 如果有详细结果，在消息中显示
                if result.get('details'):
                    details_html = '<table style="width:100%; margin-top:10px;"><tr><th>行号</th><th>用户名</th><th>状态</th></tr>'
                    for detail in result['details'][:20]:  # 最多显示20条
                        status_color = 'green' if detail['status'] == '成功' else 'red'
                        details_html += f'<tr><td>{detail["row_num"]}</td><td>{detail["username"]}</td><td style="color:{status_color}">{detail["status"]}</td></tr>'
                    if len(result['details']) > 20:
                        details_html += f'<tr><td colspan="3">...还有 {len(result["details"]) - 20} 条记录未显示</td></tr>'
                    details_html += '</table>'
                    messages.info(request, format_html(f'导入详情：{details_html}'))
                
                # 如果没有成功也没有失败，说明文件有问题
                if result['success_count'] == 0 and result['failed_count'] == 0:
                    if result['errors']:
                        error_details = '<br>'.join(result['errors'])
                        messages.error(request, format_html(f'导入失败：<br>{error_details}'))
                    else:
                        messages.warning(request, '未找到有效数据，请检查Excel文件格式')
                
            except Exception as e:
                messages.error(request, f'导入过程中发生错误：{str(e)}')
            finally:
                # 删除临时文件
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass
            
            return redirect('admin:accounts_user_changelist')
        
        # GET请求，显示导入页面
        return render(request, 'admin/accounts/user/import.html', {
            'title': '批量导入用户',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        })
    
    def download_template_view(self, request):
        """下载导入模板"""
        template_path = os.path.join(settings.BASE_DIR.parent, 'docs', '用户导入模板.xlsx')
        
        if os.path.exists(template_path):
            return FileResponse(
                open(template_path, 'rb'),
                as_attachment=True,
                filename='用户导入模板.xlsx'
            )
        else:
            messages.error(request, '模板文件不存在')
            return redirect('admin:accounts_user_changelist')

