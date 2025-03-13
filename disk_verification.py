# 警告：这个会删除上面的所有资料
# Mac用户如果遇到[Errno 16] Resource busy请先执行sudo diskutil unmounDisk /dev/diskX
# Mac和Linux用户可能需要使用root权限执行
# 如有错误请使用Issues
# 如想要改进代码可以提交PR

import os
import random
import sys
import argparse
from rich.progress import Progress, BarColumn, TimeRemainingColumn
from rich.console import Console

console = Console()

def get_confirmation(device_path):
    console.print("[bold red]警告：此操作将永久擦除目标设备上的所有数据！[/]")
    console.print(f"目标设备: [bold]{device_path}[/]")
    confirmation = input("确定要继续吗？(y/N): ")
    return confirmation.lower() == 'y'

def generate_random_data(chunk_size):
    return bytes(random.getrandbits(8) for _ in range(chunk_size))

def write_and_verify(device_path):
    chunk_size = 1024 * 1024  # 1MB
    max_blocks = 0
    successful_write = 0
    successful_read = 0
    validation_results = []

    # 写入阶段
    with Progress(
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        "• 写入速度: [progress.speed]{task.speed}MB/s",
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]写入数据...", total=None)
        
        try:
            with open(device_path, 'wb+', buffering=0) as device:
                while True:
                    data = generate_random_data(chunk_size)
                    device.write(data)
                    device.flush()
                    os.fsync(device.fileno())
                    max_blocks += 1
                    progress.update(task, advance=1, 
                                   description=f"[cyan]写入数据... ({max_blocks}MB)")
                    
        except IOError as e:
            console.print(f"\n[red]写入错误: {str(e)}[/]")
            successful_write = max_blocks
            console.print(f"[yellow]最大写入容量: {successful_write}MB[/]")

    # 验证阶段
    if successful_write > 0:
        console.print("\n[bold]开始验证数据完整性...[/]")
        current_line = []
        validation_errors = 0

        with Progress(
            BarColumn(bar_width=None),
            "[progress.percentage]{task.percentage:>3.0f}%",
            "• 剩余时间: [progress.remaining]",
            console=console
        ) as progress:
            task = progress.add_task("[green]验证数据...", total=successful_write)
            
            try:
                with open(device_path, 'rb+', buffering=0) as device:
                    for i in range(successful_write):
                        device.seek(i * chunk_size)
                        original_data = generate_random_data(chunk_size)
                        read_data = device.read(chunk_size)
                        
                        if read_data == original_data:
                            current_line.append("[green]🟩[/]")
                            successful_read += 1
                        else:
                            current_line.append("[red]🟥[/]")
                            validation_errors += 1
                        
                        # 每50个区块换行显示
                        if len(current_line) % 50 == 0:
                            console.print("".join(current_line), end="")
                            current_line = []
                        
                        progress.update(task, advance=1, 
                                      description=f"[green]验证数据... ({i+1}/{successful_write}MB)")
                    
            except IOError as e:
                console.print(f"\n[red]验证错误: {str(e)}[/]")

        # 打印剩余的区块状态
        if current_line:
            console.print("".join(current_line))
        
        console.print(f"\n[bold]验证结果:[/]")
        console.print(f"成功区块: [green]{successful_read} 🟩[/]")
        console.print(f"异常区块: [red]{validation_errors} 🟥[/]")

    return successful_write, successful_read

def main():
    parser = argparse.ArgumentParser(description='USB存储设备容量验证工具')
    parser.add_argument('device', help='目标设备路径（例如：/dev/disk2）')
    args = parser.parse_args()

    if not args.device.startswith('/dev/disk'):
        console.print("[red]错误：请指定正确的块设备路径[/]")
        sys.exit(1)

    if not get_confirmation(args.device):
        console.print("[yellow]操作已取消[/]")
        sys.exit(0)

    try:
        written, verified = write_and_verify(args.device)
        console.print(f"\n[bold]最终结果：[/]")
        console.print(f"成功写入: [cyan]{written}MB[/]")
        console.print(f"成功验证: [green]{verified}MB[/]")
        
        if written != verified:
            console.print("[red bold]警告：设备可能存在扩容问题或坏块！[/]")
        else:
            console.print("[green bold]✓ 设备容量验证通过[/]")
            
    except Exception as e:
        console.print(f"[red bold]发生错误: {str(e)}[/]")
        sys.exit(1)

if __name__ == '__main__':
    main()
