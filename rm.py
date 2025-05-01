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

vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNDMw5pel5pysIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0430以色列 
ss://YWVzLTEyOC1nY206Vk1oR3A1d0VJeUNEZjkwVA==@gysz0000.dynu.net:56277#0430印度 
trojan://c702521f-8953-4bb0-95df-ec0479d68c1a@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27201?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430台湾 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0430孟加拉国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0430斯洛文尼亚共和国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0430新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzY2MDksInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTI5MSwic2N5IjoiYXV0byIsInBzIjoiMDQzMOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTc4NTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0430日本 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0430法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0430波兰 
vless://7c317161-5cf8-4cbc-811a-d1297c41bb23@152.67.68.116:443?flow=xtls-rprx-vision-udp443&encryption=none&security=tls&sni=yapc-1.afshin.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430瑞士 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@172.67.204.22:443?flow=&security=tls&sni=1SdfghJk.890602.xyz&type=ws&header=none&host=&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430美国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@137.175.113.193:8388#0430美国 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://3c461e2c-9d13-11ef-8563-f23c913c8d2b@4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net:8443?insecure=0&sni=4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://2ee8f830-09e2-11f0-90e2-f23c913c8d2b@5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net:8443?insecure=0&sni=5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://c11ff50c-f582-11ee-94df-f23c9164ca5d@74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net:8443?insecure=0&sni=74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://be8ba532-0dcf-11f0-9a65-f23c9164ca5d@8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net:8443?insecure=0&sni=8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://7af3db60-b2d9-11ef-88ab-f23c913c8d2b@b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net:8443?insecure=0&sni=b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://8de795d2-a06f-11ed-8edf-f23c913c8d2b@bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net:8443?insecure=0&sni=bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://80aa5178-f936-11ed-8ce6-f23c91369f2d@c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net:8443?insecure=0&sni=c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://279b8588-616b-11ed-a8bf-f23c91cfbbc9@cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net:8443?insecure=0&sni=cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0430美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDMw576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJvY2JjLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNDMw576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDQzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDQzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDQ0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDY1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192-227-152-86.nip.io:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&os=#0430美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0430英国 
trojan://59838af2-1171-4033-8686-02f2198d6f46@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27002?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430日本 
trojan://dabb4fca-ae9a-45e9-af87-d9602dc05ef7@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:34017?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430澳大利亚 
trojan://42e81557-3749-4d0d-8def-2f730ff60b27@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43395?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430泰国 
trojan://1e0a3f8d-dd1a-49f5-9d78-70f191f70ca4@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43396?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430越南 
hysteria2://b8886785-9e99-4791-b11b-e1a7f63cfe51@23.132.228.217:58339?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0430美国 
hysteria2://b8886785-9e99-4791-b11b-e1a7f63cfe51@85.235.205.212:36012?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0430俄罗斯 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@121.14.61.174:8313?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430香港 
vless://9e769ce1-34be-4e3f-b0a6-823f30eb8f69@205.233.181.186:8443?flow=&encryption=none&security=tls&sni=CiR346yL3b.DeRaKhT.iNfO&type=ws&host=CiR346yL3b.DeRaKhT.iNfO&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430摩尔多瓦 
trojan://telegram-id-vlessconfig@18.184.137.232:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
hysteria2://0caa5855-3a02-47be-b2cc-fcd7f99dd32b@sg05.tkgow.top:8080?insecure=0&sni=&alpn=&fp=&os=#0430新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNywic2N5IjoiYXV0byIsInBzIjoiMDQzMOWhnua1pui3r+aWryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Im9jYmMuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://c8b9db60-2132-11f0-880d-1239d0255272@uk1.test3.net:443?flow=&security=tls&sni=uk1.test3.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430英国 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@dozo01.flztjc.top:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430香港 
trojan://2c605663-b89a-5734-a9d6-97d4743d72cf@183.232.235.2:8313?flow=&security=tls&sni=hk-13-568.flztjc.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430香港 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDQzMOaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzI5ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImpwNC5nMi5tb29uYmFzZS5saWZlIiwicG9ydCI6MzUyMTQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDml6XmnKwiLCJuZXQiOiJ3cyIsImlkIjoiNDZhNTM5ZDItZDNiYS00YTZlLWFlZGItYjcyN2QyZmM2MGY4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3ZWIueGNqcy5pbmZvIiwicGF0aCI6Ii9ob21lIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid2ViLnhjanMuaW5mbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6ImpwMy52aXAyLmcyLm1vb25iYXNlLmxpZmUiLCJwb3J0IjozNTI0Mywic2N5IjoiYXV0byIsInBzIjoiMDQzMOaXpeacrCIsIm5ldCI6IndzIiwiaWQiOiI0NmE1MzlkMi1kM2JhLTRhNmUtYWVkYi1iNzI3ZDJmYzYwZjgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IndlYi54Y2pzLmluZm8iLCJwYXRoIjoiL2hvbWUiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3ZWIueGNqcy5pbmZvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQwMTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1NDY1Miwic2N5IjoiYXV0byIsInBzIjoiMDQzMOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@45.131.6.160:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430英国 
vless://838f5273-5d2d-4630-a0f5-9cc8e4aef4d6@188.42.88.45:443?flow=&encryption=none&security=tls&sni=CxNiMjJz.cAfUnEaR.InFo&type=ws&host=CxNiMjJz.cAfUnEaR.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430英国 
vless://9e769ce1-34be-4e3f-b0a6-823f30eb8f69@199.34.228.174:2096?flow=&encryption=none&security=tls&sni=DrOt0Ai1Oq.DeRaKhT.iNfO&type=ws&host=DrOt0Ai1Oq.DeRaKhT.iNfO&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430摩尔多瓦 
vless://9e769ce1-34be-4e3f-b0a6-823f30eb8f69@208.86.168.74:2096?flow=&encryption=none&security=tls&sni=DrOt0Ai1Oq.DeRaKhT.iNfO&type=ws&host=DrOt0Ai1Oq.DeRaKhT.iNfO&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430摩尔多瓦 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@172.67.205.22:443?flow=&security=tls&sni=1SSdDdFfffHhHJJJJ.20220420.Pp.uA&type=ws&header=none&host=1ssdddffffhhhjjjj.20220420.pp.ua&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjU5LjQyLjI0Ny4xODkiLCJwb3J0Ijo4MDA0LCJzY3kiOiJhdXRvIiwicHMiOiIwNDMw5pel5pysIiwibmV0Ijoid3MiLCJpZCI6IjY0ODQxNTM0LTBlMzItNDUyZS1hMDM4LWM0NDNmZTFmZGVmMCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmJpbmcuY29tIiwicGF0aCI6Ii9ubWtqIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMjkxOSwic2N5IjoiYXV0byIsInBzIjoiMDQzMOmmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImpwMy5nMi5tb29uYmFzZS5saWZlIiwicG9ydCI6MzUyMTMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDml6XmnKwiLCJuZXQiOiJ3cyIsImlkIjoiNDZhNTM5ZDItZDNiYS00YTZlLWFlZGItYjcyN2QyZmM2MGY4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3ZWIueGNqcy5pbmZvIiwicGF0aCI6Ii9ob21lIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://VMhGp5wEIyCDf90T@120.198.100.58:42303?flow=&security=tls&sni=hk06.run.place&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDIzNzUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTkwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MzDpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://075b9690-f1cc-4d0c-aa1e-f80f07f09815@104.21.69.50:443?flow=&security=tls&sni=4o.191292.xyz&type=ws&header=none&host=4o.191292.xyz&path=/w8oHMEEc9tWBZ57XYkE&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpCZ3I2WUJIRW5wZnQ=@178.22.31.239:443#0430奥地利 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@193.108.119.230:8080#0430德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.23.63:989#0430波兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.188.29.80:443#0430美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.163.102:443#0430美国 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@1sdfghjk.890602.xyz:443?flow=&security=tls&sni=1SdfghJk.890602.xyz&type=ws&header=none&host=&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430美国 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@104.21.25.95:443?flow=&security=tls&sni=1sDFgT.890604.FileGear-sG.mE&type=ws&header=none&host=1sdfgt.890604.filegear-sg.me&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430美国 
trojan://7a89ce77-0fcc-4cdc-8838-e1ad2f210f5c@45.82.121.180:56257?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/bOQjQbS8CYRtHb57xL%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.7.2:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.150.203:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
hysteria2://C2XaAk5hqScXOpRiVUuTQKFWKchfFlHyn@45.82.121.180:64178?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=blY2dM7iQpFf14NiCPQEYel9&os=#0430德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xODAiLCJwb3J0Ijo2NTI1Mywic2N5IjoiYXV0byIsInBzIjoiMDQzMOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxMjE0NWVkZS00NjE3LTQ0ZGYtOTM5NS1lYzgzMDUyNWM1OGQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9BbEowRk85eGh0UEV6WEl0djA2UmNZREpBZDZlbz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.202.129:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
hysteria2://vZId18eftYAy9APyZLY2zM3baeffp4v5OAI@45.82.121.180:41566?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=1v4zz4rzymYcICe7Wg&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.160.168:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.252.210:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.210:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.192.183:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzkxNmFkN2ItYjQ2OS00N2RjLTg4ZWYtNTM4MGRkZjRhMmY2QDQ1LjgyLjEyMS4xODA6MjU1OTQ6d3M6L21oQnUlM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.77:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.95.192:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.22.22.57:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.206.167:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@190.93.246.230:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.49.54:443?flow=&encryption=none&security=tls&sni=dash.ckosuz.dpdns.org&type=xhttp&host=dash.ckosuz.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0430德国 

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
