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


vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDcyM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjguaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723美国 
vless://c32819a3-bb1c-4e15-be00-ffcb657f8323@dl1-tr-cdn.easy-upload.org:2010?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723土耳其 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723美国 
vless://afdb6e6e-3145-4284-c15a-0a38030a8129@193.238.153.85:13305?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723美国 
vless://598d2298-5e1f-4d07-bc4b-6d1949693852@162.19.250.117:25921?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://133361c8-60e7-447a-dd5b-e7af60b9d115@193.238.153.84:33817?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723美国 
vless://c4ccf00e-72c6-4fd9-b7ce-f625a835539f@109.123.236.161:42692?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0OC4xMTMuNi44MSIsInBvcnQiOjQ5ODgyLCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz6aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiI2NjYzYTQyMi04NzVjLTQ0ZWUtOWEyNS0zZjdiMzM0ZGQ5ZjUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.38.148.178:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0723韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNiwic2N5IjoiYXV0byIsInBzIjoiMDcyM+iLseWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yNDkuMjA3LjI0OSIsInBvcnQiOjQwMTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz5pel5pysIiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0uYXZoeGMuY24iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206Y2ozU1R4KzBOd0xVUUZ2SldIYkttUT09@iepl.huli168.com:42277?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0723印度尼西亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0723斯洛文尼亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xMTYuNy4yNDEiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjI0OGJlNTJiLTM1ZDktMzRjYi05YjczLWUxMmI3OGJjMTMwMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0723波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOC4xNjUuMjE2LjI0MSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MjPnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMjQ4YmU1MmItMzVkOS0zNGNiLTliNzMtZTEyYjc4YmMxMzAxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206aVVCMDkyM1JCQQ==@154.3.8.151:30067?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0723香港 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwNzIz5oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@108.162.192.139:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@172.66.45.147:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.21.58.226:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.16.109.184:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@141.101.113.112:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.18.108.128:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.21.110.201:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.19.83.34:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@103.21.244.6:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xNDYiLCJwb3J0Ijo1MTM1OSwic2N5IjoiYXV0byIsInBzIjoiMDcyM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjMzE5NGViYi1hYjg4LTQ5NzMtOGVkMS03YjZjMTRhNDI2ZTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNtMS5hd3NsY24uaW5mbyIsInBhdGgiOiIvUz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiY20xLmF3c2xjbi5pbmZvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.25.184.190:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@190.93.244.170:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
anytls://9QWvH080WslZz9QNKpEtHzpuPO6xhq@45.82.121.146:24270?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#0723德国 
hysteria2://GGuTaEMyLNVdbp93nOh8EpMPRxZOJurCoQ24a@45.82.121.146:61727?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=D5BAyaCDNMJlw0eqdZKKkEFgfI6juyxrpU&mport=&os=#0723德国 
trojan://4fb60c9f-199b-439a-adb1-9293d9cdbe04@45.82.121.146:53961?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/yjyEebVTA6LuLImZL2qiR%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
anytls://AhA4pDy0Dol7zicCO7fvoCYY6alu2FM00@45.82.121.146:59303?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#0723德国 
hysteria2://L8HTvkRlq8rVbn293Z5y8uQ@45.82.121.146:50233?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=iUd5LVGlSPU3rfJrLE6wdoP7jGh5siwHM&mport=&os=#0723德国 
hysteria2://D6NKoWnCjOJZ4lgsX@45.82.121.146:42600?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=WVegMtgTXcKfKwnIqj&mport=&os=#0723德国 
vless://dbe41a05-ce75-4d00-baa5-344226b3ed36@45.82.121.146:53386?flow=&encryption=none&security=tls&sni=cm1.awslcn.info&type=ws&host=cm1.awslcn.info&path=/E1MiYyyhXQg%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.19.8.33:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.22.251:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
trojan://a1f79978-6d02-450a-9070-3de3212855ed@45.82.121.146:40101?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/0tvIcahl%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@190.93.244.134:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
hysteria2://t1w5935QJh5zMSne0BoOgypqmY@45.82.121.146:14405?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=EfmpbzBeh0bqdy7FezTAj1cTHLFk7ouVRaE&mport=&os=#0723德国 
trojan://4b0e7e22-dd3b-4a78-b532-333c860a4e53@45.82.121.146:49579?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/MmWCvwWaVz%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@141.101.123.23:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
hysteria2://ToI4U7ln1EZj0NbtJGQo0AoII@45.82.121.146:22037?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=8IFjjAABGIFCyl3CZXVXTE8Z9nKCySyw&mport=&os=#0723德国 
trojan://3cc172e6-ceb9-4781-9fad-ded68e73cf2d@45.82.121.146:38917?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/RVEHqpJvODwDqv4feOmDMsYcRyb9%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
hysteria2://HzYG2VEjIcj4qgQYrnFWyQQ@45.82.121.146:30220?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=FeYP1mdG2u1qfzPQwRLGBuI&mport=&os=#0723德国 
vless://5e9ddc29-d535-48ae-8797-81f9d2ce23a5@45.82.121.146:3319?flow=&encryption=none&security=tls&sni=cm1.awslcn.info&type=ws&host=cm1.awslcn.info&path=/aK%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@104.20.211.182:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 
vless://f8737ccc-0817-4cae-89ed-8c0c072d286b@162.159.254.11:443?flow=&encryption=none&security=tls&sni=uh.vidlx.qzz.io&type=xhttp&host=uh.vidlx.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0723德国 


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
