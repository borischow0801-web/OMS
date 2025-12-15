"""自定义文件存储，按日期组织文件"""
import os
from datetime import date
from django.core.files.storage import FileSystemStorage
from django.conf import settings


class DateBasedFileStorage(FileSystemStorage):
    """按日期组织的文件存储"""
    
    def __init__(self, location=None, base_url=None):
        if location is None:
            # 使用OMS/docs/作为存储根目录
            location = os.path.join(settings.BASE_DIR.parent, 'docs')
        super().__init__(location=location, base_url=base_url)
    
    def get_available_name(self, name, max_length=None):
        """获取可用文件名，如果文件已存在则添加数字后缀"""
        if self.exists(name):
            dir_name, file_name = os.path.split(name)
            file_root, file_ext = os.path.splitext(file_name)
            counter = 1
            while self.exists(name):
                name = os.path.join(
                    dir_name,
                    f"{file_root}_{counter}{file_ext}"
                )
                counter += 1
        return name
    
    def generate_filename(self, filename):
        """生成按日期组织的文件路径"""
        # 获取当前日期
        today = date.today()
        year = str(today.year)
        month = str(today.month).zfill(2)
        day = str(today.day).zfill(2)
        
        # 构建路径: OMS/docs/2025/11/24/filename
        date_path = os.path.join(year, month, day)
        filename_path = os.path.join(date_path, filename)
        
        # 确保目录存在
        full_path = os.path.join(self.location, date_path)
        os.makedirs(full_path, exist_ok=True)
        
        return filename_path

