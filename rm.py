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


vless://f61a4285-7264-4d07-9408-7b9ba1922c26@111.118.118.177:12566?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40freecodes/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.38.245.191:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.40.126.7:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.40.126.7:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.44.64.9:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.91.78.76:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@118.91.78.76:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@121.131.242.29:12219?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@121.158.194.32:11413?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@121.173.93.124:12185?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@121.173.93.124:12185?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyNC4yMzYuNDYuMTE0IiwicG9ydCI6NDcwODMsInNjeSI6ImF1dG8iLCJwcyI6IjEwMjHloZ7oiIzlsJQiLCJuZXQiOiJ0Y3AiLCJpZCI6ImZkNDkzODFmLTlmZDgtNDQwMy04Njk4LTQ4MzMxYTRkNzc1ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@124.61.52.107:26257?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@124.61.52.107:26257?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@125.128.215.162:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@14.39.99.235:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@147.75.225.105:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@147.75.225.105:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@152.67.194.140:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@153.121.45.101:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@153.121.45.101:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@153.121.45.101:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.101.77.33:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.101.80.84:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@160.16.203.210:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@160.16.203.210:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@160.22.79.155:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@175.211.35.161:50003?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@175.215.175.175:50003?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@182.31.70.92:12336?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@182.31.70.92:12336?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@183.100.113.37:21297?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@183.101.243.99:12576?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@183.104.0.181:16923?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@183.104.0.181:16923?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1021摩尔多瓦 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@185.18.222.208:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1021波兰 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@203.243.63.166:27249?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.219.241.28:31337?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.228.5.119:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1021韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@220.90.247.28:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@222.113.18.211:14443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@223.16.138.113:10002?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
trojan://BxceQaOe@36.150.215.138:4451?flow=&security=tls&sni=36.150.215.138&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021香港 
trojan://BxceQaOe@36.150.215.138:4451?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021香港 
trojan://BxceQaOe@36.151.251.18:811?flow=&security=tls&sni=36.151.251.18&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021日本 
trojan://BxceQaOe@36.151.251.18:811?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021日本 
trojan://BxceQaOe@36.156.102.115:26876?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021美国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@141.101.121.129:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.17.107.191:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.27.6.183:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@103.21.244.164:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
hysteria2://jPC59G4CL18DvOcEYB9jdeorkZO@109.71.253.8:26908?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=8k1C61696odkHsLE&mport=&os=#1021德国 
hysteria2://KC6tOX5yDwbnYyXgLYzglNanXUmlpvSM4V4iq@109.71.253.8:63759?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=491bPqRJYE2JrapD7nKSzT54YcR&mport=&os=#1021德国 
trojan://2d272ef8-f3f0-40bc-8816-34621d800a6e@109.71.253.8:16564?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/A6F2%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@162.159.130.238:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.18.248.218:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@190.93.244.167:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://a73dcf71-cc2e-4c04-a74f-9ded78a512d6@109.71.253.8:61619?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/McwRZ%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://c183973b-cd93-4d55-8068-b4df8e6f7dca@109.71.253.8:16974?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/nioYRQO2jjEpkhhUy8Br%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@198.41.201.41:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@141.101.113.130:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.19.133.213:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
trojan://44cb96b5-d20f-42e6-bb61-844663f4d1ff@109.71.253.8:9704?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/frn%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
anytls://pEwTpElwz957roMFvu3FnArg71@109.71.253.8:41850?insecure=1&sni=download.windowsupdate.com&alpn=h2&fp=&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.27.104.179:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
hysteria2://N4CzJ5kBQwMkdytJIyau@109.71.253.8:40715?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=iCRxEp3MQ4rBHJ3oqB9RE9lLJW&mport=&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.19.135.80:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZGMzODNhZjMtMmJkMS00MjhmLWJkZDYtNmJmZTgwMTBjOGViQDEwOS43MS4yNTMuODoxMzAxNjp3czovRVlyTHVuUlEyZnVGUVBoRFQ3OHhqanFvRjFXNVMlM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.139.79:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.25.199.206:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWI4MWYzOTYtYzlkZC00OWQzLWEwMjYtMzYwOGE3YjA2MjVkQDEwOS43MS4yNTMuODo2MDQwOTp3czovT3JyWm5na2dzMFRtZHdQcU8wbDduQVJsdW4lM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@103.21.244.155:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@188.114.98.101:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.170.148:443?flow=&encryption=none&security=tls&sni=ho.msxoa.dpdns.org&type=xhttp&host=ho.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 
vless://5b81f396-c9dd-49d3-a026-3608a7b0625d@109.71.253.8:27050?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/iYtDEvY8jd2A%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1021德国 

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
