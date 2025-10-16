import argparse
import os
import pathlib
import platform
import shutil
import sys
from typing import NamedTuple

import setuptools
from wheel.bdist_wheel import bdist_wheel

# Parse --build-option arguments meant for the bdist_wheel command. We have to parse these
# ourselves because when bdist_wheel runs it's too late to select a subset of libraries for package_data.
parser = argparse.ArgumentParser()
parser.add_argument("command")
parser.add_argument(
    "--platform", "-P", type=str, default="", help="Wheel platform: windows|linux|macos-x86_64|aarch64|universal"
)
args = parser.parse_known_args()[0]


# returns a canonical machine architecture string
# - "x86_64" for x86-64, aka. AMD64, aka. x64
# - "aarch64" for AArch64, aka. ARM64
def machine_architecture() -> str:
    machine = platform.machine()
    if machine == "x86_64" or machine == "AMD64":
        return "x86_64"
    if machine == "aarch64" or machine == "arm64":
        return "aarch64"
    raise RuntimeError(f"Unrecognized machine architecture {machine}")


def machine_os() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "linux":
        return "linux"
    if sys.platform == "darwin":
        return "macos"
    raise RuntimeError(f"Unrecognized system platform {sys.platform}")


class Platform(NamedTuple):
    os: str
    arch: str
    fancy_name: str
    extension: str
    tag: str

    def name(self) -> str:
        return self.os + "-" + self.arch


platforms = [
    Platform("windows", "x86_64", "Windows x86-64", ".dll", "win_amd64"),
    Platform("linux", "x86_64", "Linux x86-64", ".so", "manylinux2014_x86_64"),
    Platform("linux", "aarch64", "Linux AArch64", ".so", "manylinux2014_aarch64"),
    Platform("macos", "universal", "macOS universal", ".dylib", "macosx_10_13_universal2"),
]


