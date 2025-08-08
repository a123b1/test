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

vmess://eyJ2IjoiMiIsImFkZCI6ImZhc3RjdXAubmV0IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MDfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNzY0MTQ1NzQtNzFlMC00NzA2LTg5Y2MtYzViMDljMTM0NDVkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjZG4tbm9kZS1vc3MtOTkucGFvZnUuZGUiLCJwYXRoIjoiL3Byb2ZpbGUvdGVsZWdyYW1Ac3Nyc3ViIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InB1YmcuYWMiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDgwN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3NjQxNDU3NC03MWUwLTQ3MDYtODljYy1jNWIwOWMxMzQ0NWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNkbi1ub2RlLW9zcy05OS5wYW9mdS5kZSIsInBhdGgiOiIvcHJvZmlsZS90ZWxlZ3JhbUBzc3JzdWIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://357b1bba-6400-4944-baff-1b933311ff28@162.159.129.11:443?flow=&encryption=none&security=tls&sni=SsSSSSSsSSSD.890606.Xyz&type=ws&host=SsSSSSSsSSSD.890606.Xyz&path=/kSIHD28dr9nkaMBYIsgt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.157.220:443?flow=&encryption=none&security=tls&sni=XXCsDERT6.777159.XyZ&type=ws&host=xxcsdert6.777159.xyz&path=/O9jlBCbIm3xr1D40NK&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
trojan://tg-fq521free@216.24.57.30:443?flow=&security=tls&sni=torjan.xn--xhq44j.eu.org&type=ws&header=none&host=torjan.xn--xhq44j.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0807美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vmess://eyJ2IjoiMiIsImFkZCI6IkpKSmpqampqbU1NbU0uNDQ0NDkyNi5YWVoiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MDfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZGM1MGViMWQtMjQ0ZC00NzExLWIxNjgtYTEwMWE1ZTZmYjFiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJKSkpqampqam1NTW1NLjQ0NDQ5MjYuWFlaIiwicGF0aCI6Ii9hd21xcTc5QjE3cmZucFhpTmFXYiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807美国 
vmess://eyJ2IjoiMiIsImFkZCI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA4MDfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNDE3NGI5NWQtMTE1ZS00ZDM5LWFkZDYtMWY4ZGI5NWJiODYwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc3Nzc3NzeHh4eC4yMDMyLnBwLnVhIiwicGF0aCI6Ii82V2UzVTlEZjFXR3hnRm5vRlB3MSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4xNjIuMjI4Ljg4IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDgwN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYzA5MjZkZi01NGE4LTNkZjctOTM0Yy1mZDNlYWQ2NGY2YWEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnMyLmNuLWRiLnRvcCIsInBhdGgiOiIvZGFiYWkmVGVsZWdyYW3wn4eo8J+Hs0BXYW5nQ2FpMi8/ZWQ9MjU2MCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4xOTMuMjkuODgiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwODA3576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNjMDkyNmRmLTU0YTgtM2RmNy05MzRjLWZkM2VhZDY0ZjZhYSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuY24tZGIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgwLjExMS44OCIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MDfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiY2MwOTI2ZGYtNTRhOC0zZGY3LTkzNGMtZmQzZWFkNjRmNmFhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwODA3576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDgwN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDgwN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://HfK3UK4MoXxYUccnp7qzx3Y3o@209.38.144.136:34321?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0807美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjEyMS40OC4xNzQiLCJwb3J0IjoyMDc4OCwic2N5IjoiYXV0byIsInBzIjoiMDgwN+WPsOa5viIsIm5ldCI6InRjcCIsImlkIjoiYmZjNjMwYWEtNDU5OC00NDgxLTkzMzgtY2FjMTVlM2U2YjY1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807斯洛文尼亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDgwN+aWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807韩国 
trojan://005fddef-e432-482f-a98c-2715563a2b25@139.199.194.86:36009?flow=&security=tls&sni=139.199.194.86&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807韩国 
ss://YWVzLTEyOC1nY206MDE3MjFlNDMtNTM4OS00Zjk3LWIyMWMtOTAwYWJiMmJkYTll@awes35lesl.blhao0o.dpdns.org:12012?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807日本 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwODA35oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.183.154:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807香港 
ss://YWVzLTI1Ni1nY206aVVCMDkyM1JCQQ==@154.3.8.151:30067?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807香港 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDgwN+mmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0807希腊 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.174:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.24.46.117:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@141.101.113.112:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.6:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.23.99.41:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.27.206.118:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.20.192.155:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.112:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@108.162.192.139:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@190.93.244.134:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.25.78.193:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.59.50:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.16.155.114:443?flow=&encryption=none&security=tls&sni=cs.ryalol.qzz.io&type=xhttp&host=cs.ryalol.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
hysteria2://klvkocX4I6a0gujR2K4rajalieHgsRNwj7b@45.82.122.236:9485?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=7HJ2jC5nMib7XL0Wi25pCyOmOXOmbMpNe9Sn0p8&mport=&os=#0807德国 
anytls://NOfJkQsa93nkchQXHUK8Vo9Z19IHxuRm@45.82.122.236:11862?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0807德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0IjoxOTU0OSwic2N5IjoiYXV0byIsInBzIjoiMDgwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI5YjA4MzJmYy05ZTI4LTRmZjktYmM0OS00ODljY2ZhMTA1NWMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9WNFdjcllHSmlKeVljP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjEwMS4xNTIuNjgiLCJwb3J0IjoyMDA4Niwic2N5IjoiYXV0byIsInBzIjoiMDgwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlMzUwMWNiNi1hZjlhLTQ0YWItYmI0Yi00OGFhNWZjYTJhZTgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://7817e21e-81cd-4cbc-a0df-cdce11f6ccd6@45.82.122.236:29032?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/Zr2RkbGvIziHnxjZEo5xv%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0IjozNjY3Niwic2N5IjoiYXV0byIsInBzIjoiMDgwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwZmI0NzMzZC05NzRlLTQ1N2UtOGJkYi05N2ZkNjNiMjdjNTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9RP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://1cff427d-1035-4ebd-b153-7246c94a6d25@45.82.122.236:40456?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/qHAQ2R%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
trojan://6a7d7c7a-b584-4403-a0c4-41f286ddc06a@45.82.122.236:43233?flow=&security=tls&sni=api.namasha.co&type=ws&header=none&host=api.namasha.co&path=/477emub7L14I4%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
hysteria2://0lZ5XRSaI17dovJZ2pogfI@45.82.122.236:46782?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=KJccTYZVdY6WO9j9ueUwJ4mzCBShS8svq&mport=&os=#0807德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMzYiLCJwb3J0Ijo1ODAzMywic2N5IjoiYXV0byIsInBzIjoiMDgwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI1ZmM3NzQ2MC1iNjBjLTQ2YTktOGFhZi1mMGI5Njk1MTZmODAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9pR3U2WWdNcWVKSWRWaTl6YXlZSnJBcVNHdno4YWhoP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
anytls://yMsQYIHRhAgOisH8CGdOzyaIq8b14YgqrL7@45.82.122.236:61279?insecure=1&sni=api.namasha.co&alpn=h2&fp=&os=#0807德国 
vless://90cae3a4-b5bb-408e-b79c-3b5c074f8a25@45.82.122.236:61556?flow=&encryption=none&security=tls&sni=api.namasha.co&type=ws&host=api.namasha.co&path=/hdjfp24cV81Ee0NHiH2UTNQnM%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807德国 
hysteria2://wy5lyoz5SGwI2LSNkk67paz0W@45.82.122.236:63440?insecure=1&sni=api.namasha.co&alpn=&fp=&obfs=salamander&obfs-password=R9qGBHIeElbZoKamlbg&mport=&os=#0807德国 
hysteria2://0a2986e1-86da-411b-b986-63360f8eebb4@172.252.236.213:48695?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0807瑞士 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDgwN+a+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://db400287-fb42-441d-8a76-5624a8a96f49@172.67.66.177:443?flow=&encryption=none&security=tls&sni=rayan-roof.atena.dpdns.org&type=ws&host=rayan-roof.atena.dpdns.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0807亚美尼亚 


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
