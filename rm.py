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


vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTE56aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwOTE56Iux5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjguaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwOTE55oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDkxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://d378d3d0-c521-4874-a6f3-21794398cf9c@test.barayekhudam.ir:59697?flow=&encryption=none&security=reality&sni=bimeh.com&type=xhttp&host=Join---i10VPN---Join---i10VPN---Join---i10VPN---Join---i10VPN&path=/&mode=auto&alpn=&fp=chrome&pbk=HDE3ZT4rZPr6RIpgLK6dn6FGvolXLJtwJEeDEC4N1Eg&sid=c5a5b0&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0919瑞典 
ssr://c3NjYS5pcnVuZG5zLm5ldDo0NDM6YXV0aF9hZXMxMjhfbWQ1OmFlcy0xMjgtY2ZiOmh0dHBfcG9zdDpKQ1JVZFhKaU1GWlFUaVFrLz9vYmZzcGFyYW09JnByb3RvcGFyYW09JnJlbWFya3M9TURreE9lV0tvT2FMditXa3B3PT0mb3M9 
vmess://eyJ2IjoiMiIsImFkZCI6InNlcmthdC5vcmciLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA5MTnlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMDNmY2M2MTgtYjkzZC02Nzk2LTZhZWQtOGEzOGM5NzVkNTgxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoxLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoibGlua3Z3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://e3847ec6-b2fc-4eb2-b919-174d986f882c@poland20.clearorbitllc.com:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=poland20.clearorbitllc.com&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=oNYCpjXjcYAV9qSWBt95N9dDUPhc_QnauJZ3kSJVeSQ&sid=2a22&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919波兰 
vless://e3847ec6-b2fc-4eb2-b919-174d986f882c@poland20.clearorbitllc.com:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=poland20.clearorbitllc.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=oNYCpjXjcYAV9qSWBt95N9dDUPhc_QnauJZ3kSJVeSQ&sid=2a22&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0919波兰 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919韩国 
vless://f9f1ed42-9943-4121-9408-8fbe766343ae@m5a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://aac5267c-93e1-44d2-97a0-be936b98690a@m48a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://b9793e0b-b030-4ac6-a503-8f2081d1cada@m47a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://39c8e0d3-c932-4ff7-b3e3-83002647907b@m44a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://bbef1e1b-4061-45ce-a6e0-4cec2fe38cc4@m41a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://d36f457f-17a9-4891-a113-322ec6792917@m24a.vip784.com:33801?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.ir&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://b754b53a-aaf5-475c-eeed-46806c2aa63f@kifpool.me:443?flow=&encryption=none&security=tls&sni=nkang2replace.airlineshoma.com&type=ws&host=nkang2replace.airlineshoma.com&path=/&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919瑞典 
vless://0e8a6896-ad90-4a3b-89a3-77d64aa409e2@ilta-wzxrxkdhbjpnprhkkpplsjwawhssvollvxzdhqshiqckwdgrdm.orbnet.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=i2pd.website&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=YVDo7U4O-AT2fa5H9E7hyYHKgfZd1vB6UdbAf2ggWQE&sid=55e6af1a35e64a98&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919以色列 
vless://8da7bd17-70ab-472d-a925-cc827857dc35@hk01.youyacloud.me:28888?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.tvb.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=slSuocOAiBpxoouM2bOV03TG7LRqrGyKDivA__DEric&sid=&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0919香港 
vless://cfa392db-7445-4aa6-964f-2a3e20103936@99.199.60.164:56565?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.samsung.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=59iI-5g0yQ3r6ZaoBOQSWOCnMw6_t_q0oS4gXngXhW0&sid=2e3b0488&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919加拿大 
vless://1a6fe500-59da-4598-8576-256f06765ffb@94.26.228.10:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=ru.sfasti.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=J_jQq9-SWQZjiMhuPaFV7V2MaJ4pkKgVRaz7x6tmvy8&sid=16895459a2c7768d&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919荷兰 
vless://8496c102-4094-4dd3-ad63-7bb7a35cbaee@94.182.137.12:20532?flow=&encryption=none&security=&sni=&type=tcp&host=Telewebion.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://c01c0c92-b2d1-44b1-a5e5-2f8a94e57008@91.99.58.127:2090?flow=&encryption=none&security=reality&sni=refersion.com&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=lQbgwNDYw6Zbjdim0JtXUarzb-3GSjDvtX6FJYZD9Qo&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://88a5a796-6669-424f-9048-4fe269468372@91.98.165.163:57276?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=FAST78_CHANNEL-TEL--FAST78_CHANNEL-TEL--FAST78_CHANNEL-TEL--FAST78_CHANNEL-JOIN-FAST78_CHANNEL-TEL--FAST78_CHANNEL-JOIN-FAST78_CHANNEL-TEL-FAST78_CHANNEL-TEL--FAST78_CHANNEL-JOIN-FAST78_CHANNEL-TEL--FAST78_CHANNEL&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919斯洛文尼亚共和国 
vless://4a0e3cf3-4a10-4a38-bba4-b17b592a0d2b@89.44.242.222:29495?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919爱尔兰 
vless://888a20e2-fc3f-4f52-973c-36a6386225b8@89.44.242.222:29500?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919爱尔兰 
vless://44aded6c-a012-452b-8e13-04d5f15a659f@89.44.242.222:46822?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919爱尔兰 
vless://6035325d-399a-5148-9126-29cedfd5966a@88.151.192.52:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=Cb6bPG7NAEde5yU3KChBcx_iF3n7UHakfvi6aWT0ezY&sid=dcaebc34&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919乌克兰 
vless://2ecc1c66-0808-174c-e51a-5274c1428b3c@85.133.206.49:48008?flow=&encryption=none&security=&sni=&type=tcp&host=myket.ir&path=&headerType=http&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ssr://NjIuMTAwLjIwNS40ODo5ODk6b3JpZ2luOmFlcy0yNTYtY2ZiOnBsYWluOlpqaG1OMkZEZW1OUVMySnpSamh3TXc9PS8/b2Jmc3BhcmFtPSZwcm90b3BhcmFtPSZyZW1hcmtzPU1Ea3hPZWlMc2VXYnZRPT0mb3M9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919英国 
vless://417dab4b-f2e0-4baf-94d0-6bfbcb1e43a8@51.91.139.99:34309?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://f924939e-2d9a-46b7-a3c2-67a225b7c027@51.89.2.113:8081?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=nT4JZTeUVOw-XZ-htdqbFi1je4ZHeg-ALICrDk2usFE&sid=d19d7a2d3da8595a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919英国 
vless://6ce3bb2b-bff1-431f-bb46-f492bf6a5b35@51.178.253.42:27185?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://6035325d-399a-5148-9126-29cedfd5966a@51.158.205.183:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=OHDOdOV5Zdi-bSFlXCstXXdunYLtxZ-6quyX0bA6MFQ&sid=8aa41f71&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919荷兰 
vless://9d0a75d2-f747-4afa-b43f-d208af9e8f9a@500770.xyz:34074?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.ucla.edu&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=zimSAAs4SyUKAR-MTMaw08PuI7skyi1U5Peb6VGJwjY&sid=061cca24&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ3Ljc5LjQyLjIyNiIsInBvcnQiOjU3NDY5LCJzY3kiOiJhdXRvIiwicHMiOiIwOTE55pel5pysIiwibmV0Ijoia2NwIiwiaWQiOiIzNWZlYWQ2ZC0zMWVlLTQwYTAtOTk5Yi05MjkzYzkzN2QxMjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiJCSXY0M1FpbWplIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://6035325d-399a-5148-9126-29cedfd5966a@46.29.234.115:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=XwdE6RvcykBQPGDye7izprpanSk6YrTX2cQqunFz9Gw&sid=ec999ef7&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919立陶宛 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@46.183.184.60:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919克罗地亚共和国 
vless://bb77271b-a88c-431f-b7be-358d13f29574@46.101.87.178:443?flow=&encryption=none&security=tls&sni=zula.ir&type=ws&host=&path=/ws&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919英国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.81.58.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://e0042666-497b-4fde-bf4a-c5281df24d15@45.130.214.192:20992?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919拉脱维亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.54.57.90:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919巴西 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.165.233.93:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919巴拉圭 
vless://401374e6-df77-41fb-f638-dad8184f175b@31.43.179.38:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919韩国 
vless://895a39fb-6c32-49af-b04d-efecc1f6c5fb@206.189.135.13:41856?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919印度 
vless://6baf31c3-a32e-46b6-943d-e71500c68004@206.189.106.37:443?flow=&encryption=none&security=tls&sni=zula.ir&type=ws&host=&path=/ws&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919荷兰 
vless://6035325d-399a-5148-9126-29cedfd5966a@194.58.66.234:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=l8CueSIvv8QqvxehXPrpd_8OEGI9xMbX0ZRtXG-DqCA&sid=4ff781da&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919希腊 
vless://0abf9050-c7be-464d-80af-24094c2b97de@188.68.53.100:6666?flow=&encryption=none&security=reality&sni=Tgju.org&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=S_2bepGaT7EHeH5DdyEgio421RTgrAvvOOQiaq8zV0g&sid=b525ecd2fc&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://6035325d-399a-5148-9126-29cedfd5966a@185.39.207.121:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=Mjz6Gz75xTMe9ZU08h0y-A_VgRQ6tnt3qoOzdEn1k1M&sid=0fa84b90&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919希腊 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.213.23.226:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919挪威 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.135.9.144:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
hysteria2://c6e02cd8-ce11-40f0-afeb-e2c412b6cc3a@185.126.255.78:41749?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0919乌克兰 
vless://6035325d-399a-5148-9126-29cedfd5966a@185.105.111.50:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=outlook.office.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=WtKTSZd2ujSiy4M42WgwrSp3flODoh2eHpasVWnySSE&sid=8074a7f8&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919俄罗斯 
vless://401374e6-df77-41fb-f638-dad8184f175b@184.174.80.250:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://192ea2c7-d7d0-6676-2929-b04a072b387d@178.20.215.2:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=speed.cloudflare.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=GfTzhy59k9CXlAdF819OUVeBdrqIILaDIWa1bddjGnA&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919塞舌尔 
hysteria2://af4c517e-6a06-441a-b560-6662aa446f4c@172.252.236.213:57588?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0919瑞士 
hysteria2://c6e02cd8-ce11-40f0-afeb-e2c412b6cc3a@172.252.236.213:57588?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0919法国 
vless://9b3d65ab-576c-4750-9cb3-bb41c12c085e@172.245.251.10:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.ieee.org&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=XgQPLMVHvbUKTzcAZPBDGZ_mDhaZRiAJEk7c4-7UzR4&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@171.22.254.17:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919马耳他 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@156.146.40.194:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919斯洛伐克 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.63.177:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919韩国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.62.168:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919韩国 
vless://401374e6-df77-41fb-f638-dad8184f175b@154.83.2.167:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919美国 
ssr://MTUwLjEwNy40Ni4yMTo4MDgzOm9yaWdpbjphZXMtMjU2LWNmYjp0bHMxLjJfdGlja2V0X2F1dGg6YVVaeGJucFRjMk5PLz9vYmZzcGFyYW09JnByb3RvcGFyYW09JnJlbWFya3M9TURreE9lbW1tZWE0cnc9PSZvcz0= 
vless://2715b5fc-a3a8-49dd-8c10-55f18f3030c5@141.94.213.115:25365?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://24244970-2b14-47e6-b0c1-95cecc9bcc3c@141.227.174.30:32657?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://de332b56-8cae-4cf7-92a1-19e9f5647ce0@141.227.172.235:57249?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://f894d5ed-530d-4f9f-ab7d-468bf8ac5dda@141.227.170.186:34024?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://a1015799-6c9a-4bab-8ad0-8c9444d46fa0@141.227.166.22:11230?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919法国 
vless://2429bee3-e0c1-47dd-b420-75e6512b184b@140.238.147.101:42557?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=LiHpb4jWrgHBSpi1mjKH3I8m2ahpVNexeNDh-sMW3Xo&sid=f430927d&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919加拿大 
vless://976191fd-e929-467e-98b4-1349f58907d5@139.59.46.188:37548?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919印度 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.61.188.86:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919瑞典 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.28:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.20:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.64:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.26:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0919越南 
vless://dbfd9260-1bf5-49bd-ae4a-d6aeba30ebdc@45.82.122.139:40760?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/DBkEnDlHMx2RruYE4WECOa5Dt9iBG3%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@188.114.98.202:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.29.71:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
anytls://Z5QoQlPBUu342BdxdPswrfnji@45.82.122.139:14022?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.87.206:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWYxZjZmYjMtMzRkYy00M2JjLTkzNTAtYTI4OTlhZDc0OWQ3QDQ1LjgyLjEyMi4xMzk6NTEyNDg6d3M6L0szRWtHZHFSOXRvdzlmTExBV0k2S1QlM0ZlZCUzRDI1NjA6d3d3LnlhaG9vLmNvbTpub25lOnRsczp3d3cueWFob28uY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.25.202.125:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@198.41.196.174:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.21.115.63:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.65.243:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@198.41.192.217:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.59.126:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
trojan://5f1f6fb3-34dc-43bc-9350-a2899ad749d7@45.82.122.139:37022?flow=&security=tls&sni=www.yahoo.com&type=ws&header=none&host=www.yahoo.com&path=/f3SueE%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.25.194.251:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4xMzkiLCJwb3J0Ijo1MzY4LCJzY3kiOiJhdXRvIiwicHMiOiIwOTE55b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjgwMGFkY2MyLTUzNGUtNGUzNS1iOWQ4LWU1ZGZhMGJiMzAxNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LnlhaG9vLmNvbSIsInBhdGgiOiIvelNOUlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy55YWhvby5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.27.86:443?flow=&encryption=none&security=tls&sni=vm.msxoa.dpdns.org&type=xhttp&host=vm.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3FvLwyOm3246wCyY6NIhOmdC4mh3wiw&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0919德国 
hysteria2://Soc32ZJ2WzinalajczhQseLpU@45.82.122.139:20060?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=lYaf3roZ0GfFR7b4C6884xdf5nL4TP5u2hNmE&mport=&os=#0919德国 
hysteria2://ScTd57PB6yeVju78XIFh8yl9IZWOLVJ3Gp@45.82.122.139:52371?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=0sQk4h7vV7MaOg29gseoHOJcTbMQlO6k5G&mport=&os=#0919德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4xMzkiLCJwb3J0Ijo1NjYwOSwic2N5IjoiYXV0byIsInBzIjoiMDkxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlMTA3NjFmZS1jNjM4LTQyNDEtYWRiMy0yZGIwY2JhMmZlZTQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55YWhvby5jb20iLCJwYXRoIjoiLzZmcGNlSTBHeDBWNkd2Qlo/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy55YWhvby5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
    
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
