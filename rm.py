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


vless://f61a4285-7264-4d07-9408-7b9ba1922c26@61.85.1.77:12389?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@61.85.1.77:12394?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@104.19.50.238:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@112.165.52.204:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@113.37.149.36:12553?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@116.93.199.28:12136?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@125.130.15.106:27879?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@130.162.130.105:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@130.162.130.105:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@158.101.77.33:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@175.208.202.41:20583?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@183.101.243.99:12576?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1026摩尔多瓦 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@185.18.222.208:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpBUmd2R1p5d0ErZ2FjZ0dWMjZCdm11MDUrd1ptUlcvaitBZFUrWjhCdDQ0PQ==@188.214.157.58:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1026澳门 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.84.53.85:19999?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.84.53.85:19999?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@202.84.53.85:19999?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.6.207.42:18622?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.6.207.42:18622?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.6.207.42:18622?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.61.97.241:81?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.61.97.241:81?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.61.97.241:81?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@210.61.97.241:81?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=freecodes/%3Eds%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.219.241.28:31337?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@211.228.5.119:50001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@217.60.248.66:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@218.151.91.131:12151?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/x%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1026韩国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@218.54.55.117:12176?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@222.113.18.206:10913?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@27.100.189.152:50000?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@31.192.238.71:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://BxceQaOe@36.150.215.237:1821?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026日本 
trojan://BxceQaOe@36.150.215.241:1924?flow=&security=tls&sni=36.150.215.241&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026日本 
trojan://BxceQaOe@36.150.215.241:1924?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026日本 
trojan://BxceQaOe@36.150.215.241:26373?flow=&security=tls&sni=36.150.215.241&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://BxceQaOe@36.150.215.241:26373?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://BxceQaOe@36.150.215.241:27409?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://BxceQaOe@36.151.251.23:4451?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026香港 
trojan://BxceQaOe@36.151.251.23:4451?flow=&security=tls&sni=36.151.251.23&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026香港 
trojan://BxceQaOe@36.151.251.35:24392?flow=&security=tls&sni=36.151.251.35&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026新加坡 
trojan://BxceQaOe@36.151.251.35:24392?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026新加坡 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=X%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:35951?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:47790?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@36.50.90.241:47790?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@46.8.226.39:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@46.8.226.39:2053?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@46.8.226.39:8443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@47.76.218.163:443?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/Telegram%40freecodes/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@5.182.85.253:2096?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=58.152.46.98&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026香港 
trojan://BxceQaOe@58.152.46.98:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026香港 
vless://f61a4285-7264-4d07-9408-7b9ba1922c26@61.85.1.77:17001?flow=&encryption=none&security=tls&sni=gaosir.unfeeling.sbs&type=ws&host=gaosir.unfeeling.sbs&path=/telegram%40%E8%8A%82%E7%82%B9%E7%8B%82%E9%AD%94/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026美国 
trojan://adbac894-90b9-4913-b77e-a715a8d4ebc8@oss-cn-shanghai.letssepub.com:20021?flow=&security=tls&sni=dingding-doc.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026香港 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMTAyNuiLseWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIxMDI26aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIxMDI26aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://joMd8MsTLV6of1GsaX3J4Zw7YR6xDRY8QUN@37.114.49.117:31834?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=JCEwXr7E0kq3ishJ77V6CR4XKdDKnxNDUEHkDbx&mport=&os=#1026德国 
anytls://oRet2qA4Jzegx5hY0QlQ3bYjnwWBHjm5@37.114.49.117:46768?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.42.49:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
hysteria2://RoErfo1wj7oXNxxykK61vOzAghxFmUa7A1oN3@37.114.49.117:17139?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=W9ICfYNqB3CGhhUQbN&mport=&os=#1026德国 
hysteria2://tl0zSpjaOdxNqCNzS3z35ViWbOlpQIpoNTM0@37.114.49.117:52855?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=rHmwTnGifWFdCqzR1&mport=&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.228.174:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
anytls://KuDisNHdOwnmt5zdYn@37.114.49.117:65499?insecure=1&sni=ssca.irundns.net&alpn=h2&fp=&os=#1026德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4xMTciLCJwb3J0IjoxOTIyOCwic2N5IjoiYXV0byIsInBzIjoiMTAyNuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlNDVjM2FkYi00ZTIwLTRkMWItYWFjZi05NzQ3YmIxN2I3ZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiL0tOeE5PRm1nNlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzY2EuaXJ1bmRucy5uZXQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4xMTciLCJwb3J0Ijo1NzAzNCwic2N5IjoiYXV0byIsInBzIjoiMTAyNuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhZmU2NWM1Yi1kYjI2LTQwN2ItYWI5MC0yNTEwYWUzNmYzNDMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNzY2EuaXJ1bmRucy5uZXQiLCJwYXRoIjoiLzlvNnRNU2pkTmR2eWM5TkwwUkl2P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzc2NhLmlydW5kbnMubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.97.141:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.89:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.49.233:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
hysteria2://eVt5ustHpN84fpJfK8WQhJWNCIAhf5Kbnl54@37.114.49.117:53739?insecure=1&sni=ssca.irundns.net&alpn=&fp=&obfs=salamander&obfs-password=uBnJAfuWfbb8jm1cTAmnL7z&mport=&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@190.93.245.63:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.24.205.235:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.153:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.112:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.215.192:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@162.159.18.195:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.26.13.81:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.114:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.25.18.25:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.70:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.235:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.59.65:443?flow=&encryption=none&security=tls&sni=tty.vock33.qzz.io&type=xhttp&host=tty.vock33.qzz.io&path=/ZETj2YLh24mig7%3F99abd410-b52d-4408-8942-bf0a25f4753e%3Fport%3D3000&mode=packet-up&alpn=h2&fp=edge&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1026德国 


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
