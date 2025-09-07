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


vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.116.7.158:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.160.204.145:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@103.181.165.246:12030?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906台湾 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.165.101:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.166.207:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.167.161:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.167.253:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@108.165.216.167:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTI1Ni1nY206ODRhOWNhMTgtN2M5Mi00YjEyLThiZGUtNDI4NDRiNzVjZDVi@128.199.56.167:8443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906荷兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@134.209.147.198:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906印度 
vless://401374e6-df77-41fb-f638-dad8184f175b@14.102.228.18:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.202.193:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@147.185.161.234:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@154.83.2.167:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://27b61a3e-ef8c-4bc8-923f-f4ac433d1056@157.230.16.250:50395?flow=&encryption=none&security=&sni=&type=kcp&host=&seed=K1nVjOzkLe&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
hysteria2://7GEEGxAfgQaVPQX0PGk7lIuj3I@158.41.110.234:10820?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0906英国 
vless://401374e6-df77-41fb-f638-dad8184f175b@159.112.235.235:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
hysteria2://peEduuHzbExjK7UQHzazXwqgA@166.88.164.9:27704?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.18:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@171.22.254.17:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906马耳他 
vless://401374e6-df77-41fb-f638-dad8184f175b@176.124.223.161:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@184.174.80.250:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.148.104.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.148.105.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.148.106.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.148.107.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/TelegramU0001F1E8U0001F1F3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906俄罗斯 
trojan://slch2024@185.156.19.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@185.16.110.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906法国 
trojan://slch2024@185.176.24.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906俄罗斯 
trojan://slch2024@185.176.26.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906哈萨克 
trojan://slch2024@185.18.184.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@185.18.250.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@185.221.160.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906香港 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906波兰 
trojan://slch2024@185.238.228.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=&path=/Telegram&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906西班牙 
trojan://slch2024@185.251.80.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906西班牙 
trojan://slch2024@185.251.81.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906西班牙 
trojan://slch2024@185.251.82.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906西班牙 
trojan://slch2024@185.251.83.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906西班牙 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.59.218.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906俄罗斯 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.58:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@185.7.240.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906法国 
trojan://slch2024@188.164.248.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906荷兰 
trojan://slch2024@188.164.248.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@188.244.122.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@188.42.145.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906俄罗斯 
trojan://slch2024@188.42.88.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906卢森堡 
trojan://slch2024@192.0.54.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@192.0.63.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@192.200.160.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192.227.152.86:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&mport=&os=#0906美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906希腊 
trojan://slch2024@193.124.224.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906捷克 
trojan://slch2024@193.124.224.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@193.227.99.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@193.9.49.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906俄罗斯 
trojan://slch2024@193.9.49.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@194.152.44.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@194.36.55.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906英国 
trojan://slch2024@194.59.5.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@194.76.18.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@195.13.44.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@195.13.44.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@195.13.45.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@195.13.54.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@195.13.55.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@195.13.55.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@195.26.229.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@195.26.229.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@195.85.59.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
vless://598b4251-fd03-48fe-b12d-630ac3adf2e5@198.62.62.2:443?flow=&encryption=none&security=tls&sni=smn2.gerlemondns.info&type=ws&host=&path=/hjgfdws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906英国 
trojan://slch2024@198.71.188.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@199.34.229.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@199.34.229.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@199.34.230.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@199.68.156.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906美国 
trojan://slch2024@199.68.156.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@205.233.181.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@209.46.30.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@209.46.30.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
trojan://slch2024@209.94.90.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@212.183.88.195:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0906香港 
trojan://slch2024@212.183.88.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906 
vless://784646e5-8e84-4672-8670-efc9cafcd2cc@212.95.34.12:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
trojan://slch2024@216.24.57.87:2096?flow=&security=tls&sni=ocost-dy.wmlefl.cc&type=ws&header=none&host=ocost-dy.wmlefl.cc&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906香港 
vless://401374e6-df77-41fb-f638-dad8184f175b@31.43.179.38:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@31.43.179.43:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.54.57.90:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906巴西 
ss://YWVzLTEyOC1nY206OGFhMGIwM2ItZTRjNi00MzY1LWFkMmQtZjZlOGE2OTQxMWFh@38.54.88.237:13890?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906日本 
ss://YWVzLTEyOC1nY206OGFhMGIwM2ItZTRjNi00MzY1LWFkMmQtZjZlOGE2OTQxMWFh@38.60.196.46:13888?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906英国 
hysteria2://2429bee3-e0c1-47dd-b420-75e6512b184b@40.233.102.224:30300?insecure=1&sni=www.bing.com&alpn=&fp=&mport=&os=#0906加拿大 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.142.120.139:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.153.7.133:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.159.218.165:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.80.110.128:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.80.111.32:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://3c1c08fd-4755-454a-9746-72efc50249ed@45.91.81.111:8881?flow=&encryption=none&security=reality&sni=addons.mozilla.org&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=gupSTIXodm3AFVUeU6rfxp_2jID7P7FK_I6CjyLO2ns&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://bf3e8944-8d26-47de-8748-b9aa74cce974@46.29.34.204:40721?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=TUZgwzcTvoROSbgnqMh3WorXVMxQNIF2zsEM39FQbyk&sid=df8611c07d&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906法国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpuWVJoVENaZFFMRXhLNmV3VkhnSFMybWx2NEZDeXNLeWV5VFRmaFJkRWdkZWVSTjA=@5.188.36.93:31348?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906土耳其 
trojan://1ce1df7962f71c6f@51.195.255.103:8443?flow=&security=tls&sni=uk-03.allhubb.info&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpxc2NhdkY1VXZpSUwtOFYtRTRyYUJB@62.133.63.226:2222?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906土耳其 
trojan://telegram-id-directvpn@63.179.50.132:22223?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
hysteria2://79c4fe11-9787-406b-bf94-c1c1dbf59e28@77.223.214.193:31468?insecure=1&sni=www.bing.com&alpn=&fp=&mport=&os=#0906德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@77.75.199.71:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@86.38.214.158:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@89.116.180.248:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906斯洛文尼亚共和国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=http/1.1%2Ch2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.191.80:443?flow=&encryption=none&security=tls&sni=pqh36v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTplVWg0bFNwaTduT1lqMHZTcnFMVWgw@95.163.176.37:8506?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906荷兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12023?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12030?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906台湾 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12031?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906台湾 
vless://54559d31-a4f0-4648-beeb-8323045a36c8@cb14.connectbaash.info:4414?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://789d4f30-c31b-4762-8116-ed42574d5e85@cdn26.saloonak.ir:8443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://789d4f30-c31b-4762-8116-ed42574d5e85@cdn27.saloonak.ir:8443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://789d4f30-c31b-4762-8116-ed42574d5e85@cdn28.saloonak.ir:8443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://789d4f30-c31b-4762-8116-ed42574d5e85@cdn29.saloonak.ir:8443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
ss://YWVzLTI1Ni1nY206ZTBjNDM0NWUtZjk0My00YTQ1LTk3N2ItNTE0ZmRlYzZmZmU5@entrance03.qqa678.cc:47083?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906日本 
vless://464ec76e-fd60-4ad4-993e-d2c262f88ed1@fr.pixvpn.app:8443?flow=&encryption=none&security=reality&sni=jd.com&type=grpc&host=&serviceName=grpc-jd&mode=gun&alpn=&fp=chrome&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid=41a4cee2c50c4fc3&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906英国 
ss://YWVzLTEyOC1nY206OGFhMGIwM2ItZTRjNi00MzY1LWFkMmQtZjZlOGE2OTQxMWFh@jianpuzai.tmdns-sing.top:13891?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0906柬埔寨 
trojan://1ce1df7962f71c6f@uk-03.allhubb.info:8443?flow=&security=tls&sni=uk-03.allhubb.info&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906英国 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDkwNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDkwNuaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwOTA2576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwOTA25oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTA26aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://Yet-Another-Public-Config-1@yapc-1.adamhayward.co.uk:35000?insecure=1&sni=YAPC-1.afshin.ir&alpn=&fp=&obfs=salamander&obfs-password=Yet-Another-Public-Config-1&mport=&os=#0906荷兰 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.20.51.130:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.252.210:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@188.114.98.210:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
anytls://Kxt9Sht0kfyzl1rgNqhixmfneodHFAP@45.82.121.53:24477?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@141.101.123.154:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.25.94.26:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@198.41.202.129:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
hysteria2://lnDTQVAeudv0cW60gmEYUZ2e0s92L21@45.82.121.53:64310?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=IlzNASnRGeE6tack431W2LrOCg6cO8dg&mport=&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.20.251.171:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.62.219:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@172.67.192.86:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@173.245.59.77:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
hysteria2://4Au0b0WhanaIqkFBURJ2mWnj2IZZ1TD7VOs7ZW@45.82.121.53:46354?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=zb8s2caVCtOTlRbfCh&mport=&os=#0906德国 
hysteria2://YJVR5swOvxYhr0zesQFfEXgUWTVvM8Xq9HNX6Y9I@45.82.121.53:55297?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=uBoCSepc8FVG5SvOrE5vhtsUbfwJYev&mport=&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.240.77:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.24.91.33:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@198.41.192.217:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.27.124.15:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@198.41.196.174:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.24.226.87:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.243.78:443?flow=&encryption=none&security=tls&sni=x3.jfhgytrueiowos.dpdns.org&type=xhttp&host=x3.jfhgytrueiowos.dpdns.org&path=/ZETj2YLh24mig7%3Fforward%3DTG.WangCai2.s4.db-link02.top&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjI2YWUxMmYtZDQ1Ny00YWM0LWI3YTQtNTQ0NmE1NGJjYjM0QDQ1LjgyLjEyMS41MzoxMTgxNDp3czovVnhpT1YyZmxGeDNPTkVaell2VGNDbkw1JTNGZWQlM0QyNTYwOmJ1cmdlcmlwLmNvLnVrOm5vbmU6dGxzOmJ1cmdlcmlwLmNvLnVrOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0906德国 
anytls://GCnPeKndJHTrVba5Ba571oF1RyNbAnJD8ouZMl@45.82.121.53:38495?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0906德国 
trojan://5f30d955-1aa0-4ef0-a276-adbb6c315b24@45.82.121.53:17694?flow=&security=tls&sni=burgerip.co.uk&type=ws&header=none&host=burgerip.co.uk&path=/cOfQYANlY9oao7Dqb368OlI5z%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0906德国 


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