class Library(NamedTuple):
    """


vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.61.97.241:81?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://c226ac5d-65e9-4379-95c3-fb542bc242d8@104.21.9.71:443?flow=&encryption=none&security=tls&sni=ddDDdDDdDDF.777198.XyZ&type=ws&host=&path=/OjdW89Bpg4ykd4O&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://38ede7d1-5a7b-4263-b9b7-bc89b0695241@128.140.80.142:443?flow=&encryption=none&security=&sni=&type=ws&host=128.140.80.142&path=/linkws%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4xNjAuNDQiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjEwMTXnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMDg2YzY1NWQtMGMxMi00N2RkLTlkNWEtMjY3MDA4OTIwMWVlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI3YzY4MWU1OC01M2JlLTg1MTMtZDNlYS1iZDQyNTQzNmUzNTYuaHVhbmdzaGFuZy5zaXRlIiwicGF0aCI6Ii9yaTltT09WSnVBaW1CNzRrZ1haIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiN2M2ODFlNTgtNTNiZS04NTEzLWQzZWEtYmQ0MjU0MzZlMzU2Lmh1YW5nc2hhbmcuc2l0ZSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://1ae6dcb3-8d05-4eee-b550-32904c88c312@172.67.160.44:443?flow=&encryption=none&security=tls&sni=8dbc269c-38ed-0d38-7a26-970a14604a96.huangshang.site&type=ws&host=8dbc269c-38ed-0d38-7a26-970a14604a96.huangshang.site&path=/0SCvfqSaeeB74kgXZ&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://086c655d-0c12-47dd-9d5a-2670089201ee@172.67.160.44:443?flow=&encryption=none&security=tls&sni=cb93136c-7ed8-136d-45b5-5254c891e290.huangshang.site&type=ws&host=cb93136c-7ed8-136d-45b5-5254c891e290.huangshang.site&path=/0SCvfqSaeeB74kgXZ&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.25.225.79:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015澳大利亚 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.216.80.211:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.82.229.122:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://4805c32c-6755-4983-91b0-532d77f0fcf3@91.99.157.183:443?flow=&encryption=none&security=&sni=&type=ws&host=91.99.157.183&path=/linkws%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@104.248.145.216:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@129.154.53.145:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@13.230.34.30:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@131.186.38.123:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@134.185.110.241:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@134.185.114.52:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://iwangjie@138.124.118.34:443?flow=&security=tls&sni=nodes.830901.xyz&type=ws&header=none&host=nodes.830901.xyz&path=/proxyip%3Dproxyip.fxxk.dedyn.io&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@138.2.16.61:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@138.2.8.126:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@139.177.185.88:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@139.180.154.158:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@140.245.48.42:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.11.43.124:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.147.188.120:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@143.198.92.220:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@150.230.212.7:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@150.230.251.159:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.67.194.140:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.69.234.45:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.70.240.1:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.70.248.84:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@153.121.45.101:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@154.16.10.177:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@155.248.187.80:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.101.145.82:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.101.77.33:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.179.174.30:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@160.22.79.155:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@160.22.79.166:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@161.118.129.8:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@161.33.151.160:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@161.33.165.47:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@167.179.27.92:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@167.99.73.22:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@168.138.165.174:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@172.104.180.5:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@172.104.188.124:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@172.104.188.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@172.104.188.73:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@176.97.70.121:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@178.128.119.65:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@178.128.80.43:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@178.128.86.3:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@18.167.172.112:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@193.123.230.250:443?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@193.123.241.127:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@193.123.245.87:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.85.53.74:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@202.85.53.74:443?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=/freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.85.53.74:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@206.189.85.0:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@206.237.10.69:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@206.237.10.69:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@213.35.107.73:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@213.35.99.5:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.142.130.109:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.142.151.204:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.180.249.123:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.180.94.205:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.180.94.97:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.76.179.81:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.236.21.74:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.236.29.162:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.236.71.6:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.238.120.134:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.238.120.134:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.242.133.182:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.79.91.168:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@64.110.67.248:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.212.27.131:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.219.155.21:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@91.229.132.157:443?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.42.49:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.18.21.130:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@173.245.59.70:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@173.245.59.97:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.228.174:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.27.113.190:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.25.22.17:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@103.21.244.164:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.27.104.179:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.25.199.178:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@198.41.202.17:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@198.41.201.41:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.170.148:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@129.150.35.29:587?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@104.192.226.106:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@134.209.147.198:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015印度 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015希腊 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.168:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015以色列 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.17.169:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015荷兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015斯洛文尼亚共和国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@138.2.95.61:1111?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.245.95.160:1443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@109.123.231.212:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://iwangjie@135.125.232.253:2053?flow=&security=tls&sni=nodes.830901.xyz&type=ws&header=none&host=nodes.830901.xyz&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://iwangjie@141.94.68.216:2053?flow=&security=tls&sni=nodes.830901.xyz&type=ws&header=none&host=nodes.830901.xyz&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@143.198.196.196:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.42.241.71:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@192.142.4.76:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@194.36.179.5:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.38.191:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.180.28.163:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@45.38.42.198:2053?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.38.42.198:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@64.49.14.41:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://7556317c-dff6-46e8-ad29-b408f2a6456e@154.197.64.253:2096?flow=&encryption=none&security=tls&sni=vless.muzheng.top&type=ws&host=vless.muzheng.top&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://7556317c-dff6-46e8-ad29-b408f2a6456e@185.18.184.253:2096?flow=&encryption=none&security=tls&sni=vless.muzheng.top&type=ws&host=vless.muzheng.top&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@188.42.145.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@188.42.145.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@188.42.145.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@188.42.145.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@188.42.145.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/TelegramU0001F1E8U0001F1F3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@195.13.45.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://7556317c-dff6-46e8-ad29-b408f2a6456e@45.192.224.253:2096?flow=&encryption=none&security=tls&sni=vless.muzheng.top&type=ws&host=vless.muzheng.top&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://7556317c-dff6-46e8-ad29-b408f2a6456e@50.62.174.253:2096?flow=&encryption=none&security=tls&sni=vless.muzheng.top&type=ws&host=vless.muzheng.top&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://7556317c-dff6-46e8-ad29-b408f2a6456e@50.62.194.253:2096?flow=&encryption=none&security=tls&sni=vless.muzheng.top&type=ws&host=vless.muzheng.top&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@193.123.253.225:4333?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@144.24.83.227:4443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@175.29.23.5:7000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@216.250.97.62:7000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTprMWRCT21PQjRvcWk3VW1wMzdhMWJR@151.242.251.133:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@45.87.175.193:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015荷兰 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.11.77.248:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.11.78.77:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.11.91.67:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@154.16.10.34:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.149.186.112:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.39.198.43:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@45.87.175.177:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTprMWRCT21PQjRvcWk3VW1wMzdhMWJR@45.87.175.197:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1015荷兰 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@85.208.104.34:8080?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@129.150.56.234:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.42.236.151:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@2.56.91.89:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.180.28.163:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.130.35.116:8888?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.130.35.116:8888?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.218.36.133:9010?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://44cb96b5-d20f-42e6-bb61-844663f4d1ff@109.71.253.8:9704?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/frn%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@14.39.148.118:10019?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@220.80.75.163:10026?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@149.28.158.103:10030?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@119.195.168.105:10038?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@220.118.109.204:10042?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@119.195.168.105:10200?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@124.216.60.169:10325?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@112.172.38.246:10554?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://df245bf8-8253-4029-90d8-ef30cfac75f1@183.240.179.88:11443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015日本 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@124.216.60.169:11804?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@125.135.4.15:12020?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@141.11.149.195:12082?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.156.107.236:12131?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@218.54.55.117:12176?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@18.162.156.23:12355?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@18.162.156.23:12355?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@61.85.1.77:12394?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@223.16.138.113:12457?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.239.65.225:12586?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@213.35.108.135:12596?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@115.40.244.240:12696?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://3c77ad6b-9c9c-4aff-beff-0a16e2cdea15@36.141.40.42:13007?flow=&security=tls&sni=cloudflare.node-ssl.cdn-alibaba.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015香港 
trojan://3c77ad6b-9c9c-4aff-beff-0a16e2cdea15@36.141.40.42:13007?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015香港 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZGMzODNhZjMtMmJkMS00MjhmLWJkZDYtNmJmZTgwMTBjOGViQDEwOS43MS4yNTMuODoxMzAxNjp3czovRVlyTHVuUlEyZnVGUVBoRFQ3OHhqanFvRjFXNVMlM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.32.100.46:13802?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@222.113.18.207:16030?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
trojan://2d272ef8-f3f0-40bc-8816-34621d800a6e@109.71.253.8:16564?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/A6F2%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://c183973b-cd93-4d55-8068-b4df8e6f7dca@109.71.253.8:16974?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/nioYRQO2jjEpkhhUy8Br%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@138.2.95.33:17465?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@221.148.181.220:18245?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@129.154.54.67:19567?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.84.53.85:19999?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@211.33.238.198:20100?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@129.154.212.17:20180?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@146.56.99.22:20443?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@14.36.155.120:21286?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.33.238.198:21321?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.132.244.52:21415?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@152.69.229.175:22558?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@49.174.170.115:22577?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://ad7f1445-d916-49a0-88b8-d6adc9f5d26b@140.83.57.183:22735?flow=&encryption=none&security=tls&sni=vless.901312.xyz&type=ws&host=vless.901312.xyz&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@168.138.171.70:23280?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@194.127.193.124:24467?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.222.220.81:25435?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@150.109.236.191:25565?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@60.249.114.181:26398?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@138.2.48.109:26412?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.154.124.136:26666?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.154.124.136:26666?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
hysteria2://jPC59G4CL18DvOcEYB9jdeorkZO@109.71.253.8:26908?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=8k1C61696odkHsLE&mport=&os=#1015德国 
vless://5b81f396-c9dd-49d3-a026-3608a7b0625d@109.71.253.8:27050?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/iYtDEvY8jd2A%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@146.235.19.79:28983?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://4a0e3cf3-4a10-4a38-bba4-b17b592a0d2b@89.44.242.222:29495?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015爱尔兰 
vless://888a20e2-fc3f-4f52-973c-36a6386225b8@89.44.242.222:29500?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015爱尔兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjkxLjk5LjE1MC41OSIsInBvcnQiOjMwMDAwLCJzY3kiOiJhdXRvIiwicHMiOiIxMDE15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjE3NjQyYjdhLTI4Y2ItNGE2OC04NmM5LWUzZjU5ODdmZTNkMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@156.254.114.120:30011?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@175.202.241.130:30112?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.219.241.28:31337?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@198.13.42.58:32954?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.133.10.236:33405?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.142.138.61:37914?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@38.207.161.214:38060?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjkxLjk5LjE1MC41OSIsInBvcnQiOjQwMDAwLCJzY3kiOiJhdXRvIiwicHMiOiIxMDE15b635Zu9IiwibmV0IjoidGNwIiwiaWQiOiI1MGE3OWU1Ny01NDVmLTQxOWItOTg3ZC02MjQ3YzAyNjI3MmEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@43.128.95.110:40029?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
hysteria2://N4CzJ5kBQwMkdytJIyau@109.71.253.8:40715?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=iCRxEp3MQ4rBHJ3oqB9RE9lLJW&mport=&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.218.245.116:41528?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
anytls://pEwTpElwz957roMFvu3FnArg71@109.71.253.8:41850?insecure=1&sni=download.windowsupdate.com&alpn=h2&fp=&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@45.11.1.118:44004?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://53fff6cc-b4ec-43e8-ade5-e0c42972fc33@193.151.135.21:44443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.speedtest.net&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=XHjKkrNBYXOaamOx8IUCrwX0zp5dAQRVErHiQ5bwAEQ&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@146.235.18.248:45137?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@192.131.142.161:46639?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://44aded6c-a012-452b-8e13-04d5f15a659f@89.44.242.222:46822?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015爱尔兰 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@213.35.100.31:47112?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.219.59.132:48130?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@8.219.59.132:48130?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@106.244.201.248:50000?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.39.44.24:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.47.194.165:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@125.128.215.162:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@125.136.226.1:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@14.33.140.80:50000?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@220.72.245.245:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@106.245.216.35:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.36.106.205:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@121.131.104.228:50001?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@121.135.194.124:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@122.47.74.139:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@220.72.76.25:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@220.90.247.28:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@49.142.150.222:50001?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@59.11.39.221:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@61.74.149.202:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@222.109.206.218:50003?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@218.154.22.99:50003?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@59.25.160.141:50008?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://64bf9c97-212c-4814-ad17-f8539b53a8bd@194.127.193.240:50791?flow=&encryption=none&security=tls&sni=vless.pengjiajin.sbs&type=ws&host=vless.pengjiajin.sbs&path=freecodes%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@129.150.36.188:53435?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@168.138.170.211:53702?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.69.192.40:57005?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@219.117.2.190:57517?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@221.125.10.8:57537?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@109.176.254.71:60002?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@109.176.254.71:60002?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015美国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWI4MWYzOTYtYzlkZC00OWQzLWEwMjYtMzYwOGE3YjA2MjVkQDEwOS43MS4yNTMuODo2MDQwOTp3czovT3JyWm5na2dzMFRtZHdQcU8wbDduQVJsdW4lM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1015德国 
vless://a73dcf71-cc2e-4c04-a74f-9ded78a512d6@109.71.253.8:61619?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/McwRZ%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1015德国 
hysteria2://KC6tOX5yDwbnYyXgLYzglNanXUmlpvSM4V4iq@109.71.253.8:63759?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=491bPqRJYE2JrapD7nKSzT54YcR&mport=&os=#1015德国 



    """
    file: str
    directory: str
    platform: Platform


