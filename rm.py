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
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpOazlhc2dsRHpIemprdFZ6VGt2aGFB@arxfw2b78fi2q9hzylhn.freesocks.work:443#1212 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@103.44.255.81:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@57.181.42.233:443#1212日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.169.221.38:443#1212新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTE2IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjI0IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMjE5IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTM3IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjA5IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiYzY1ZmFjMi03ZGM3LTQyNmYtYWNkZC0wNzc5YTUwMzViZGUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InAxLjYxMzA1NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuNjciLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIxMjEy576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkOTJmZmM5LTAyZTEtNDA4Ny04YTQ2LWNjNGQ3NjU2MDkxNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZTUuODA4MDc1Lnh5eiIsInBhdGgiOiJnaXRodWIuY29tL0FsdmluOTk5OSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTQ2IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiYzY1ZmFjMi03ZGM3LTQyNmYtYWNkZC0wNzc5YTUwMzViZGUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InAxLjYxMzA1NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTUzIiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiYzY1ZmFjMi03ZGM3LTQyNmYtYWNkZC0wNzc5YTUwMzViZGUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InAxLjYxMzA1NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.187.153:443#1212新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMjIxIiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.200.142:443#1212美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.213.67.37:443#1212新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpOazlhc2dsRHpIemprdFZ6VGt2aGFB@160.19.78.75:443#1212越南 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjI0NyIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2Q5MmZmYzktMDJlMS00MDg3LThhNDYtY2M0ZDc2NTYwOTE3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJlNS44MDgwNzUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://QwwHvrnN@36.151.192.203:25241?flow=&security=tls&sni=36.151.192.203&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212香港 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.142:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjE4OCIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2Q5MmZmYzktMDJlMS00MDg3LThhNDYtY2M0ZDc2NTYwOTE3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJlNS44MDgwNzUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.125:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjE0MiIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2Q5MmZmYzktMDJlMS00MDg3LThhNDYtY2M0ZDc2NTYwOTE3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJlNS44MDgwNzUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.179:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjI5IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xLjEwNjc3OC54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.147:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.91:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.86:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.13:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.88:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjIwOCIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTBmOGY0ZGMtODA5Mi00MzU1LTkwNDctMDVmNTA2ZjVlOWFiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJtMS4xMDY3NzgueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.41:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.209:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.249:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.4:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.145:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.114:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNy4xNzIuMjM1Ljc1IiwicG9ydCI6Mzc1NjksInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMDExNWNmOWUtYTRiMC00ZGM2LWE1MDYtNmM5YTcyOGE1ODY0IiwiYWxwbiI6ImgyLGh0dHAvMS4xIiwiZnAiOiJlZGdlIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJkeG9iRzRhWm1rLmdhZm5vZGUuc2JzIiwicGF0aCI6Ii9zcGVlZHRlc3QiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkeG9iRzRhWm1rLmdhZm5vZGUuc2JzIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.100:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.220:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
hysteria2://0115cf9e-a4b0-4dc6-a506-6c9a728a5864@107.172.235.75:47443?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@107.172.235.55:1024?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.212:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.64:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTM1IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.203:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.54:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.241:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.77:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@129.151.198.3:8443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.70:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMzMiLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIxMjEy576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkOTJmZmM5LTAyZTEtNDA4Ny04YTQ2LWNjNGQ3NjU2MDkxNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZTUuODA4MDc1Lnh5eiIsInBhdGgiOiJnaXRodWIuY29tL0FsdmluOTk5OSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@104.19.34.126:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.185:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.220:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.105:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@143.47.243.144:8443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://ab99638d-1d04-451c-92a4-89364d0570f4@151.101.64.155:80?flow=&encryption=none&security=&sni=&type=ws&host=join-bede-CONFIGT.OrG&path=/lW0tvTq4oSbHyKeRM%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212英国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.185:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTI0IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuNDAiLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIxMjEy576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkOTJmZmM5LTAyZTEtNDA4Ny04YTQ2LWNjNGQ3NjU2MDkxNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZTUuODA4MDc1Lnh5eiIsInBhdGgiOiJnaXRodWIuY29tL0FsdmluOTk5OSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTAwIiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTIyIiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.242:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@14.39.254.65:50000?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212韩国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@join.my.telegram.channel.cmliussss.to.unlock.more.premium.nodes.cf.090227.xyz:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://995dc2bd-bafb-4343-9945-10283a9dee4a@194.226.49.245:33679?flow=&encryption=none&security=&sni=&type=ws&host=bestm03&path=/bestm03&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212俄罗斯 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.48:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.235:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.59:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTQyIiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xLjEwNjc3OC54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.38:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://8e6c2e8d-3574-4cea-bb03-118e5cb9cc13@57.129.55.94:443?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212法国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.171:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.139:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.10:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://9a2eeb28-0baa-5f9a-9926-ac3189543551@199.232.125.59:443?flow=&encryption=none&security=tls&sni=JOiN--E-L-I-V-2-R-A-Y.net&type=ws&host=JOiN--E-L-I-V-2-R-A-Y.net&path=/fp%3Dsafari&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212土耳其 
trojan://QwwHvrnN@36.151.192.198:31071?flow=&security=tls&sni=36.151.192.198&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212日本 
trojan://DNUMdmnJ@36.151.192.239:42395?flow=&security=tls&sni=36.151.192.239&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212香港 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@59.3.3.161:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212韩国 
vless://9df625ba-7d04-405d-9d54-2c8c1e5fbccb@69.84.182.187:443?flow=&encryption=none&security=tls&sni=cc.aimercc.filegear-sg.me&type=ws&host=cc.aimercc.filegear-sg.me&path=/proxyip%3Dproxyip.us.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjExMCIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2Q5MmZmYzktMDJlMS00MDg3LThhNDYtY2M0ZDc2NTYwOTE3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJlNS44MDgwNzUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@154.17.21.134:18446?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.67:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.49:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.94:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjA5IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xLjEwNjc3OC54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.27:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.161:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.9:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@132.145.54.84:8443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.140:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.145:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.90:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjciLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIxMjEy576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkOTJmZmM5LTAyZTEtNDA4Ny04YTQ2LWNjNGQ3NjU2MDkxNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZTUuODA4MDc1Lnh5eiIsInBhdGgiOiJnaXRodWIuY29tL0FsdmluOTk5OSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@104.19.56.96:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMTA2IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.137:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.227:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjY1IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiYzY1ZmFjMi03ZGM3LTQyNmYtYWNkZC0wNzc5YTUwMzViZGUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InAxLjYxMzA1NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.199:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.111:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@129.146.59.212:8443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.43:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.111:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.204:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.183:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.84:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.39:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@158.180.89.73:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.132:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuMi4xMzMiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMuazleWbvSIsIm5ldCI6IndzIiwiaWQiOiJhOTgzYzY5OC1jYWU0LTQyNTQtZDA0Ny01MTg5OGNjZDhlZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImtpbS5nb3Yua3AiLCJwYXRoIjoiL2FyaWVzP2VkPTIwNDgiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@92.118.205.85:20022#1212波兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.233:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.186:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@104.19.46.207:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@130.162.228.90:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212韩国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.226:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@140.238.23.148:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212韩国 
hysteria2://0115cf9e-a4b0-4dc6-a506-6c9a728a5864@151.249.104.35:34623?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#1212捷克 
vless://bd2914ed-69b1-4533-a7f0-929527541c35@104.24.196.20:80?flow=&encryption=none&security=&sni=dl5.heykakenakhshanemvaberanakhshanemkhadijeomanigakobraoaminfatema.com&type=ws&host=dl5.heykakenakhshanemvaberanakhshanemkhadijeomanigakobraoaminfatema.com&path=/Mmdv2rayng-V2rayngmmd-telegram-mmd_v2rayng%3Fed%3D80&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212德国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@158.178.238.239:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjExMiIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTBmOGY0ZGMtODA5Mi00MzU1LTkwNDctMDVmNTA2ZjVlOWFiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJtMS4xMDY3NzgueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@138.2.69.236:23334?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.215.84.62:443#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjE1IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xMjUuMTA2Nzc4Lnh5eiIsInBhdGgiOiIvZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.152.184:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4yNDkuMTA0LjM1IiwicG9ydCI6MzQ2NzEsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLmjbflhYsiLCJuZXQiOiJ3cyIsImlkIjoiMDExNWNmOWUtYTRiMC00ZGM2LWE1MDYtNmM5YTcyOGE1ODY0IiwiYWxwbiI6ImgyLGh0dHAvMS4xIiwiZnAiOiIzNjAiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImR4b2JHNGFabWsuZ2Fmbm9kZS5zYnMiLCJwYXRoIjoiL3NwZWVkdGVzdCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImR4b2JHNGFabWsuZ2Fmbm9kZS5zYnMiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.43:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@198.62.62.139:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@140.83.61.244:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212澳大利亚 
ss://YWVzLTI1Ni1jZmI6WFB0ekE5c0N1ZzNTUFI0Yw==@217.30.10.18:9025#1212波兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.250:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@141.11.125.215:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212法国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyRXRQcW42SFlqVU5jSG9oTGZVcEZRd25makNDUTVtaDFtSmRFTUNCdWN1V1o5UDF1ZGtSS0huVnh1bzU1azFLWHoyRm82anJndDE4VzY2b3B0eTFlNGJtMWp6ZkNmQmI=@84.19.31.63:50841#1212德国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@69.84.182.232:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
ss://YWVzLTI1Ni1jZmI6Z1lDWVhma1VRRXMyVGFKUQ==@217.30.10.18:9038#1212波兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@104.168.43.27:37190?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@43.135.44.101:30002?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212澳大利亚 
vless://65364f16-a80d-4879-a22a-fdb81340d0c2@www.speedtest.net:443?flow=&encryption=none&security=tls&sni=54153597949886727526628702092980.v2line.net&type=ws&host=54153597949886727526628702092980.v2line.net&path=/v2line-amsterdam-netherlands-vl-ws-tls-advanced&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212荷兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@47.57.233.126:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://6b469585-4a07-4387-89cc-b28da026a9a7@212.192.13.179:9187?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@8.218.148.106:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
ss://YWVzLTI1Ni1jZmI6WkVUNTlMRjZEdkNDOEtWdA==@217.30.10.18:9005#1212波兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@138.2.123.70:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@172.67.27.46:80?flow=&encryption=none&security=&sni=cc.ailicf.us.kg&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@13.230.34.30:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjQ0IiwicG9ydCI6MjA4Niwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZDkyZmZjOS0wMmUxLTQwODctOGE0Ni1jYzRkNzY1NjA5MTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImU1LjgwODA3NS54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4yMzguMjQ2IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xLjEwNjc3OC54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xMTQuMTU3IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxMue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5MGY4ZjRkYy04MDkyLTQzNTUtOTA0Ny0wNWY1MDZmNWU5YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xLjEwNjc3OC54eXoiLCJwYXRoIjoiZ2l0aHViLmNvbS9BbHZpbjk5OTkiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjI1MCIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2Q5MmZmYzktMDJlMS00MDg3LThhNDYtY2M0ZDc2NTYwOTE3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJlNS44MDgwNzUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yNi4wLjE0MSIsInBvcnQiOjIwODYsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYmM2NWZhYzItN2RjNy00MjZmLWFjZGQtMDc3OWE1MDM1YmRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJwMS42MTMwNTUueHl6IiwicGF0aCI6ImdpdGh1Yi5jb20vQWx2aW45OTk5IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE2My41LjE1OS4yMzEiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiZTUzN2YyZjUtMmEwYy00ZjU5LTkyYzktODMyY2E2NDMzYmYzIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpcnZpZGVvLmNmZCIsInBhdGgiOiIvbGlua3dzIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiaXJ2aWRlby5jZmQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@210.61.97.241:81?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@104.22.53.235:80?flow=&encryption=none&security=&sni=cc.ailicf.us.kg&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@162.159.153.235:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
vless://d5285e2d-f110-4bd9-a15a-36febf08428d@212.192.13.51:8307?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.231.184:443#1212新加坡 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@219.76.13.164:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@141.147.147.180:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212瑞典 
vmess://eyJ2IjoiMiIsImFkZCI6InJvb3QubWlkLmFsIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTLms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiYTk4M2M2OTgtY2FlNC00MjU0LWQwNDctNTE4OThjY2Q4ZWU3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJraW0uZ292LmtwIiwicGF0aCI6Ii9hcmllcz9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@35.219.15.90:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
ss://YWVzLTI1Ni1jZmI6cDl6NUJWQURIMllGczNNTg==@217.30.10.18:9040#1212波兰 
vless://71ed6628-5870-4d19-8a52-f2a3ba3d4898@47.243.237.160:443?flow=&encryption=none&security=tls&sni=aba.zhuk.us.kg&type=ws&host=aba.zhuk.us.kg&path=/youlingkaishi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212中国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.211.105.26:443#1212美国 
vless://9df625ba-7d04-405d-9d54-2c8c1e5fbccb@138.2.66.92:443?flow=&encryption=none&security=tls&sni=cc.aimercc.filegear-sg.me&type=ws&host=cc.aimercc.filegear-sg.me&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1212美国 
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
