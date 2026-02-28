"""
Сетевые инструменты для Telegram-бота.
Показ IP, ping, netstat, DNS lookup, speedtest.
"""

import logging
import socket
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)


def get_public_ip() -> tuple[bool, str, str]:
    """
    Получение публичного IP-адреса.

    Returns:
        Кортеж (success, message, ip_address)
    """
    try:
        import urllib.request

        services = [
            'https://api.ipify.org',
            'https://ifconfig.me/ip',
            'https://icanhazip.com',
        ]

        for service in services:
            try:
                with urllib.request.urlopen(service, timeout=5) as response:
                    ip = response.read().decode().strip()
                    message = f"✅ Public IP: {ip}"
                    logger.info(message)
                    return True, message, ip
            except Exception:
                continue

        return get_local_ip()
    except Exception as e:
        message = f"❌ Error getting public IP: {e}"
        logger.error(message)
        return False, message, ""


def get_local_ip() -> tuple[bool, str, str]:
    """
    Получение локального IP-адреса.

    Returns:
        Кортеж (success, message, ip_address)
    """
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()

        message = f"✅ Local IP: {local_ip}"
        logger.info(message)
        return True, message, local_ip
    except Exception as e:
        message = f"❌ Error getting local IP: {e}"
        logger.error(message)
        return False, message, ""


def get_all_ips() -> dict:
    """
    Получение всех IP-адресов системы.

    Returns:
        Словарь с IP-адресами
    """
    import psutil

    ips = {
        'local': [],
        'public': None
    }

    addrs = psutil.net_if_addrs()
    for interface_name, addrs_list in addrs.items():
        for addr in addrs_list:
            if addr.family == socket.AF_INET:
                ips['local'].append({
                    'interface': interface_name,
                    'ip': addr.address,
                    'netmask': addr.netmask
                })

    success, _, public_ip = get_public_ip()
    if success:
        ips['public'] = public_ip

    return ips


def ping_host(host: str, count: int = 4) -> tuple[bool, str]:
    """
    Ping указанного хоста.
    
    Args:
        host: Хост для ping (домен или IP)
        count: Количество запросов
        
    Returns:
        Кортеж (success, message)
    """
    try:
        # Windows ping
        cmd = ['ping', '-n', str(count), host]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=count * 2 + 10
        )
        
        output = result.stdout + result.stderr
        message = f"📡 Ping results for {host}:\n\n```\n{output}\n```"
        logger.info(f"Ping {host}: {result.returncode}")
        return result.returncode == 0, message
    except subprocess.TimeoutExpired:
        message = f"❌ Ping timeout for {host}"
        logger.warning(message)
        return False, message
    except Exception as e:
        message = f"❌ Error pinging {host}: {e}"
        logger.error(message)
        return False, message


def netstat(show_all: bool = True) -> tuple[bool, str]:
    """
    Выполнение команды netstat.

    Args:
        show_all: Показывать все соединения (включая LISTENING)

    Returns:
        Кортеж (success, message)
    """
    try:
        cmd = ['netstat', '-a', '-n', '-o']
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30
        )

        output = result.stdout
        lines = output.split('\n')
        if len(lines) > 50:
            output = '\n'.join(lines[:50]) + f"\n\n... and {len(lines) - 50} more lines"

        message = f"📊 Netstat output:\n\n```\n{output}\n```"
        logger.info("Netstat executed")
        return True, message
    except subprocess.TimeoutExpired:
        message = "❌ Netstat timeout"
        logger.warning(message)
        return False, message
    except Exception as e:
        message = f"❌ Error executing netstat: {e}"
        logger.error(message)
        return False, message


def dns_lookup(hostname: str) -> tuple[bool, str]:
    """
    DNS lookup для указанного хоста.

    Args:
        hostname: Имя хоста для разрешения

    Returns:
        Кортеж (success, message)
    """
    try:
        ip_addresses = socket.gethostbyname_ex(hostname)

        result = f"Hostname: {hostname}\n"
        result += f"Canonical name: {ip_addresses[0]}\n"
        result += f"IP addresses: {', '.join(ip_addresses[2])}\n"

        for ip in ip_addresses[2]:
            try:
                reverse = socket.gethostbyaddr(ip)
                result += f"Reverse DNS for {ip}: {reverse[0]}\n"
            except socket.herror:
                result += f"Reverse DNS for {ip}: Not available\n"

        message = f"🔍 DNS Lookup results:\n\n```\n{result}\n```"
        logger.info(f"DNS lookup for {hostname}: success")
        return True, message
    except socket.gaierror as e:
        message = f"❌ DNS lookup failed for {hostname}: {e}"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error in DNS lookup: {e}"
        logger.error(message)
        return False, message


def run_speedtest() -> tuple[bool, str]:
    """
    Запуск теста скорости интернета.
    
    Returns:
        Кортеж (success, message)
    """
    try:
        # Пробуем использовать speedtest-cli
        import speedtest
        
        st = speedtest.Speedtest()
        
        # Выбор лучшего сервера
        st.get_best_server()
        
        # Тест загрузки
        download_speed = st.download() / 1_000_000  # Mbps
        
        # Тест выгрузки
        upload_speed = st.upload() / 1_000_000  # Mbps
        
        # Пинг
        ping_result = st.results.ping
        
        message = f"""⚡ Speedtest Results:

📥 Download: {download_speed:.2f} Mbps
📤 Upload: {upload_speed:.2f} Mbps
📡 Ping: {ping_result:.2f} ms
"""
        logger.info(f"Speedtest: DL={download_speed:.2f} Mbps, UL={upload_speed:.2f} Mbps")
        return True, message
    except ImportError:
        message = "❌ speedtest-cli not installed. Install with: pip install speedtest-cli"
        logger.error(message)
        return False, message
    except Exception as e:
        message = f"❌ Error running speedtest: {e}"
        logger.error(message)
        return False, message


def get_network_interfaces() -> list:
    """
    Получение информации о сетевых интерфейсах.
    
    Returns:
        Список сетевых интерфейсов
    """
    import psutil
    
    interfaces = []
    addrs = psutil.net_if_addrs()
    
    for interface_name, addrs_list in addrs.items():
        iface_info = {
            'name': interface_name,
            'ipv4': [],
            'ipv6': [],
            'mac': None
        }
        
        for addr in addrs_list:
            if addr.family == socket.AF_INET:
                iface_info['ipv4'].append({
                    'address': addr.address,
                    'netmask': addr.netmask
                })
            elif addr.family == socket.AF_INET6:
                iface_info['ipv6'].append({
                    'address': addr.address,
                    'netmask': addr.netmask
                })
            elif hasattr(socket, 'AF_LINK'):
                iface_info['mac'] = addr.address
        
        interfaces.append(iface_info)
    
    return interfaces


def get_active_connections() -> list:
    """
    Получение активных сетевых подключений.

    Returns:
        Список активных подключений
    """
    import psutil

    connections = []
    try:
        conns = psutil.net_connections(kind='inet')
        for conn in conns[:50]:
            connections.append({
                'family': 'IPv4' if conn.family == socket.AF_INET else 'IPv6',
                'type': 'TCP' if conn.type == socket.SOCK_STREAM else 'UDP',
                'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                'status': conn.status,
                'pid': conn.pid
            })
    except psutil.AccessDenied:
        pass

    return connections
