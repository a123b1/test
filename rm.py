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
vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.160.204.145:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.167.161:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@154.83.2.167:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@184.174.80.250:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
trojan://slch2024@185.148.107.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/TelegramU0001F1E8U0001F1F3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913新加坡 
trojan://slch2024@185.156.19.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913新加坡 
trojan://slch2024@185.18.184.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@185.221.160.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@185.238.228.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913西班牙 
trojan://slch2024@185.251.80.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913西班牙 
trojan://slch2024@185.251.81.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
trojan://slch2024@185.7.240.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@192.0.54.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913 
trojan://slch2024@192.0.63.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@192.200.160.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@192.65.217.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913澳大利亚 
trojan://slch2024@193.124.224.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@193.124.224.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@193.9.49.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913俄罗斯 
trojan://slch2024@193.9.49.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@194.152.44.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913新加坡 
trojan://slch2024@194.36.55.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913新加坡 
trojan://slch2024@194.76.18.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/%E7%94%B1%E9%9B%B6%E5%BC%80%E5%A7%8B&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913俄罗斯 
trojan://slch2024@194.76.18.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@195.26.229.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@195.85.59.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@198.62.62.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@199.34.229.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@209.46.30.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913 
trojan://slch2024@209.94.90.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913香港 
trojan://slch2024@212.183.88.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913 
vmess://eyJ2IjoiMiIsImFkZCI6IjIxMi4xOTIuMTUuNzMiLCJwb3J0IjoyMzE3MCwic2N5IjoiYXV0byIsInBzIjoiMDkxM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjNjdjZTE5MS00NjZiLTRhMzEtYWUxOS01ZWM4ODZlNDMwMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://slch2024@213.241.198.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/TelegramU0001F1E8U0001F1F3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0913新加坡 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0913韩国 
vless://e0042666-497b-4fde-bf4a-c5281df24d15@45.130.214.192:20992?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913拉脱维亚 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://bf3e8944-8d26-47de-8748-b9aa74cce974@46.29.34.204:40721?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=TUZgwzcTvoROSbgnqMh3WorXVMxQNIF2zsEM39FQbyk&sid=df8611c07d&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913法国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ3Ljc5LjQyLjIyNiIsInBvcnQiOjU3NDY5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTEz5pel5pysIiwibmV0Ijoia2NwIiwiaWQiOiIzNWZlYWQ2ZC0zMWVlLTQwYTAtOTk5Yi05MjkzYzkzN2QxMjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiJCSXY0M1FpbWplIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@89.116.180.248:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0913斯洛文尼亚共和国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913美国 
vless://08604288-670b-4663-854d-fa47ab3fe068@cloud4.leechirankadeh.cloud:2096?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0913韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDkxM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDkxM+aWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwOTEz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwOTEz5oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTEz6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@198.41.196.251:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.59.126:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.25.202.125:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.29.71:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.24.9.3:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@190.93.247.114:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.58.127:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.4.50:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@162.159.251.147:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.20.64.155:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
hysteria2://Soc32ZJ2WzinalajczhQseLpU@45.82.122.139:20060?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=lYaf3roZ0GfFR7b4C6884xdf5nL4TP5u2hNmE&mport=&os=#0913德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWYxZjZmYjMtMzRkYy00M2JjLTkzNTAtYTI4OTlhZDc0OWQ3QDQ1LjgyLjEyMi4xMzk6NTEyNDg6d3M6L0szRWtHZHFSOXRvdzlmTExBV0k2S1QlM0ZlZCUzRDI1NjA6d3d3LnlhaG9vLmNvbTpub25lOnRsczp3d3cueWFob28uY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.16.244.36:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://dbfd9260-1bf5-49bd-ae4a-d6aeba30ebdc@45.82.122.139:40760?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/DBkEnDlHMx2RruYE4WECOa5Dt9iBG3%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
trojan://5f1f6fb3-34dc-43bc-9350-a2899ad749d7@45.82.122.139:37022?flow=&security=tls&sni=www.yahoo.com&type=ws&header=none&host=www.yahoo.com&path=/f3SueE%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@188.114.98.202:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.25.194.251:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4xMzkiLCJwb3J0Ijo1NjYwOSwic2N5IjoiYXV0byIsInBzIjoiMDkxM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlMTA3NjFmZS1jNjM4LTQyNDEtYWRiMy0yZGIwY2JhMmZlZTQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55YWhvby5jb20iLCJwYXRoIjoiLzZmcGNlSTBHeDBWNkd2Qlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy55YWhvby5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4xMzkiLCJwb3J0Ijo1MzY4LCJzY3kiOiJhdXRvIiwicHMiOiIwOTEz5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjgwMGFkY2MyLTUzNGUtNGUzNS1iOWQ4LWU1ZGZhMGJiMzAxNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LnlhaG9vLmNvbSIsInBhdGgiOiIvelNOUlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy55YWhvby5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://ScTd57PB6yeVju78XIFh8yl9IZWOLVJ3Gp@45.82.122.139:52371?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=0sQk4h7vV7MaOg29gseoHOJcTbMQlO6k5G&mport=&os=#0913德国 
anytls://Z5QoQlPBUu342BdxdPswrfnji@45.82.122.139:14022?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#0913德国 
anytls://5OjTklEgnXzqaMH3Q6WDsrX5dnT0UA@45.82.122.139:49737?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.191:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.19.243.241:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0913德国 

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
