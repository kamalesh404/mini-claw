import psutil
import platform
import GPUtil
from typing import Dict, Any, List
from pydantic import BaseModel, Field

from app.tools.registry import BaseTool, ToolInputSchema, ToolOutput, PermissionLevel
from app.security.permissions import Permission


class GetSystemInfoInput(ToolInputSchema):
    pass


class GetSystemInfoTool(BaseTool):
    name = "get_system_info"
    description = "Get comprehensive system information"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetSystemInfoInput
    
    async def execute(self, input_data: GetSystemInfoInput) -> ToolOutput:
        try:
            info = {
                "platform": platform.system(),
                "platform_release": platform.release(),
                "platform_version": platform.version(),
                "architecture": platform.machine(),
                "processor": platform.processor(),
                "hostname": platform.node(),
                "python_version": platform.python_version(),
                "boot_time": psutil.boot_time(),
            }
            return ToolOutput(success=True, data=info)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetCPUUsageInput(ToolInputSchema):
    interval: float = Field(default=1.0, ge=0.1, le=10.0)
    per_cpu: bool = Field(default=True)


class GetCPUUsageTool(BaseTool):
    name = "get_cpu_usage"
    description = "Get current CPU usage percentage"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetCPUUsageInput
    
    async def execute(self, input_data: GetCPUUsageInput) -> ToolOutput:
        try:
            if input_data.per_cpu:
                usage = psutil.cpu_percent(interval=input_data.interval, percpu=True)
            else:
                usage = psutil.cpu_percent(interval=input_data.interval)
            
            freq = psutil.cpu_freq()
            cpu_info = {
                "usage_percent": usage,
                "core_count": psutil.cpu_count(logical=False),
                "thread_count": psutil.cpu_count(logical=True),
            }
            if freq:
                cpu_info["frequency_mhz"] = freq.current
            return ToolOutput(success=True, data=cpu_info)
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetGPUUsageInput(ToolInputSchema):
    pass


class GetGPUUsageTool(BaseTool):
    name = "get_gpu_usage"
    description = "Get GPU usage information"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetGPUUsageInput
    
    async def execute(self, input_data: GetGPUUsageInput) -> ToolOutput:
        try:
            gpus = GPUtil.getGPUs()
            gpu_info = []
            for gpu in gpus:
                gpu_info.append({
                    "id": gpu.id,
                    "name": gpu.name,
                    "load_percent": gpu.load * 100,
                    "memory_used_mb": gpu.memoryUsed,
                    "memory_total_mb": gpu.memoryTotal,
                    "memory_free_mb": gpu.memoryFree,
                    "temperature_c": gpu.temperature,
                })
            return ToolOutput(success=True, data={"gpus": gpu_info})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetRAMUsageInput(ToolInputSchema):
    pass


