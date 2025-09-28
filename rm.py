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


vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTI36aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwOTI36Iux5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjguaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwOTI35oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDkyN+aWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDkyN+iLseWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDkyN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDkyN+mmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://ac93caa8-fc75-4bc8-bbb9-f09d964b5d69@updatem.faraservice.space:3209?flow=&encryption=none&security=reality&sni=dash.cloudflare.com&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=chrome&pbk=22YtANl_6-2LKrTdIfArHahVa1L0lo86Y8jhHVU-Iis&sid=3679c72c&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927奥地利 
vless://ac93caa8-fc75-4bc8-bbb9-f09d964b5d69@updatem.faraservice.space:3209?flow=&encryption=none&security=reality&sni=dash.cloudflare.com&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=chrome&pbk=22YtANl_6-2LKrTdIfArHahVa1L0lo86Y8jhHVU-Iis&sid=3679c72c&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927奥地利 
hysteria2://TELEGRAM-ID-conf0088.TELEGRAM-ID-conf0088@repuestoslibertad.cl.repuestoslibertad.cl:2084?insecure=0&sni=&alpn=&fp=&obfs=salamander&obfs-password=ed5s8665dsss&mport=&os=#0927德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpVTW1PYVVoam1NcFhGckZmSXFQMkpw@repuestoslibertad.cl.repuestoslibertad.cl:43548?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://hqV2rayNG@pub.hajmalla.com:8000?flow=&encryption=none&security=reality&sni=tgju.org&type=xhttp&host=&path=/HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG---HqV2rayNG&mode=auto&alpn=&fp=chrome&pbk=CuJ44knWuoHEKYL12mVOObNJehc2v0MdpjYuXql7ZSE&sid=&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927韩国 
vless://0ec8c120-33fa-4658-9bed-3a51cb04c55c@net2026cd.zanddynastyofpersia.org:443?flow=&encryption=none&security=tls&sni=net2026cd.zanddynastyofpersia.org&type=ws&host=&path=/eJsVXFVZ6iavNx1EFxOyH861WH&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://b754b53a-aaf5-475c-eeed-46806c2aa63f@kifpool.me:443?flow=&encryption=none&security=tls&sni=nkang2replace.airlineshoma.com&type=ws&host=nkang2replace.airlineshoma.com&path=/&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927瑞典 
vless://0e8a6896-ad90-4a3b-89a3-77d64aa409e2@ilta-wzxrxkdhbjpnprhkkpplsjwawhssvollvxzdhqshiqckwdgrdm.orbnet.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=i2pd.website&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=YVDo7U4O-AT2fa5H9E7hyYHKgfZd1vB6UdbAf2ggWQE&sid=55e6af1a35e64a98&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927以色列 
ss://YWVzLTI1Ni1nY206MTQ4MzcxNDEtNTAwMS00ZDIxLTlhMjUtNTJmZWI5OTY3MzAy@iaplsg.91king.win:21004?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927新加坡 
vless://8da7bd17-70ab-472d-a925-cc827857dc35@hk01.youyacloud.me:28888?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.tvb.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=slSuocOAiBpxoouM2bOV03TG7LRqrGyKDivA__DEric&sid=&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927香港 
vless://e959d53c-91e9-459d-a332-d59ae89b3b4c@hdfynpv2d1.makingirangreatagain.com:443?flow=&encryption=none&security=tls&sni=hdfynpv2d1.makingirangreatagain.com&type=ws&host=&path=/Iyq035lnud9R8ruNNrqGxZZ2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://e959d53c-91e9-459d-a332-d59ae89b3b4c@hdfynpv2d1.farvaharforever.com:443?flow=&encryption=none&security=tls&sni=hdfynpv2d1.farvaharforever.com&type=ws&host=hdfynpv2d1.farvaharforever.com&path=/Iyq035lnud9R8ruNNrqGxZZ2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://b695a9d1-4c91-46a7-adae-09d80a44b6ed@germany2.abolfazl.ru:21262?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
trojan://biOrJGlcfX@creativecommons.org:443?flow=&security=tls&sni=ghasem.kotlet.org&type=ws&header=none&host=ghasem.kotlet.org&path=/kos-madaret-khamneii&alpn=h2%2Chttp/1.1&fp=firefox&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImMzLUJiNTgwNDc2LTRBOTEtNmY3Ri1FZUI2LTJlMmNhYzRCNjkxRS4xMzEuUHAuVUEiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA5Mjfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYzI2MzM1NjAtNWFjYi00ZGQzLTljMjItOWE2YzJmZDIxMmUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJDMy1iQjU4MDQ3Ni00QTkxLTZmN2YtZUViNi0yRTJjQUM0YjY5MUUuMTMxLnBwLnVBIiwicGF0aCI6Ii8ydVJzTTRaNFk4TzVPc2JKa0EiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJDMy1iQjU4MDQ3Ni00QTkxLTZmN2YtZUViNi0yRTJjQUM0YjY5MUUuMTMxLnBwLnVBIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://8496c102-4094-4dd3-ad63-7bb7a35cbaee@94.182.137.12:20532?flow=&encryption=none&security=&sni=&type=tcp&host=Telewebion.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://90cd2100-044d-49fa-b82c-49ef09d60e88@94.131.107.201:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=anydesk.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=rwXlON1aDW3CM1wfNYMWb-hpPYqvH0kHHOBDatkuCSE&sid=26a70553&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927荷兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://d81c7a1c-6292-47c0-cc37-0823c8fc6b94@91.208.109.55:59079?flow=xtls-rprx-vision&encryption=none&security=tls&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@89.116.180.248:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjczRTQyMDE5LWM4MjAtQTY2YS0wMTFFLWYxMTkzNzIzMmVjMS44OTg5MDYwNC5YWXoiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA5Mjfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYzI2MzM1NjAtNWFjYi00ZGQzLTljMjItOWE2YzJmZDIxMmUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI3M2U0MjAxOS1DODIwLUE2NkEtMDExRS1mMTE5MzcyMzJFQzEuODk4OTA2MDQueFlaIiwicGF0aCI6Ii8ydVJzTTRaNFk4TzVPc2JKa0EiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiI3M2U0MjAxOS1DODIwLUE2NkEtMDExRS1mMTE5MzcyMzJFQzEuODk4OTA2MDQueFlaIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://tunnel-astrovpn_official019@69.42.222.177:8441?flow=&security=tls&sni=zula.ir.AstroVPN-official.AstroVPN-official.workers.dev.AstroVPN_Official.org.AstroVPN.com.AstroVPN_Official.xyz.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.AstroVPN_Official.monster.AstroVPN_OfficialJoinTelegram-------------AstroVPN_Official----------Join.ir&type=tcp&header=none&host=69.42.222.177&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
trojan://telegram-id-privatevpns@63.180.56.18:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
trojan://telegram-id-directvpn@63.180.56.18:22223?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
trojan://telegram-id-privatevpns@63.178.137.4:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://4981b98f-4943-4083-83aa-00b028f57a18@57.129.92.155:36626?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://bb5be5c2-bf5e-4050-8193-eb18f1faa42e@51.210.77.32:24292?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
hysteria2://2b67ONZROv%2BfRVMxB94BSw%3D%3D@5.231.70.79:443?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0927德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.81.58.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@31.43.179.38:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927韩国 
vless://53fff6cc-b4ec-43e8-ade5-e0c42972fc33@193.151.135.21:44443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.speedtest.net&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=XHjKkrNBYXOaamOx8IUCrwX0zp5dAQRVErHiQ5bwAEQ&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927希腊 
hysteria2://8864aa9f-7517-4fd5-aef1-32050eb3095d@185.92.220.240:30205?insecure=1&sni=net2025.afsharidempire.uk&alpn=&fp=&obfs=salamander&obfs-password=GdQ4bgvT8RFwuWi2&mport=&os=#0927荷兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@184.174.80.250:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://192ea2c7-d7d0-6676-2929-b04a072b387d@178.20.215.2:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=speed.cloudflare.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=GfTzhy59k9CXlAdF819OUVeBdrqIILaDIWa1bddjGnA&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927塞舌尔 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi44Mi42NS43NyIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDkyN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiIxZWNjN2U2MS1kNjM5LTRlMTgtOGNhZS0yY2ZmOWU3ODcyNjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Im0xNi05ZDg2ZGMxNS03ZDUxLTcxMzgtYmVlNS02NDVlMGVmNzkzNmMuaHVhbmdzaGFuZy5wcC51YSIsInBhdGgiOiIvWlZyYzdNR1pjS3pZRTQwc0Y5WjUiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJtMTYtOWQ4NmRjMTUtN2Q1MS03MTM4LWJlZTUtNjQ1ZTBlZjc5MzZjLmh1YW5nc2hhbmcucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://9b3d65ab-576c-4750-9cb3-bb41c12c085e@172.245.251.10:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.ieee.org&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=XgQPLMVHvbUKTzcAZPBDGZ_mDhaZRiAJEk7c4-7UzR4&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@164.38.155.97:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://dfc84ee3-ec04-4635-84e1-7c4c22e77c7b@159.65.186.184:20096?flow=&encryption=none&security=reality&sni=cloudflare.com&type=xhttp&host=&path=/&mode=auto&alpn=&fp=chrome&pbk=jyX-pjSN3o_LphKC_496D45TtUf6zH50A0GLgxu-t3c&sid=f7&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://87664dc2-1ee0-4452-9895-bdeff5a9818d@159.223.38.173:443?flow=&encryption=none&security=tls&sni=zula.ir&type=ws&host=&path=/ws&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927新加坡 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.62.168:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927韩国 
vless://401374e6-df77-41fb-f638-dad8184f175b@154.83.2.167:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://3e7f67de-648e-4871-b51a-a225214d41ee@147.45.51.160:443?flow=&encryption=none&security=reality&sni=api.company-target.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=TRP10HqKUXEQ3O-cfsq93DycfBmbJe9KM36yvSa8Mmw&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927意大利 
vless://2715b5fc-a3a8-49dd-8c10-55f18f3030c5@141.94.213.115:25365?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://fae6aee4-70ee-4416-b9ee-22d957262ef4@141.227.142.158:47462?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://6f93e5b7-2188-45ac-91e3-71e8909c225e@141.227.140.168:45946?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://bbb7af93-94f1-4ad7-8a4d-2b674bea8922@135.125.88.66:37612?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927法国 
vless://2bcae70e-cfd5-4f56-a6f7-0b6e51a90211@109.122.197.72:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=ya.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=UpO0lV2YR0otf1jQKLHDp2bD623tyUIefqCLGm04a2Q&sid=b2cb507156722e6e&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
trojan://2fd0d127-266d-4d0b-b453-f94659a132fc@106.75.134.1:12000?flow=&security=tls&sni=aliyun.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927香港 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.26.2.186:443?flow=&encryption=none&security=tls&sni=pqh31v7.hiddendom.shop&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://97fc44dd-c88c-4470-8d66-1752089c0183@104.16.53.11:2053?flow=&encryption=none&security=tls&sni=frAgeU2.cpI2HIdd.eu.ORG&type=ws&host=&path=/&headerType=none&alpn=h2%2Chttp/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927荷兰 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.28:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.64:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0927越南 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927美国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@141.101.113.112:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@190.93.246.121:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.19.192.183:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@108.162.196.116:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@162.159.7.2:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@188.114.99.92:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@162.159.245.40:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@108.162.192.139:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4zOSIsInBvcnQiOjQxMjA3LCJzY3kiOiJhdXRvIiwicHMiOiIwOTI35b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjU0M2Q4YTNlLWI5ODAtNGU2OC1iNmJiLTJiODZlOWUwY2Y1MSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYXBpLm5hbWFzaGEuY28iLCJwYXRoIjoiL2VMP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.18.108.128:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@162.159.240.77:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
hysteria2://4vlmCZChrOL57g6RKrzkGetIxvh829d@45.82.121.39:34572?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=2YsvJ9OthUQUE0YQby&mport=&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@190.93.244.134:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
anytls://heZTqh6EYzjd0brRTZUjJgRXAUj@45.82.121.39:18855?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.23.98.214:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@190.93.246.240:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
hysteria2://Rvzl6puD00lbe6w4o7bsUv0S2Krqy70Fda@45.82.121.39:20117?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=gE2lBK4vHXlqzj326aXXoy1cy8i&mport=&os=#0927德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.58.119:443?flow=&encryption=none&security=tls&sni=www.cjowefs.qzz.io&type=xhttp&host=www.cjowefs.qzz.io&path=/ZETj2YLh24mig7%3F8bf6bb4a-1374-445f-9a51-3434f820c136&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
trojan://7795bea8-7fab-4f98-aed1-02b6b511019d@45.82.121.39:6004?flow=&security=tls&sni=api.namasha.co&type=ws&header=none&host=api.namasha.co&path=/gw7ZTAY94hhSa1s01AFZK%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0927德国 
hysteria2://P8DO7e2JNAFd4FVP@45.82.121.39:22610?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=3Bcf359LaoEGTy9SC5gCq84BzMjqIndwIjC&mport=&os=#0927德国 
anytls://Q8KSvtSDDnhxd1IJLjUshGB5YbEswA@45.82.121.39:6631?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0927德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YTU2YmJlNGEtYzA4NS00ZjVmLWJmNzMtZmVhNDVhNjljNzcyQDQ1LjgyLjEyMS4zOTo1MjcwOndzOi9HQUM3WHdNazdJMCUzRmVkJTNEMjU2MDphcGkubmFtYXNoYS5jbzpub25lOnRsczphcGkubmFtYXNoYS5jbzpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0927德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NDlmYjgzOGEtOWMxYi00OTcxLWE1NmYtNzYyOWM4MDA0YzE2QDQ1LjgyLjEyMS4zOTo0NzQwNzp3czovR1VXJTNGZWQlM0QyNTYwOmFwaS5uYW1hc2hhLmNvOm5vbmU6dGxzOmFwaS5uYW1hc2hhLmNvOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0927德国 
anytls://TaI9TciLo9AWRqPoDS40baO2Kq9z6@45.82.121.39:17696?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0927德国 
hysteria2://u7NlBONSiAu3rizPiNCHX@45.82.121.39:57598?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=TuKGVrpGQcrPJmdMaSFh46UmWMsHNg9nGlk&mport=&os=#0927德国 



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
