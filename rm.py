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

vless://6202b230-417c-4d8e-b624-0f71afa9c75d@103.219.194.43:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@116.44.53.251:12126?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.64.226:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.72.118:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.72.18:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.72.75:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.73.122:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.73.129:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.73.184:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.73.222:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.73.239:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.74.152:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.74.166:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.74.190:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.74.34:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@135.84.75.14:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@143.20.160.195:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@143.20.213.130:8443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@143.20.213.193:8443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://d65cc14c-f53f-4fe2-b262-97856601319c@143.20.236.51:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=e2RLf57Li_-MDZGE9ss1BWPgP54mqRb5PfXhW2jcVVg&sid=c39cc7310a&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305荷兰 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@153.121.45.101:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@185.110.189.174:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@185.16.110.0:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@185.236.26.30:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@188.253.26.128:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@192.200.160.20:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@195.133.44.199:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://5a4abb78-ecd7-4d68-ab2a-c11a3842f261@198.62.62.235:443?flow=&encryption=none&security=tls&sni=bank.alaska-tigr.info&type=ws&host=bank.alaska-tigr.info&path=/love&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305英国 
vless://5a4abb78-ecd7-4d68-ab2a-c11a3842f261@198.62.62.235:443?flow=&encryption=none&security=tls&sni=bank.alaska-tigr.info&type=ws&host=bank.alaska-tigr.info&path=/love&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305英国 
vless://5a4abb78-ecd7-4d68-ab2a-c11a3842f261@198.62.62.248:443?flow=&encryption=none&security=tls&sni=tar.alabama-tigr.info&type=ws&host=tar.alabama-tigr.info&path=/love&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://5a4abb78-ecd7-4d68-ab2a-c11a3842f261@198.62.62.248:443?flow=&encryption=none&security=tls&sni=tar.alabama-tigr.info&type=ws&host=tar.alabama-tigr.info&path=/love&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@199.107.164.217:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@199.34.230.158:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@199.34.230.66:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@202.84.53.85:19999?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@203.69.248.40:10443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@209.177.165.17:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@211.48.77.114:12312?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@216.24.57.4:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@217.60.39.10:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
trojan://c5355528-55a2-45df-b8fd-a48ce3c41413@220.130.58.136:35502?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
trojan://6f038cee-6ba1-4941-bce5-de1969f37405@220.130.58.136:35502?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@23.169.184.123:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@36.50.90.241:47790?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@45.145.42.211:2016?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@5.178.110.202:2053?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@63.141.128.9:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@77.110.120.225:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://fd8972d7-cf5e-11f0-9970-45e1d80c4039@78.153.139.68:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=images.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=random&pbk=pekfYPV5U8EjfQ4_zS5c6I2NnOZ2jUlyMGAWa4FWPF4&sid=58c512b4422e2517&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305芬兰 
vless://fd8972d7-cf5e-11f0-9970-45e1d80c4039@78.153.139.68:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=images.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=pekfYPV5U8EjfQ4_zS5c6I2NnOZ2jUlyMGAWa4FWPF4&sid=58c512b4422e2517&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305芬兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiI/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiNDEyMC1CRTA0LTEzZWY1NjA5Njk4OS40NTcuUFAudWEiLCJwYXRoIjoiL2tUNVZIWWNNcnBoZXNxUk96U1BvSHJCbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY2RuZmlyZS54aWFvbWlzcGVlZC5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMjAwMTpiYzg6MzJkNzozMDI6OjEwIiwicGF0aCI6Ii8/ZWQ9MjA0OCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiODIuMTk4LjI0Ni45NyIsInBhdGgiOiJlZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@85.208.139.98:8443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@89.58.26.175:2083?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@94.141.123.231:443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://6202b230-417c-4d8e-b624-0f71afa9c75d@95.182.97.125:8443?flow=&encryption=none&security=tls&sni=sni.111000.dynv6.net&type=ws&host=sni.111000.dynv6.net&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305加拿大 
vless://60c4d55d-bee3-4719-9568-aabf45153f9f@c6y.0c0.ccwu.cc:80?flow=&encryption=none&security=&sni=c6y.0c0.ccwu.cc&type=ws&host=c6y.0c0.ccwu.cc&path=/gPvZ4oCcNDyuc3szX7xhuvpEm&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
ss://YWVzLTEyOC1nY206SlZyc0xMTjF0a044b1haTw==@chengbai02.ascwt179.com:13223?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0305英国 
vless://79149019-5abe-46f9-91ae-e1e7d1d2c408@dns.dressforida.monster:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.techradar.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=4YLfHf90V012Oyd2wHbwAXaJNvNUGrKWmatTKc165U8&sid=174c6cf22e22&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305荷兰 
vless://4ef1e946-aa74-4ce3-8875-4339a07d46aa@ffgghjuuuuui.007770777.xyz:443?flow=&encryption=none&security=tls&sni=ffgghjuuuuui.007770777.xyz&type=ws&host=ffgghjuuuuui.007770777.xyz&path=/gswYtzBd52XmedI6YBH&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
trojan://04e5b584-1850-483d-a844-9ad624a4ca8e@green2.cdntencentmusic.com:35501?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://60c4d55d-bee3-4719-9568-aabf45153f9f@huu89.0h0.ccwu.cc:80?flow=&encryption=none&security=&sni=huu89.0h0.ccwu.cc&type=ws&host=huu89.0h0.ccwu.cc&path=/gPvZ4oCcNDyuc3szX7xhuvpEm&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://337bf72e-bb79-4d5f-be3f-7822eb77100c@hwefesw.aloiacs.shop:2087?flow=&encryption=none&security=tls&sni=TxLiD9gF4r.InDoSoXr.InFo&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305摩尔多瓦 
ss://YWVzLTI1Ni1nY206ZzRKdHBrdXhrd1JINGpoag==@iepl.huli168.com:19822?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=0&fragment=,100-200,10-60&os=#0305日本 
vless://5f6c3f92-7220-4275-b34d-57c04db3f967@nnmkki9.6no.ccwu.cc:80?flow=&encryption=none&security=&sni=&type=ws&host=nnmkki9.6no.ccwu.cc&path=/F24D1rlC85bVBOSONBms&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZGFjZC5jb20iLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDMwNee+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJicGJnLmFuZ3Vzd2VuLnRvcCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJuMTc0NDQ1NDQ5OC5saWU1ZC5jeW91IiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjZG5maXJlLnhpYW9taXNwZWVkLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3czLmdhaXVvaHIuY2xvdWQtaXAuY2MiLCJwYXRoIjoiL3Jpb3V0Z2hld2l1b3JyaDk4MjNyIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhkYWNkLmNvbSIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMzA1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiJjaHJvbWUiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhkYWNkLmNvbSIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMzA1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://uYKKsx9uMF2CwVsw7eTT@109.71.253.110:50721?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=CosZAbDcDv7ANk6PtHSyZgma41bAAUvbtxY3hKoP&mport=&os=#0305德国 
hysteria2://LZEqIpDbeiEnS0ym4lHyR4RzbREMQVs8gdA2Eg@109.71.253.110:27753?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=pC2qqNVeMdMFVOR4lkhTSmH4zEohE&mport=&os=#0305德国 
vless://df5dc5a7-f6cc-4bf0-8cda-d9a2dd54a27c@109.71.253.110:57476?flow=&encryption=none&security=tls&sni=www.jquery.com&type=ws&host=www.jquery.com&path=/3Xs4D0Z5JC8xuznqtaH1YE%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MjA2NjdhOWItYTg0MS00MDZkLWFmOTEtMTdjYjQ3MjJjZWQ0QDEwOS43MS4yNTMuMTEwOjQ5NDc6d3M6L3BxJTNGZWQlM0QyNTYwOnd3dy5qcXVlcnkuY29tOm5vbmU6dGxzOnd3dy5qcXVlcnkuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0305德国 
trojan://8c2bf9d4-e29d-42b3-a53b-29f7fe3392d2@109.71.253.110:30199?flow=&security=tls&sni=www.jquery.com&type=ws&header=none&host=www.jquery.com&path=/y%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://8fb87d41-f68a-47d5-8b8c-6c930dbcbe5d@109.71.253.110:35748?flow=&encryption=none&security=tls&sni=www.jquery.com&type=ws&host=www.jquery.com&path=/QpsKHsUWnWSyw%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
anytls://iZmDbN4PrTQt4707leYZg5nrFH9f@109.71.253.110:48094?insecure=1&sni=www.jquery.com&alpn=h2&fp=&os=#0305德国 
hysteria2://lgBbDFTzZy5ZhCA6gl@109.71.253.110:57691?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=nMXY6kLCqZhKB0Hijl&mport=&os=#0305德国 
hysteria2://HF7F34KZ6IeCSoaJNDDOOLg8@109.71.253.110:54924?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=EyAkO5VkT8G4Ami7N9Ckn&mport=&os=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTEwIiwicG9ydCI6NTY5Niwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJkZjVkYzVhNy1mNmNjLTRiZjAtOGNkYS1kOWEyZGQ1NGEyN2MiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5qcXVlcnkuY29tIiwicGF0aCI6Ii9NQTJzMGFTOFVCdktqOG1XeG9lUT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3LmpxdWVyeS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
anytls://egBGMt57ALXGiBl6g15RASSVtdaiLhUy5UUrY@109.71.253.110:31833?insecure=1&sni=www.jquery.com&alpn=h2&fp=&os=#0305德国 
hysteria2://Hy5St4quwUbaiGQGlYl@109.71.253.110:35910?insecure=1&sni=www.jquery.com&alpn=&fp=&obfs=salamander&obfs-password=CNZCTuTmod5SLtsJuGGw&mport=&os=#0305德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@wheatscabjom.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=wheatscabjom.oceanof.xyz&type=xhttp&host=wheatscabjom.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@bygonel.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=bygonel.oceanof.xyz&type=xhttp&host=bygonel.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@defrosterbd.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=defrosterbd.oceanof.xyz&type=xhttp&host=defrosterbd.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@argyley.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=argyley.oceanof.xyz&type=xhttp&host=argyley.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@backwardnlx.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=backwardnlx.oceanof.xyz&type=xhttp&host=backwardnlx.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@appellantj.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=appellantj.oceanof.xyz&type=xhttp&host=appellantj.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@alarmingig.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=alarmingig.oceanof.xyz&type=xhttp&host=alarmingig.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@prepayuhu.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=prepayuhu.oceanof.xyz&type=xhttp&host=prepayuhu.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@ectoproctalp.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ectoproctalp.oceanof.xyz&type=xhttp&host=ectoproctalp.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@sympathizeny.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=sympathizeny.oceanof.xyz&type=xhttp&host=sympathizeny.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@sculptorklu.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=sculptorklu.oceanof.xyz&type=xhttp&host=sculptorklu.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@hypoxisaml.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=hypoxisaml.oceanof.xyz&type=xhttp&host=hypoxisaml.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@cutterz.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=cutterz.oceanof.xyz&type=xhttp&host=cutterz.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@seamlesscv.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=seamlesscv.oceanof.xyz&type=xhttp&host=seamlesscv.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@heronshj.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=heronshj.oceanof.xyz&type=xhttp&host=heronshj.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305美国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@162.159.18.195:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.18.248.218:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@141.101.113.130:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.203:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.24.205.235:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.235:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.18.24.219:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.215.192:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.225.87:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@141.101.121.129:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.78:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@190.93.245.63:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.97.141:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.16.228.174:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.242:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.19.133.213:443?flow=&encryption=none&security=tls&sni=so.cjowefs.qzz.io&type=xhttp&host=so.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0305德国 


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