class GetRAMUsageTool(BaseTool):
    name = "get_ram_usage"
    description = "Get RAM usage information"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetRAMUsageInput
    
    async def execute(self, input_data: GetRAMUsageInput) -> ToolOutput:
        try:
            mem = psutil.virtual_memory()
            swap = psutil.swap_memory()
            return ToolOutput(success=True, data={
                "ram": {
                    "total_gb": round(mem.total / (1024**3), 2),
                    "available_gb": round(mem.available / (1024**3), 2),
                    "used_gb": round(mem.used / (1024**3), 2),
                    "percent": mem.percent,
                },
                "swap": {
                    "total_gb": round(swap.total / (1024**3), 2),
                    "used_gb": round(swap.used / (1024**3), 2),
                    "free_gb": round(swap.free / (1024**3), 2),
                    "percent": swap.percent,
                }
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetDiskUsageInput(ToolInputSchema):
    path: str = Field(default="/")


class GetDiskUsageTool(BaseTool):
    name = "get_disk_usage"
    description = "Get disk usage for a given path"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetDiskUsageInput
    
    async def execute(self, input_data: GetDiskUsageInput) -> ToolOutput:
        try:
            usage = psutil.disk_usage(input_data.path)
            partitions = psutil.disk_partitions()
            partition_info = []
            for part in partitions:
                try:
                    part_usage = psutil.disk_usage(part.mountpoint)
                    partition_info.append({
                        "device": part.device,
                        "mountpoint": part.mountpoint,
                        "fstype": part.fstype,
                        "total_gb": round(part_usage.total / (1024**3), 2),
                        "used_gb": round(part_usage.used / (1024**3), 2),
                        "free_gb": round(part_usage.free / (1024**3), 2),
                        "percent": round(part_usage.used / part_usage.total * 100, 1),
                    })
                except PermissionError:
                    continue
            
            return ToolOutput(success=True, data={
                "path": input_data.path,
                "total_gb": round(usage.total / (1024**3), 2),
                "used_gb": round(usage.used / (1024**3), 2),
                "free_gb": round(usage.free / (1024**3), 2),
                "percent": round(usage.used / usage.total * 100, 1),
                "partitions": partition_info,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetNetworkInfoInput(ToolInputSchema):
    pass


class GetNetworkInfoTool(BaseTool):
    name = "get_network_info"
    description = "Get network interface information"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetNetworkInfoInput
    
    async def execute(self, input_data: GetNetworkInfoInput) -> ToolOutput:
        try:
            interfaces = psutil.net_if_addrs()
            stats = psutil.net_if_stats()
            io = psutil.net_io_counters(pernic=True)
            
            interface_info = []
            for name, addrs in interfaces.items():
                iface = {
                    "name": name,
                    "addresses": [],
                    "is_up": stats[name].isup if name in stats else False,
                    "speed_mbps": stats[name].speed if name in stats else 0,
                    "bytes_sent": io[name].bytes_sent if name in io else 0,
                    "bytes_recv": io[name].bytes_recv if name in io else 0,
                }
                for addr in addrs:
                    iface["addresses"].append({
                        "family": str(addr.family),
                        "address": addr.address,
                        "netmask": addr.netmask,
                        "broadcast": addr.broadcast,
                    })
                interface_info.append(iface)
            
            return ToolOutput(success=True, data={"interfaces": interface_info})
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class ListProcessesInput(ToolInputSchema):
    limit: int = Field(default=50, ge=1, le=500)
    sort_by: str = Field(default="cpu", pattern="^(cpu|memory|name|pid)$")


class ListProcessesTool(BaseTool):
    name = "list_processes"
    description = "List running processes"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = ListProcessesInput
    
    async def execute(self, input_data: ListProcessesInput) -> ToolOutput:
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username', 'status']):
                try:
                    processes.append(proc.info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            if input_data.sort_by == "cpu":
                processes.sort(key=lambda x: x.get('cpu_percent', 0) or 0, reverse=True)
            elif input_data.sort_by == "memory":
                processes.sort(key=lambda x: x.get('memory_percent', 0) or 0, reverse=True)
            elif input_data.sort_by == "name":
                processes.sort(key=lambda x: x.get('name', '').lower())
            elif input_data.sort_by == "pid":
                processes.sort(key=lambda x: x.get('pid', 0))
            
            return ToolOutput(success=True, data={
                "processes": processes[:input_data.limit],
                "total_count": len(processes),
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))


class GetBatteryStatusInput(ToolInputSchema):
    pass


class GetBatteryStatusTool(BaseTool):
    name = "get_battery_status"
    description = "Get battery status (laptop only)"
    permission_level = PermissionLevel.READ_ONLY
    required_permissions = [Permission.SYSTEM_READ]
    input_schema = GetBatteryStatusInput
    
    async def execute(self, input_data: GetBatteryStatusInput) -> ToolOutput:
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return ToolOutput(success=True, data={"has_battery": False})
            
            return ToolOutput(success=True, data={
                "has_battery": True,
                "percent": battery.percent,
                "power_plugged": battery.power_plugged,
                "time_left_seconds": battery.secsleft if battery.secsleft != psutil.POWER_TIME_UNLIMITED else None,
            })
        except Exception as e:
            return ToolOutput(success=False, error=str(e))