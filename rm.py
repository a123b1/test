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


vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
trojan://ttfang@103.116.7.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821荷兰 
trojan://ttfang@103.169.142.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821 
vless://8df60790-c903-4661-b85d-64c0009378e5@104.19.99.250:443?flow=&encryption=none&security=tls&sni=F1.paRsa.fiLegEar-Sg.Me&type=ws&host=f1.parsa.filegear-sg.me&path=/%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821加拿大 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@104.21.3.219:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://376734bc-4db8-4317-b451-af0262cb01c7@104.21.75.120:2087?flow=&encryption=none&security=tls&sni=InvInciBLe.FAFa20.sHop&type=ws&host=invincible.fafa20.shop&path=/&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.26.2.186:443?flow=&encryption=none&security=tls&sni=pqh31v7.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://357b1bba-6400-4944-baff-1b933311ff28@162.159.129.11:443?flow=&encryption=none&security=tls&sni=SsSSSSSsSSSD.890606.Xyz&type=ws&host=SsSSSSSsSSSD.890606.Xyz&path=/kSIHD28dr9nkaMBYIsgt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@172.67.153.156:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.157.220:443?flow=&encryption=none&security=tls&sni=XXCsDERT6.777159.XyZ&type=ws&host=xxcsdert6.777159.xyz&path=/O9jlBCbIm3xr1D40NK&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@176.34.150.214:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821爱尔兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821波兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
trojan://ttfang@45.12.31.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821 
hysteria2://nfsn666@45.207.222.138:8888?insecure=1&sni=hk.nfsn666.gq&alpn=&fp=&mport=&os=#0821香港 
trojan://ttfang@45.40.152.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
trojan://ttfang@45.85.118.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@46.183.184.60:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821克罗地亚共和国 
trojan://ttfang@66.81.247.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
trojan://ttfang@72.167.25.216:2096?flow=&security=tls&sni=ttfang.fange.me&type=ws&header=none&host=ttfang.fange.me&path=Telegram%F0%9F%87%A8%F0%9F%87%B3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821斯洛文尼亚共和国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=http/1.1%2Ch2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12014?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821日本 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12028?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImNmLmZvdmkudGsiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MjHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYmY2NzQzN2UtNmM5MC00NWNhLWFiYzItYzcyNDBhNWNlMmFhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJmb3hsdXguZm92aS50ayIsInBhdGgiOiIvZWlzYXNxYSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://f2fdcc30-a0c1-434d-94a7-dc8fc2c11a45@cloudflare.182682.xyz:2086?flow=&encryption=none&security=&sni=&type=ws&host=free.naichachong.top&path=/TG%40naichachong&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImNsb3VkZ2V0c2VydmljZS5tY2xvdWRzZXJ2aWNlLnNpdGUiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MjHms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiMzdmNDY0Y2ItYjgyNi00Mjc4LTliZjgtMTFiZGYxZWM4OTJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJGcmEtVnAtMTIzLkJMYVpFQ0xPVUQuU2l0ZSIsInBhdGgiOiIvbGludmt3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IkZyYS1WcC0xMjMuQkxhWkVDTE9VRC5TaXRlIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImRkZHZ2Ym4uOTMxLnBwLnVhIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwODIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjQxNzRiOTVkLTExNWUtNGQzOS1hZGQ2LTFmOGRiOTViYjg2MCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZGRkdnZibi45MzEucHAudWEiLCJwYXRoIjoiLzZXZTNVOURmMVdHeGdGbm9GUHcxIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImdnZ2dnZ2dnZ2dnZ2dnLjIyMjc2OS54eXoiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDgyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiIyZTY1NTc3ZS04ZmRiLTRiYjEtYTQ5NS05NmYzMTIyMDk5YTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImdnZ2dnZ2dnZ2dnZ2dnLjIyMjc2OS54eXoiLCJwYXRoIjoiL2Y2dGFPTWNPU1piOVRQUiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTEyOC1nY206NmIxZTU0NzUtNzY2MS00OTIxLWFhMjYtZDExNzU4YjJmM2Yx@hanguo01.tmdns-sing.top:13882?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821韩国 
ss://YWVzLTEyOC1nY206NmIxZTU0NzUtNzY2MS00OTIxLWFhMjYtZDExNzU4YjJmM2Yx@hk1-20250813213806be3c17japantm01.tmdns-sing.top:13872?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821香港 
ss://YWVzLTEyOC1nY206NmIxZTU0NzUtNzY2MS00OTIxLWFhMjYtZDExNzU4YjJmM2Yx@japan001.tmdns-sing.top:13890?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821日本 
vmess://eyJ2IjoiMiIsImFkZCI6Imtsby45ODY5ODYuc2hvcCIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDgyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiNzVjOTczMS00MDhkLTRhYTYtOGFlOS0zODU3MjA1MTEzYTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Imtsby45ODY5ODYuc2hvcCIsInBhdGgiOiIvbnZqeDZqN2tiRFFJUU1admJlVkE5IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InNzc3Nzc3Nzc3Nzc2ZmZmZmZmZnaC4yMDMyLnBwLnVhIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwODIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjQxNzRiOTVkLTExNWUtNGQzOS1hZGQ2LTFmOGRiOTViYjg2MCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic3Nzc3Nzc3Nzc3NzZmZmZmZmZmdoLjIwMzIucHAudWEiLCJwYXRoIjoiLzZXZTNVOURmMVdHeGdGbm9GUHcxIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo5dHFoTWRJclRrZ1E0NlB2aHlBdE1I@switcher-nick-croquet.freesocks.work:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821英国 
ss://YWVzLTEyOC1nY206NmIxZTU0NzUtNzY2MS00OTIxLWFhMjYtZDExNzU4YjJmM2Yx@usa022.tmdns-sing.top:13892?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
ss://YWVzLTEyOC1nY206NmIxZTU0NzUtNzY2MS00OTIxLWFhMjYtZDExNzU4YjJmM2Yx@usa20250815010624020199.tmdns-sing.top:13874?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0821美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDgyMemmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDgyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDgyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDgyMea+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDgyMeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwODIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwODIx5oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://1JMx5gTKqllRmrOi765Ebk3C@45.82.120.197:40408?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0821德国 
anytls://TqO9dK7ieVX2JO6HzP9vUkEMj13th0j5jQM@45.82.120.197:54324?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@173.245.58.158:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@198.41.201.41:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@162.159.251.147:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.16.244.36:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
hysteria2://WZ01n3FX4venCVCe9KaiztCZNOK1gYDU5593CK@45.82.120.197:47722?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=REI9eqfk6v8BGDJleZGZVFZRtSzMDSb6l7YV&mport=&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@103.21.244.144:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.16.170.148:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.25.22.17:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@173.245.59.97:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
trojan://19c8d140-23e0-4bed-95be-b97102992426@45.82.120.197:37675?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/OsRrfC12Fg4EBTNAQGNZNvGerjd0Uj%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzU1ZWY0MTItOWZjOS00OWYyLTgzMGYtYmI5MDE2OWEwMmFhQDQ1LjgyLjEyMC4xOTc6NjEzOTg6d3M6L2ExY3FpcWtyenNEYnl3dVRlJTNGZWQlM0QyNTYwOnN3ZGlzdC5hcHBsZS5jb206bm9uZTp0bHM6c3dkaXN0LmFwcGxlLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0821德国 
hysteria2://zeOJn0La77BUtvAfJRKC5@45.82.120.197:16107?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=lj0gFzVz1T9fJpg54noEyM6kX0md&mport=&os=#0821德国 
anytls://jsrw5uho96aGGIMubXwkMVLHg8X5VGcpaboqC@45.82.120.197:55932?insecure=1&sni=swdist.apple.com&alpn=h2&fp=&os=#0821德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4xOTciLCJwb3J0IjoyNDYzNiwic2N5IjoiYXV0byIsInBzIjoiMDgyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3NmI3MzU3Ny0wMjU4LTRmMDEtOTA5NC0xZTgyZjU2ZTk0NmUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL1NyR1hodnBkbmYzbEpJUD9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3dkaXN0LmFwcGxlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.19.206.167:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@190.93.246.230:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@173.245.49.54:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@173.245.58.4:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.25.154.175:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@104.18.154.3:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 
vless://eee610a1-0c4f-4b90-b5af-8c0fda1c4dad@103.21.244.215:443?flow=&encryption=none&security=tls&sni=co.strosoa.dpdns.org&type=xhttp&host=co.strosoa.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0821德国 


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
