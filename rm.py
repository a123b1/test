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

vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.183.154:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@103.163.218.2:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814越南 
vless://8df60790-c903-4661-b85d-64c0009378e5@104.19.99.250:443?flow=&encryption=none&security=tls&sni=F1.paRsa.fiLegEar-Sg.Me&type=ws&host=f1.parsa.filegear-sg.me&path=/%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814加拿大 
vless://07a3df8f-2a2c-42f8-ad92-65889d90f3bf@104.21.26.17:443?flow=&encryption=none&security=tls&sni=tTTtTTT67.459.PP.uA&type=ws&host=ttttttt67.459.pp.ua&path=/5UW2C42lpZ7Dj4VDwVOkZfoq&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@104.21.3.219:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0LjEwMi4yMjkuMTUiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwODE0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImY4YjZjOGE0LTU2MzMtMzE1OC05YzBlLTc3NTE4ZTNmYzM1NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczQuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkmVGVsZWdyYW3wn4eo8J+Hs0BXYW5nQ2FpMi8/ZWQ9MjU2MCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://YWVzLTI1Ni1nY206aVVCMDkyM1JCQQ==@154.3.8.151:30067?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814香港 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://357b1bba-6400-4944-baff-1b933311ff28@162.159.129.11:443?flow=&encryption=none&security=tls&sni=SsSSSSSsSSSD.890606.Xyz&type=ws&host=SsSSSSSsSSSD.890606.Xyz&path=/kSIHD28dr9nkaMBYIsgt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@172.67.153.156:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.157.220:443?flow=&encryption=none&security=tls&sni=XXCsDERT6.777159.XyZ&type=ws&host=xxcsdert6.777159.xyz&path=/O9jlBCbIm3xr1D40NK&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814希腊 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@193.108.119.230:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.165.233.93:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814巴拉圭 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.54.57.90:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814巴西 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0Ni4yMDEuMTUiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwODE0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImY4YjZjOGE0LTU2MzMtMzE1OC05YzBlLTc3NTE4ZTNmYzM1NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczQuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkmVGVsZWdyYW3wn4eo8J+Hs0BXYW5nQ2FpMi8/ZWQ9MjU2MCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IlRHLldhbmdDYWkyLnM0LmRiLWxpbmswMi50b3AiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE5NC41My4xNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZjhiNmM4YTQtNTYzMy0zMTU4LTljMGUtNzc1MThlM2ZjMzU2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiVEcuV2FuZ0NhaTIuczQuZGItbGluazAyLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE5NC41My4xNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZjhiNmM4YTQtNTYzMy0zMTU4LTljMGUtNzc1MThlM2ZjMzU2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI5LjM0LjIwNSIsInBvcnQiOjU5OTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwODE05rOV5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYTBjOTkzNy01OGE2LTQ0ZWEtOTExMS1hNmFiYWMyNjdkMGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI5LjM0LjIwNSIsInBvcnQiOjU5OTU2LCJzY3kiOiJhdXRvIiwicHMiOiIwODE05rOV5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYTBjOTkzNy01OGE2LTQ0ZWEtOTExMS1hNmFiYWMyNjdkMGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.17.169:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTptU1FpdVQ1alIxN255V2djWE9QclRX@77.105.166.12:8594?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814英国 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg4LjIxNi42OS4xNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZjhiNmM4YTQtNTYzMy0zMTU4LTljMGUtNzc1MThlM2ZjMzU2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814斯洛文尼亚共和国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12024?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12028?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12014?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814日本 
vmess://eyJ2IjoiMiIsImFkZCI6ImNjMmRhc2guODkwNjAwMDQueHl6IiwicG9ydCI6MjA4Mywic2N5IjoiYXV0byIsInBzIjoiMDgxNOWKoOaLv+WkpyIsIm5ldCI6IndzIiwiaWQiOiIyZmMzNzcxMy0zMDE3LTQ5N2UtZmYyZC05NjVmODI2YTE5YTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNjMmQzLjg5MDYwMDA0Lnh5eiIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImNsb3VkZ2V0c2VydmljZS5tY2xvdWRzZXJ2aWNlLnNpdGUiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiMzdmNDY0Y2ItYjgyNi00Mjc4LTliZjgtMTFiZGYxZWM4OTJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJGcmEtVnAtMTIzLkJMYVpFQ0xPVUQuU2l0ZSIsInBhdGgiOiIvbGludmt3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IkZyYS1WcC0xMjMuQkxhWkVDTE9VRC5TaXRlIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImNzZ28uY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYTEzNGUzZGUtYjI1YS00MDIwLTk5OTgtMDVmYTZiNzE1ZjFhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjZG4tbm9kZS1vc3MtOTkucGFvZnUuZGUiLCJwYXRoIjoiL3Byb2ZpbGUvdGVsZWdyYW1Ac3Nyc3ViIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://7a80a8d9-92f9-4f0a-8352-9005a8215ab8@fonts.net:443?flow=&encryption=none&security=tls&sni=rAyan-uS-2.MediCaLhIsToRy.iR&type=ws&host=rAyan-uS-2.MediCaLhIsToRy.iR&path=/%40rayan_config&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImhrdC5nb3RvY2hpbmF0b3duLm5ldCIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwODE06aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImFkYmQwYTgyLTMzMzYtMTFlZC1iZDdjLWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814韩国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p222.panda001.net:15098?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InNqMy42MjA3MjAueHl6IiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDgxNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI1MTZkOGE3YS0zZjBiLTQxZDMtYmFkMC0yNDYxMTYzODE1MTYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InNqMy42MjA3MjAueHl6IiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ssr://c3NjYS5pcnVuZG5zLm5ldDo0NDM6YXV0aF9hZXMxMjhfbWQ1OmFlcy0xMjgtY2ZiOmh0dHBfcG9zdDpKQ1JVZFhKaU1GWlFUaVFrLz9vYmZzcGFyYW09JnByb3RvcGFyYW09JnJlbWFya3M9TURneE5PV0tvT2FMditXa3B3PT0mb3M9 
vmess://eyJ2IjoiMiIsImFkZCI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MTTnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNDE3NGI5NWQtMTE1ZS00ZDM5LWFkZDYtMWY4ZGI5NWJiODYwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc3Nzc3NzeHh4eC4yMDMyLnBwLnVhIiwicGF0aCI6Ii82V2UzVTlEZjFXR3hnRm5vRlB3MSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo5dHFoTWRJclRrZ1E0NlB2aHlBdE1I@switcher-nick-croquet.freesocks.work:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0814英国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDgxNOmmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDgxNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDgxNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDgxNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDgxNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDgxNOa+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDgxNOaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwODE0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwODE05oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.25.225.87:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0IjozNjY3Niwic2N5IjoiYXV0byIsInBzIjoiMDgxNOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwZmI0NzMzZC05NzRlLTQ1N2UtOGJkYi05N2ZkNjNiMjdjNTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9RP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://1cff427d-1035-4ebd-b153-7246c94a6d25@45.82.122.236:40456?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/qHAQ2R%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.25.97.141:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.20.251.171:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
trojan://6a7d7c7a-b584-4403-a0c4-41f286ddc06a@45.82.122.236:43233?flow=&security=tls&sni=api.namasha.co&type=ws&header=none&host=api.namasha.co&path=/477emub7L14I4%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.20.51.130:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@190.93.245.63:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@103.21.244.235:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0IjoxOTU0OSwic2N5IjoiYXV0byIsInBzIjoiMDgxNOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI5YjA4MzJmYy05ZTI4LTRmZjktYmM0OS00ODljY2ZhMTA1NWMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9WNFdjcllHSmlKeVljP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@188.114.96.253:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@198.41.215.192:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@103.21.244.86:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
anytls://NOfJkQsa93nkchQXHUK8Vo9Z19IHxuRm@45.82.122.236:11862?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0814德国 
vless://7817e21e-81cd-4cbc-a0df-cdce11f6ccd6@45.82.122.236:29032?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/Zr2RkbGvIziHnxjZEo5xv%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
hysteria2://0lZ5XRSaI17dovJZ2pogfI@45.82.122.236:46782?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=KJccTYZVdY6WO9j9ueUwJ4mzCBShS8svq&mport=&os=#0814德国 
anytls://yMsQYIHRhAgOisH8CGdOzyaIq8b14YgqrL7@45.82.122.236:61279?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0814德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0Ijo1ODAzMywic2N5IjoiYXV0byIsInBzIjoiMDgxNOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI1ZmM3NzQ2MC1iNjBjLTQ2YTktOGFhZi1mMGI5Njk1MTZmODAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9pR3U2WWdNcWVKSWRWaTl6YXlZSnJBcVNHdno4YWhoP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://wy5lyoz5SGwI2LSNkk67paz0W@45.82.122.236:63440?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=R9qGBHIeElbZoKamlbg&mport=&os=#0814德国 
hysteria2://klvkocX4I6a0gujR2K4rajalieHgsRNwj7b@45.82.122.236:9485?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=7HJ2jC5nMib7XL0Wi25pCyOmOXOmbMpNe9Sn0p8&mport=&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.20.31.41:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@104.27.3.204:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://e7abc9e1-1746-4a15-b41c-ecc5df6e78d7@198.41.196.128:443?flow=&encryption=none&security=tls&sni=ru.ryalol.qzz.io&type=xhttp&host=ru.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 
vless://90cae3a4-b5bb-408e-b79c-3b5c074f8a25@45.82.122.236:61556?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/hdjfp24cV81Ee0NHiH2UTNQnM%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0814德国 

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
