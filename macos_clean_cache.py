import os
import shutil
import getpass
import platform
import sys

def sizeof_fmt(num):
    """自定义文件大小格式化函数"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if abs(num) < 1024.0:
            return "%3.1f %s" % (num, unit)
        num /= 1024.0
    return "%.1f TB" % num

def check_environment():
    """环境检查增强版"""
    if platform.system() != 'Darwin':
        print("错误：此脚本仅适用于macOS系统")
        sys.exit(1)
        
    current_user = getpass.getuser()
    if current_user == 'root':
        print("⚠️ 检测到root权限，建议使用普通用户权限执行")
        confirm = input("是否继续？(y/N): ").lower()
        if confirm != 'y':
            sys.exit(0)
    else:
        print("ℹ️ 当前用户：", current_user)
        print("提示：系统目录清理需要sudo权限")

def handle_system_dirs():
    """处理系统目录权限"""
    sys_dirs = [
        "/Library/Caches",
        "/Library/Logs",
        "/private/var/log",
        "/System/Library/Caches"
    ]
    
    need_sudo = any(os.path.exists(d) for d in sys_dirs)
    if need_sudo and os.geteuid() != 0:
        print("\n检测到系统级缓存目录，需要管理员权限")
        confirm = input("是否尝试获取sudo权限？(y/N): ").lower()
        if confirm == 'y':
            os.execvp('sudo', ['sudo', sys.executable] + sys.argv)

def get_clean_paths():
    """获取清理路径列表"""
    home = os.path.expanduser("~")
    return [
        # 用户缓存
        os.path.join(home, "Library/Caches"),
        os.path.join(home, "Library/Logs"),
        
        # 系统缓存
        "/Library/Caches",
        "/Library/Logs",
        
        # 开发者缓存
        os.path.join(home, "Library/Developer/Xcode/DerivedData"),
        os.path.join(home, "Library/Developer/Xcode/iOS Device Logs"),
        
        # 浏览器缓存
        os.path.join(home, "Library/Application Support/Google/Chrome/Default/Application Cache"),
        os.path.join(home, "Library/Application Support/Google/Chrome/Default/Service Worker/CacheStorage"),
        os.path.join(home, "Library/Safari"),
        
        # 其他缓存
        os.path.join(home, ".npm/_cacache"),
        os.path.join(home, ".cache"),
        os.path.join(home, "Library/Containers/com.docker.docker/Data/vms"),
    ]

def clean_directory(path):
    """安全清理目录"""
    try:
        if not os.path.exists(path):
            return 0, 0

        total_files = 0
        total_size = 0

        for root, dirs, files in os.walk(path):
            # 跳过系统保护目录
            dirs[:] = [d for d in dirs if 'com.apple.' not in d and 'System' not in d]
            
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.ismount(file_path) or os.path.islink(file_path):
                        continue
                        
                    file_size = os.path.getsize(file_path)
                    os.remove(file_path)
                    total_files += 1
                    total_size += file_size
                except (PermissionError, OSError):
                    print(f"⛔ 跳过受保护文件: {file_path}")
                except Exception as e:
                    print(f"删除失败 [{file_path}]: {str(e)}")

            for dir in dirs:
                dir_path = os.path.join(root, dir)
                try:
                    shutil.rmtree(dir_path)
                except (PermissionError, OSError):
                    print(f"⛔ 跳过系统目录: {dir_path}")
                except Exception as e:
                    print(f"目录删除失败 [{dir_path}]: {str(e)}")

        return total_files, total_size

    except Exception as e:
        print(f"清理中断 [{path}]: {str(e)}")
        return 0, 0

def main():
    check_environment()
    handle_system_dirs()
    
    print("\n即将清理以下内容：")
    clean_paths = get_clean_paths()
    for path in clean_paths:
        print(f" - {os.path.expanduser(path)}")
    
    confirm = input("\n确认要清理系统缓存和垃圾文件吗？(y/N): ").lower()
    if confirm != 'y':
        print("操作已取消")
        return

    total_cleaned = 0
    total_freed = 0

    for path in clean_paths:
        expanded_path = os.path.expanduser(path)
        print(f"\n正在清理: {expanded_path}")
        files, size = clean_directory(expanded_path)
        total_cleaned += files
        total_freed += size

        print(f"已清理 {files} 个文件，释放空间 {sizeof_fmt(size)}")

    print("\n清理完成！")
    print(f"总共清理文件数量: {total_cleaned}")
    print(f"总共释放空间: {sizeof_fmt(total_freed)}")

if __name__ == "__main__":
    main()