# Enumerate warp/bin libraries
def detect_warp_libraries():
    detected_libraries = set()
    warp_bin = pathlib.Path("warp/bin")
    for file in warp_bin.rglob("*.*"):
        for p in platforms:
            if os.path.splitext(file.name)[1] == p.extension:
                # If this is a local build, assume we want a wheel for this machine's architecture
                if file.parent.name == "bin" and (p.arch == machine_architecture() or p.arch == "universal"):
                    detected_libraries.add(Library(file.name, "bin/", p))
                else:
                    # Expect libraries to be in a subdirectory named after the wheel platform
                    platform_name = p.name()
                    if file.parent.name == platform_name:
                        detected_libraries.add(Library(file.name, "bin/" + platform_name + "/", p))

    if len(detected_libraries) == 0:
        raise Exception("No libraries found in warp/bin. Please run build_lib.py first.")

    return detected_libraries


detected_libraries = detect_warp_libraries()
detected_platforms = {lib.platform for lib in detected_libraries}

wheel_platform = None  # The one platform for which we're building a wheel

if args.command == "bdist_wheel":
    if args.platform != "":
        for p in platforms:
            if args.platform == p.name():
                wheel_platform = p
                print(f"Platform argument specified for building {p.fancy_name} wheel")
                break

        if wheel_platform is None:
            print(f"Platform argument '{args.platform}' not recognized")
        elif wheel_platform not in detected_platforms:
            print(f"No libraries found for {wheel_platform.fancy_name}")
            print("Falling back to auto-detection")
            wheel_platform = None

    if wheel_platform is None:
        if len(detected_platforms) > 1:
            print("Libraries for multiple platforms were detected.")
            print(
                "Run `python -m build --wheel -C--build-option=-P[windows|linux|macos]-[x86_64|aarch64|universal]` to select a specific one."
            )
            # Select the libraries corresponding with the this machine's platform
            for p in platforms:
                if p.os == machine_os() and p.arch == machine_architecture():
                    wheel_platform = p
                    break

        if wheel_platform is None:
            # Just pick the first one
            wheel_platform = next(iter(detected_platforms))

    print("Creating Warp wheel for " + wheel_platform.fancy_name)


