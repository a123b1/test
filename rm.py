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

vless://a47595a8-1add-401a-8189-e6799f8d8628@zcreat.ethervpn.fun:8443?flow=&encryption=none&security=tls&sni=zcreat.ethervpn.fun&type=ws&host=zcreat.ethervpn.fun&path=/websocketpl%3Fed%3D2047&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123俄罗斯 
ss://YWVzLTEyOC1nY206NzlhZDI4NTItZWI3Ni00YzNlLWJhNGQtMzY2OGVlNWVjZTc0@wangcai.singdns.com:23344?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://YWVzLTEyOC1nY206NzlhZDI4NTItZWI3Ni00YzNlLWJhNGQtMzY2OGVlNWVjZTc0@wangcai.singdns.com:21712?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123日本 
trojan://6e6191a3-9a93-4617-859a-8d0ea0fce937@joss.gpj1.web.id:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/81.91.214.85%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123捷克 
vmess://eyJ2IjoiMiIsImFkZCI6ImViYy56b29tLnVzIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMTEyM+WNsOW6piIsIm5ldCI6IndzIiwiaWQiOiI0NGU1NzQ4NS1lY2NjLTQ2ZWYtODA4Zi1jZDE3YWM4MTAwMTgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im5vZGU0LnJ0eGNvbmZpZ3ouY29tIiwicGF0aCI6Ii9ATWFsaW5kYTYxMDQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJub2RlNC5ydHhjb25maWd6LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@98.70.151.190:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpZekg0aWQ3WkV5S3BmeTM5RjJZY09tekNzQmtsR3doOA==@95.174.68.33:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123阿拉伯酋长国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@95.140.157.183:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@91.149.253.249:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@90.156.228.74:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@89.19.211.109:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.23:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.220:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.92.242:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidHJvamFuLmJ1cmdlcmlwLmNvLnVrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmFsaWJhYmEuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidHJvamFuLmJ1cmdlcmlwLmNvLnVrIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@80.76.32.12:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@8.217.180.234:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@77.221.157.32:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://4819860c-0e62-4804-9c59-967e5c2bed7a@77.110.119.225:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=st.ozone.ru&type=tcp&host=&path=/&headerType=none&alpn=&fp=chrome&pbk=hnec5SxCD6Os-u0FNi_YS5CML1a_oWb0niZJ1mGuFBo&sid=07e904766d29b958&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
trojan://8001fbf7-4b59-4415-a4bd-8bfded02c9c6@69.28.82.253:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/69.28.82.253%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123加拿大 
trojan://BxceQaOe@58.152.53.22:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123香港 
trojan://BxceQaOe@58.152.25.241:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123香港 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@52.68.194.189:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@51.195.43.174:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
trojan://e6f0e8b0-3dc5-4d53-a23a-86c02d5ba098@51.15.210.1:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/51.15.210.1%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1123法国 
trojan://e6f0e8b0-3dc5-4d53-a23a-86c02d5ba098@51.15.210.1:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/51.15.210.1%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123法国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@5.34.222.200:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
trojan://abb96ae5-8337-4719-b300-fc3b2efbd14d@47.89.150.45:21575?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/47.89.150.45%3D21575&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxUld3WGh3ZkFCNWdBRW96VTRHMlBn@45.87.175.166:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxN1pET1JXSWxpUUh1TzZXUkdIQ2hYWU16ZFJ0QVlWUA==@45.14.245.2:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123荷兰 
trojan://3208e968-b862-4e2e-ad90-2b49e7ce7afb@37.252.5.75:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/37.252.5.75%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1123爱沙尼亚 
trojan://3208e968-b862-4e2e-ad90-2b49e7ce7afb@37.252.5.75:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/37.252.5.75%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123爱沙尼亚 
trojan://fea8b7a7-cc83-4a78-a3fc-bbce9cc89ddb@34.22.190.30:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/34.22.190.30%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1123比利时 
trojan://0a477acf-1f95-47cb-b4a5-a627b4c57de3@34.22.190.30:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/34.22.190.30%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1123比利时 
trojan://0a477acf-1f95-47cb-b4a5-a627b4c57de3@34.22.190.30:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/34.22.190.30%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123比利时 
trojan://fea8b7a7-cc83-4a78-a3fc-bbce9cc89ddb@34.22.190.30:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/34.22.190.30%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123比利时 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpORFJ5U0lBQkFSYkVyTklWc0NOVmt5WUFIaUJ6aHZlVA==@23.95.75.146:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpVQU1WdEhtNTR1YWhkNlNpTjVXY0QxNnJzUFNkYWJQRw==@23.95.72.81:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://0f4f3a75-ae36-4992-8cb5-6638f45afcb2@216.133.148.215:36987?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTptYmhxc1N0bkZRVDFjVFpZQ2RzbWt1Z0dVQzZHVDZycA==@213.159.67.124:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123西班牙 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwbDJYdFIwcHp3a25RT0d3ZXdid1h0UFlEdzF6bjlWdQ==@213.159.66.206:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123巴西 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@213.142.149.3:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@206.189.25.65:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.77:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.54:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.160:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@194.35.119.49:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@194.35.119.135:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@193.123.90.82:12648?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpnWE9YazJGSndzejlQNm5YSUlDdUROT3FGOWdXWDFkbg==@185.156.110.92:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123克罗地亚共和国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@185.103.252.54:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://a00d89f6-ab7e-4e30-a5e5-54c701d62c93@178.236.16.98:35728?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=vhUFNoFcvtZAVMo8y5K5eU2V43m5q6yjmWIhp5RkFng&sid=69a2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123哈萨克 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@167.99.86.115:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
trojan://2cf6d686799e6fa95316394064f26c0a@160.16.63.16:4054?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1NC4yMS4yMDEuODMiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjExMjPnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNGJmMDc1ZjUtNGQ1ZS00ZDM5LWY1YWItYjMyYTg2MjUwZjBlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJoay5uYmVlLnBwLnVhIiwicGF0aCI6Ii9hYSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImhrLm5iZWUucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@154.17.225.73:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPRGZ4aW9LMFZrS3hUZHBWUUo0cnY4SGdsQXUwdnp2Ng==@146.19.49.251:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@142.132.140.130:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@139.185.34.131:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
trojan://0311306e-56d4-4aa1-bde5-8cede7fcd3e4@138.124.30.8:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/138.124.30.8%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1123荷兰 
trojan://0311306e-56d4-4aa1-bde5-8cede7fcd3e4@138.124.30.8:443?flow=&security=tls&sni=joss.gpj1.web.id&type=ws&header=none&host=joss.gpj1.web.id&path=/Free-VPN-CF-Geo-Project/138.124.30.8%3D443&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123荷兰 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@108.162.198.24:2096?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@108.162.198.11:2096?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpYTE9ydkxXa0NCQkJ4THFTRWU5UzhsbkM1UExzTmZSaA==@103.75.118.125:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123日本 
ss://YWVzLTEyOC1nY206NzlhZDI4NTItZWI3Ni00YzNlLWJhNGQtMzY2OGVlNWVjZTc0@103.219.103.217:21712?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123日本 
ss://YWVzLTEyOC1nY206NzlhZDI4NTItZWI3Ni00YzNlLWJhNGQtMzY2OGVlNWVjZTc0@103.219.103.217:23344?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1123美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMDgiLCJwb3J0IjoxOTQ2Nywic2N5IjoiYXV0byIsInBzIjoiMTEyM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI1YTk1ZDRmMS0xOWZmLTRlYTQtYjNiMi1iNGMyMDhkZmM4YTQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55YWhvby5jb20iLCJwYXRoIjoiL3d0WDlMVXRlUG5rP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cueWFob28uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.25.194.251:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
anytls://znOWYd0JaWomHw4a4Y7bE34@45.82.120.208:58087?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#1123德国 
anytls://GnB3t06qcLNjMytI55jvYYaM7p2qjYnmqaq@45.82.120.208:45004?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@162.159.62.219:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://b2723b49-6164-4876-8554-5d7421eec89f@45.82.120.208:43966?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/b1pGo0ExHOZgE9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
hysteria2://ytgmNmFZsenIOR7n6raTtb33wYfshbw6cynVk@45.82.120.208:4369?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=NgXQuYlx4QJGLLNfROu9yAA1k7TeyFzHF8hFtq&mport=&os=#1123德国 
hysteria2://mQRLLpDFCEfSyvESEQSy67F0CPg2Y@45.82.120.208:16971?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=rXjH1Y5E3ncK1OOhoxKBO3m&mport=&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.27.4.50:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://01008f22-1136-4ae8-ad82-a2a434782d7e@45.82.120.208:3028?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/SH0Duw89q730frfR2%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
hysteria2://0CD6Tva29NTXT8gdG@45.82.120.208:17394?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=X25VSOGg1opEVKAVwMhQqh57DP6VzvyPAQz&mport=&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.16.244.36:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@173.245.58.127:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.24.91.33:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@173.245.59.126:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@198.41.196.174:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.27.65.243:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@162.159.251.147:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@188.114.98.202:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@103.21.244.191:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@104.27.29.71:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@198.41.192.217:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 
vless://354888ca-3d51-4cd9-87c3-483887e5cfa5@198.41.196.251:443?flow=&encryption=none&security=tls&sni=moon.strosoa.dpdns.org&type=xhttp&host=moon.strosoa.dpdns.org&path=/ZETj2YLh24mig7%3Fbound%3D8&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1123德国 



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