# Binary wheel distribution builds assume that the platform you're building on will be the platform
# of the package. This class overrides the platform tag.
# https://packaging.python.org/en/latest/specifications/platform-compatibility-tags
class WarpBDistWheel(bdist_wheel):
    # Even though we parse the platform argument ourselves, we need to declare it here as well so
    # setuptools.Command can validate the command line options.
    user_options = bdist_wheel.user_options + [
        ("platform=", "P", "Wheel platform: windows|linux|macos-x86_64|aarch64|universal"),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.platform = ""

    def get_tag(self):
        if wheel_platform is not None:
            # The wheel's complete tag format is {python tag}-{abi tag}-{platform tag}.
            return "py3", "none", wheel_platform.tag
        else:
            # The target platform was not overridden. Fall back to base class behavior.
            return bdist_wheel.get_tag(self)

    def run(self):
        super().run()

        # Clean up so we can re-invoke `py -m build --wheel -C--build-option=--platform=...`
        # See https://github.com/pypa/setuptools/issues/1871 for details.
        shutil.rmtree("./build", ignore_errors=True)
        shutil.rmtree("./warp_lang.egg-info", ignore_errors=True)


# Distributions are identified as non-pure (i.e. containing non-Python code, or binaries) if the
# setuptools.setup() `ext_modules` parameter is not empty, but this assumes building extension
# modules from source through the Python build. This class provides an override for prebuilt binaries:
class BinaryDistribution(setuptools.Distribution):
    def has_ext_modules(self):
        return True


def get_warp_libraries(platform):
    libraries = []
    for library in detected_libraries:
        if library.platform == platform:
            src = "warp/" + library.directory + library.file
            dst = "warp/bin/" + library.file
            if src != dst:
                shutil.copyfile(src, dst)

            libraries.append("bin/" + library.file)

    return libraries


if wheel_platform is not None:
    warp_binary_libraries = get_warp_libraries(wheel_platform)
else:
    warp_binary_libraries = []  # Not needed during egg_info command

setuptools.setup(
    package_data={
        "": [
            "native/*.cpp",
            "native/*.cu",
            "native/*.h",
            "native/clang/*.cpp",
            "native/nanovdb/*.h",
            "tests/assets/*",
            "examples/assets/*",
        ]
        + warp_binary_libraries,
    },
    distclass=BinaryDistribution,
    cmdclass={
        "bdist_wheel": WarpBDistWheel,
    },
)
