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

hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192-227-152-86.nip.io:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&os=#0416美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozNzgwMiwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MzEyMSwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTc4NTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://V2RAXX@v2raxx-channel.cataba.ir:15379?flow=&encryption=none&security=&sni=&type=ws&host=&path=/%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%2C%40V2RAXX-telegram%3Fed%3D2560flow%3D-udp443&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vmess://eyJ2IjoiMiIsImFkZCI6InhnLmRhc2h1YWkuY3lvdSIsInBvcnQiOjE5OTAxLCJzY3kiOiJhdXRvIiwicHMiOiIwNDE26aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJlMDZkYzA2YS1iNjJiLTRjMDQtYjQ5Ny00ZTkzODQyZGEzYzMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InhnLmRhc2h1YWkuY3lvdSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0NC4yNTUuMzYuMjU0IiwicG9ydCI6MTQxMDAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImY2ODY2YjBiLWY5NDYtNGEwMy04ZGYwLWM3ZTAwMTZiNTVhZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJhaWR1LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpiZTQ0MzY4OS1iYzY0LTQ5ZmYtODVhNS04ZWVjYWEyMjM1ZDM=@zz5.fgmcx.top:41068#0416法国 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6ImR4djQucGFpNTAyODgudWsiLCJwb3J0IjoxNDEwMCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZjY4NjZiMGItZjk0Ni00YTAzLThkZjAtYzdlMDAxNmI1NWFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE2576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJvY2JjLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://63dbc6d0-4890-320c-8874-56f9f002d425@158.180.82.98:15446?flow=&security=tls&sni=freehr01.jd0001.top&type=grpc&mode=none&host=&serviceName=freehr01&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416韩国 
trojan://0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01@104.21.6.179:443?flow=&security=tls&sni=uS6-16.890601.xyz&type=ws&header=none&host=us6-16.890601.xyz&path=/ILLcisbMYUd6MQzxVoMQ&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
trojan://telegram-id-privatevpns@52.19.205.220:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416爱尔兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozNzgwMiwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDI4OTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0NC4yNTUuMzYuMjU0IiwicG9ydCI6MTQxMDAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImY2ODY2YjBiLWY5NDYtNGEwMy04ZGYwLWM3ZTAwMTZiNTVhZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImR4djQucGFpNTAyODgudWsiLCJwb3J0IjoxNDEwMCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZjY4NjZiMGItZjk0Ni00YTAzLThkZjAtYzdlMDAxNmI1NWFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJkeHY0LnBhaTUwMjg4LnVrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjE4LjU4LjEwNCIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQxNuiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpSaVB1S0pKbDE4Wmd2THBUald4QndTZktpUGt0OWd6Rkt5eEdDWThlSHRPY0RiMlg=@5.189.201.250:31348#0416俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6InllLmZ4bGNuLmNvbSIsInBvcnQiOjQ1MjQ1LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE26Z+p5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0NjllMGIzMS0zMGMzLTRkYWItODAwZC03MTEyMzI2MzRjZTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://c11ff50c-f582-11ee-94df-f23c9164ca5d@74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net:8443?insecure=0&sni=74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny43MS4yMTciLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTblvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiOTA3MmQzMzktMzg4NS00ZmUxLWIwYmMtMjlmYTc1MDU0MTBlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIxdDNjaHgwLnplZDIzLndlYjEzMzcubmV0IiwicGF0aCI6Ii9maXhlZGZsb2F0aS5jZmQvbGlua3dzZCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IjF0M2NoeDAuemVkMjMud2ViMTMzNy5uZXQiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.62.168:989#0416韩国 
trojan://VMhGp5wEIyCDf90T@123.88.148.42:42303?flow=&security=tls&sni=hk06.run.place&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416香港 
vless://1ccc1dd8-d8ed-4b69-b0c2-27f6282f9755@104.26.9.63:2083?flow=&encryption=none&security=tls&sni=test.bujidao.org&type=ws&host=test.bujidao.org&path=/%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjExMi42NS45Mi4yMCIsInBvcnQiOjQ1NDAyLCJzY3kiOiJhdXRvIiwicHMiOiIwNDE25pel5pysIiwibmV0IjoidGNwIiwiaWQiOiI0NjllMGIzMS0zMGMzLTRkYWItODAwZC03MTEyMzI2MzRjZTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://1688039e-a45f-499e-b9f4-c098c87d3b32@108.162.196.159:443?flow=&encryption=none&security=tls&sni=cr7777.rayan.dpdns.org&type=ws&host=&path=/Telegram%40V2ray_Alpha/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416比利时 
vless://d6a1143b-cdf0-41f8-a646-bd8f11663786@g2.com:443?flow=&encryption=none&security=tls&sni=cr7.medicalhistory.ir&type=ws&host=&path=/vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl-vpnowl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjE4LjU4LjEwNCIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQxNuiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://2fec7227-9abe-46f2-af18-78302b836c45@199.34.228.161:443?flow=&encryption=none&security=tls&sni=3u.2031.pp.ua&type=ws&host=3u.2031.pp.ua&path=/qF5dXhCllosLcFpqdDoAgkondVWl&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
vless://2fec7227-9abe-46f2-af18-78302b836c45@172.67.163.14:443?flow=&encryption=none&security=tls&sni=3u.2031.pp.ua&type=ws&host=3u.2031.pp.ua&path=/qF5dXhCllosLcFpqdDoAgkondVWl&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
vless://944d8b74-7a64-4b07-a278-9f968e9ef99c@mw5.asalemaraghe.ir:443?flow=&encryption=none&security=tls&sni=mw5.asalemaraghe.ir&type=ws&host=mw5.asalemaraghe.ir&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://2fec7227-9abe-46f2-af18-78302b836c45@199.34.228.169:443?flow=&encryption=none&security=tls&sni=3u.2031.pp.ua&type=ws&host=3u.2031.pp.ua&path=/qF5dXhCllosLcFpqdDoAgkondVWl&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
vless://4088e698-69fd-4d15-98bc-f1fe4c071642@160.22.79.177:443?flow=&encryption=none&security=tls&sni=digitalscientificresearchgroup.ir&type=ws&host=digitalscientificresearchgroup.ir&path=TelegramTW_%40WangCai2/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
vless://2fec7227-9abe-46f2-af18-78302b836c45@199.34.228.179:443?flow=&encryption=none&security=tls&sni=3u.2031.pp.ua&type=ws&host=3u.2031.pp.ua&path=/qF5dXhCllosLcFpqdDoAgkondVWl&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
ss://YWVzLTI1Ni1nY206cEtFVzhKUEJ5VFZUTHRN@67.220.95.29:443#0416美国 
trojan://Aimer@108.165.152.202:2083?flow=&security=tls&sni=epcco.ambercc.filegear-sg.me&type=ws&header=none&host=epcco.ambercc.filegear-sg.me&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416台湾 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@67.220.95.29:2375#0416美国 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@23.150.248.199:2375#0416美国 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@67.220.95.133:2375#0416美国 
ss://YWVzLTI1Ni1nY206ZzVNZUQ2RnQzQ1dsSklk@67.220.95.133:5004#0416美国 
ss://YWVzLTI1Ni1nY206VEV6amZBWXEySWp0dW9T@67.220.95.29:6697#0416美国 
ss://YWVzLTI1Ni1nY206UmV4bkJnVTdFVjVBRHhH@67.220.95.133:7001#0416美国 
ss://YWVzLTI1Ni1nY206UmV4bkJnVTdFVjVBRHhH@67.220.95.29:7002#0416美国 
ss://YWVzLTI1Ni1nY206UmV4bkJnVTdFVjVBRHhH@23.150.248.199:7002#0416美国 
ss://YWVzLTI1Ni1nY206Rm9PaUdsa0FBOXlQRUdQ@67.220.95.29:7306#0416美国 
ss://YWVzLTI1Ni1nY206Rm9PaUdsa0FBOXlQRUdQ@67.220.95.133:7306#0416美国 
ss://YWVzLTI1Ni1nY206Rm9PaUdsa0FBOXlQRUdQ@23.150.248.199:7307#0416美国 
ss://YWVzLTI1Ni1nY206Rm9PaUdsa0FBOXlQRUdQ@67.220.95.133:7307#0416美国 
ss://YWVzLTI1Ni1nY206UENubkg2U1FTbmZvUzI3@67.220.95.96:8091#0416美国 
ss://YWVzLTI1Ni1nY206Y2RCSURWNDJEQ3duZklO@67.220.95.29:8118#0416美国 
trojan://Aimer@108.165.152.38:8443?flow=&security=tls&sni=epcco.ambercc.filegear-sg.me&type=ws&header=none&host=epcco.ambercc.filegear-sg.me&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjhiZWU2OWY1LXN1eDhnMC10NXVnc3ctYjYzaC5jbTUucDVwdi5jb20iLCJwb3J0IjoxNzIzNSwic2N5IjoiYXV0byIsInBzIjoiMDQxNuazleWbvSIsIm5ldCI6InRjcCIsImlkIjoiNDBmNmE2MTYtNzE5YS0xMWVmLTllOTUtZjIzYzkxY2ZiYmM5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjI5YWM1N2M5LXN2MnNnMC10YzVvZG8tMW1oODUuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbms5Xlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImNmNzMzMWZhLWJmZWItMTFlZC1hODA3LWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjdjZmQ0MDAxLXN2MnNnMC10MzZmMWkteXlneC5jbTUucDVwdi5jb20iLCJwb3J0IjoxNzIzNSwic2N5IjoiYXV0byIsInBzIjoiMDQxNuazleWbvSIsIm5ldCI6InRjcCIsImlkIjoiMjBiNzIxN2MtY2Y0Mi0xMWVhLTgyZWYtZjIzYzkxNjRjYTVkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5ODBlMTNjLXN2MnNnMC1zd3ZwZTItMXRldHAuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbms5Xlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjU2ZDRiZTc2LWYyNGQtMTFlZi05YjY5LWYyM2M5MTY0Y2E1ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjU4N2NiNjY5LXN2MnNnMC10M2RldXotMXRsYzIuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbms5Xlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjMwNDFmOTU2LTBiOWItMTFmMC1hMmVmLWYyM2M5MWNmYmJjOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzUwMDEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MzEyMSwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDY1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6NDYzNDUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://45b5a55e-3cf9-4f3b-90ec-18a1cc31ea22@85.235.205.212:36019?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0416俄罗斯 
hysteria2://45b5a55e-3cf9-4f3b-90ec-18a1cc31ea22@107.172.235.75:52730?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0416美国 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@67.220.95.29:2376#0416美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM4OTUwNDQxLXN2MnNnMC1zeHQ2a2ctMXJvOHMuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbljbDluqblsLzopb/kupoiLCJuZXQiOiJ0Y3AiLCJpZCI6ImExOGVmMThlLTI5M2EtMTFlZi1iNzZlLWYyM2M5MWNmYmJjOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjM0MjNiODBlLXN2MnNnMC1zeXViNDEtMXFxdXEuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzQsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbljbDluqblsLzopb/kupoiLCJuZXQiOiJ0Y3AiLCJpZCI6IjIyOWEwZmVhLWQ5NzUtMTFlZS04OGM3LWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjAwYWU0YTUzLXN2MnNnMC10MHc2bzEtMWxrOWkuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbms5Xlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImE2MGUzNzgyLTIyM2UtMTFlZS1iOTczLWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozNDY1Miwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzY2MDksInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpiZTQ0MzY4OS1iYzY0LTQ5ZmYtODVhNS04ZWVjYWEyMjM1ZDM=@hk2.fgmcx.top:41049#0416阿拉伯酋长国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDQ0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@111.29.57.125:52612#0416香港 
hysteria2://45b5a55e-3cf9-4f3b-90ec-18a1cc31ea22@23.132.228.217:54565?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0416美国 
hysteria2://45b5a55e-3cf9-4f3b-90ec-18a1cc31ea22@92.112.126.122:48201?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0416乌克兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTAwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjE4LjU4LjYzIiwicG9ydCI6MTgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDE26Iux5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJkMTNmYzJmNS0zZTA1LTQ3OTUtODFlYi00NDE0M2EwOWU1NTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://80aa5178-f936-11ed-8ce6-f23c91369f2d@c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net:8443?insecure=0&sni=c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
vless://f5da3cc4-c81c-418e-a836-fbb53b841caa@79.127.70.67:4268?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
hysteria2://de5486da-f19c-11ef-8eaf-f23c9164ca5d@d446948b-sunz40-svabg7-1td06.hy2.gotochinatown.net:8443?insecure=0&sni=d446948b-sunz40-svabg7-1td06.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@137.175.113.193:8388#0416美国 
hysteria2://279b8588-616b-11ed-a8bf-f23c91cfbbc9@cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net:8443?insecure=0&sni=cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://dongtaiwang.com@46.29.163.171:32555?insecure=1&sni=apple.com&alpn=&fp=&os=#0416俄罗斯 
hysteria2://dongtaiwang.com@46.17.41.217:64816?insecure=1&sni=apple.com&alpn=&fp=&os=#0416俄罗斯 
vless://59860b15-b2d9-47f9-9b92-81bd1639fcc5@172.67.75.52:2083?flow=&encryption=none&security=tls&sni=23-lsjfjwiposkfls.hc2021.cfd&type=ws&host=23-lsjfjwiposkfls.hc2021.cfd&path=/flow%3D-udp443flow%3D-udp443flow%3D-udp443&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416韩国 
ss://YWVzLTEyOC1nY206Vk1oR3A1d0VJeUNEZjkwVA==@gysz0000.dynu.net:56277#0416印度 
vless://6f995056-7802-4a1d-bff7-61678e626c3f@20.189.104.97:443?flow=&encryption=none&security=tls&sni=dee33.azurewebsites.net&type=ws&host=dee33.azurewebsites.net&path=/flow%3D-udp443&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416香港 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE2576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.cal01i9zjfegelp.5xfsur8v62.gosdk.xyz:34016?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416加拿大 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.usl03i9zjfegelp.5xfsur8v62.gosdk.xyz:33506?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416美国 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.usl02i9zjfegelp.5xfsur8v62.gosdk.xyz:33505?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416美国 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.rul01i9zjfegelp.5xfsur8v62.gosdk.xyz:46925?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416俄罗斯 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.pkl01i9zjfegelp.5xfsur8v62.gosdk.xyz:42883?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416巴基斯坦 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.phl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27408?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416菲律宾 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.inl01i9zjfegelp.5xfsur8v62.gosdk.xyz:42882?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416印度 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.aul01i9zjfegelp.5xfsur8v62.gosdk.xyz:34017?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416澳大利亚 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.krl01i9zjfegelp.5xfsur8v62.gosdk.xyz:46668?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416韩国 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.jpl04i9zjfegelp.5xfsur8v62.gosdk.xyz:22269?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416日本 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.jpl03i9zjfegelp.5xfsur8v62.gosdk.xyz:22271?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416日本 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27001?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416日本 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.myl02i9zjfegelp.5xfsur8v62.gosdk.xyz:43383?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416马来西亚 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.sgl02i9zjfegelp.5xfsur8v62.gosdk.xyz:42881?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416新加坡 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.sgl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27401?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416新加坡 
trojan://d70a8847-7c64-4912-98f2-ea21e952880f@aafrtpfxr.hkl03i9zjfegelp.5xfsur8v62.gosdk.xyz:10465?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416香港 
trojan://74260696553770700@robust-redfish.shiner427.skin:443?flow=&security=tls&sni=robust-redfish.shiner427.skin&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImZhZGF3dGF3ZC56aGFuZ3dlaS5saSIsInBvcnQiOjQ2MDA1LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE25Y+w5rm+IiwibmV0Ijoid3MiLCJpZCI6IjRjNWE4YTc1LTdkNjUtNDBhOS04YzNiLWE2N2FiYWUwODUzNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii96aC1jbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InVzejEuZmdtY3gudG9wIiwicG9ydCI6MjM5MDMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImJlNDQzNjg5LWJjNjQtNDlmZi04NWE1LThlZWNhYTIyMzVkMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206T1A4UFhYRE9XMEdGU0JPMg==@150.116.11.9:21005#0416台湾 
vmess://eyJ2IjoiMiIsImFkZCI6ImZhZGF3dGF3ZC56aGFuZ3dlaS5saSIsInBvcnQiOjQ2MDA1LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE25Y+w5rm+IiwibmV0Ijoid3MiLCJpZCI6IjRjNWE4YTc1LTdkNjUtNDBhOS04YzNiLWE2N2FiYWUwODUzNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZmFkYXd0YXdkLnpoYW5nd2VpLmxpIiwicGF0aCI6Ii96aC1jbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6Imh6ejkuZmdtY3gudG9wIiwicG9ydCI6MjM5MTAsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmjbflhYsiLCJuZXQiOiJ0Y3AiLCJpZCI6ImJlNDQzNjg5LWJjNjQtNDlmZi04NWE1LThlZWNhYTIyMzVkMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjA0OTYzMzVjLXN1eDhnMC1zd2J1ZGctMW16d2ouY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6ImEyMDNkODBlLTEwZmUtMTFlZi04OGE2LWYyM2M5MTY0Y2E1ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://74260696553770700@robust-redfish.shiner427.skin:443?flow=&security=tls&sni=robust-redfish.shiner427.skin&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416英国 
vmess://eyJ2IjoiMiIsImFkZCI6Imh6ejkuZmdtY3gudG9wIiwicG9ydCI6MjM5MTksInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6ImJlNDQzNjg5LWJjNjQtNDlmZi04NWE1LThlZWNhYTIyMzVkMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTI5MSwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://dQUWbcwECl@automq-0413-0-proxy.automq-sg.com:443?flow=&security=tls&sni=automq-0413-0-proxy.automq-sg.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0416新加坡 
hysteria2://Bia-SiNAVM-SiNAVM-SiNAVM-SiNAVM@sinavm.sinabigo.ir:443?insecure=1&sni=sinavm.sinabigo.ir&alpn=&fp=&obfs=salamander&obfs-password=@SiNAVM-@SiNAVM-@SiNAVM-SiNAVM&os=#0416荷兰 
hysteria2://Bia-SiNAVM-SiNAVM-SiNAVM-SiNAVM@sinavm.sinabigo.ir:443?insecure=1&sni=&alpn=h3&fp=&obfs=salamander&obfs-password=@SiNAVM-@SiNAVM-@SiNAVM-SiNAVM&os=#0416荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE26aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://459b4a80-bd61-4ecd-a26b-e9c1809d9e45@agaungzhou01.bumbleshrimp.com:31800?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.nvidia.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=qhTzYYIgBzDLNYR79oxftqdo1kzL-1_hGJKfqrOliCY&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk01.x.quickcht3.club:52611#0416香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk02.x.quickcht3.club:52612#0416香港 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01@104.21.77.44:443?flow=&encryption=none&security=tls&sni=Us6-03.890603.XyZ&type=ws&host=us6-03.890603.xyz&path=/GuJUq5kZ2d6MQzxVoMQ&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
vless://d67cfeaf-b277-44ac-ab99-9dd02a7c5299@172.67.200.11:443?flow=&encryption=none&security=tls&sni=Hu9L7.890606.XyZ&type=ws&host=hu9l7.890606.xyz&path=/jAcfFDEOj85lz42MdhsCLV&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416美国 
hysteria2://4e84400e-f4bc-11ef-81b7-f23c932f2c32@57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk:443?insecure=0&sni=57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk&alpn=&fp=&os=#0416美国 
hysteria2://564b440a-700f-11ee-a90c-f23c9313b177@71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk:443?insecure=0&sni=71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk&alpn=&fp=&os=#0416美国 
hysteria2://fb8812ae-dcb5-11ef-a57d-f23c9313b177@90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk:443?insecure=0&sni=90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk&alpn=&fp=&os=#0416美国 
hysteria2://82efba2c-f420-11ef-9529-f23c93141fad@d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk:443?insecure=0&sni=d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk&alpn=&fp=&os=#0416美国 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://3c461e2c-9d13-11ef-8563-f23c913c8d2b@4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net:8443?insecure=0&sni=4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://2ee8f830-09e2-11f0-90e2-f23c913c8d2b@5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net:8443?insecure=0&sni=5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://be8ba532-0dcf-11f0-9a65-f23c9164ca5d@8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net:8443?insecure=0&sni=8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://7af3db60-b2d9-11ef-88ab-f23c913c8d2b@b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net:8443?insecure=0&sni=b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
hysteria2://8de795d2-a06f-11ed-8edf-f23c913c8d2b@bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net:8443?insecure=0&sni=bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net&alpn=&fp=&os=#0416美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE2576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQxNue+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0416波兰 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0416法国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0416日本 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0416新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDI4OTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MTbmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQxNuaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0416斯洛文尼亚共和国 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0416孟加拉国 
hysteria2://Telegram-SiNAVM-SiNAVM-SiNAVM-SiNAVM@sinavm.soft10.ir:443?insecure=1&sni=&alpn=h3&fp=&obfs=salamander&obfs-password=@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM&os=#0416塞浦路斯 
hysteria2://dongtaiwang.com@46.17.41.5:12904?insecure=1&sni=apple.com&alpn=&fp=&os=#0416俄罗斯 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0416以色列 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDY0ODViMGYtZTA0My00MmVmLTk1OTItODVlMmJkZWM0M2EyQDQ1LjgyLjEyMS4xNzc6NTg4MDp3czovM09DaDZ3YkQ1VWNYR1hMSERXV1V6RkZvV3VPTGozZCUzRmVkJTNEMjU2MDp3d3cuYW1lYmxvLmpwOm5vbmU6dGxzOnd3dy5hbWVibG8uanA6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0416德国 
vless://59e91db4-bac2-41ae-9f39-d3169bb6d38f@45.82.121.177:26568?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/73LDxy6FejolZ7zUN%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.97:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.201.41:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
hysteria2://sFZtXrWnZs9VZtJKXxsk8N4hYhuaveaHLBt@45.82.121.177:55696?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=0DSgdXku5iJGluE4v9qLvVKsszZY5C&os=#0416德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xNzciLCJwb3J0Ijo3Mzg1LCJzY3kiOiJhdXRvIiwicHMiOiIwNDE25b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjczNDY0OGQwLWMxZTItNDJjNi04ZTYyLTNhN2YwNDA1NGYyOCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmFtZWJsby5qcCIsInBhdGgiOiIvcUMwdFlNeThzZkE3STc/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5hbWVibG8uanAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://EYjdFFIw2AzYgEnsloSrKRDt@45.82.121.177:23678?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=eSn6D9nZhCzmJOmWd1cLUDb&os=#0416德国 
vless://07271067-76e1-4cc5-994b-d9adc42763c6@45.82.121.177:4049?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/W1UlfU5YmTwtGwuNP3Y3pca%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://1619b2f1-eb62-4550-86a2-3c2168c7c269@45.82.121.177:49367?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/wmNE%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
hysteria2://dstDZsD5AspKxNyOv@45.82.121.177:29020?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=CcKNRN1oZGxBvQ2GX1zz84MzIFGl&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.170.148:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.70:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
trojan://d0f74ab1-5a26-4e40-997e-e09e45667f78@45.82.121.177:5215?flow=&security=tls&sni=www.ameblo.jp&type=ws&header=none&host=www.ameblo.jp&path=/W33YX8vd1MHMTLPAUSOVLqzZud6U%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.18.195:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.104.179:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.22.17:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.202.17:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
trojan://734648d0-c1e2-42c6-8e62-3a7f04054f28@45.82.121.177:31789?flow=&security=tls&sni=www.ameblo.jp&type=ws&header=none&host=www.ameblo.jp&path=/X%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.199.178:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.27.113.190:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzI1MjA4MzgtMjkxZi00ZjEwLThhZTctMTAzMWI1NjM4Y2JkQDQ1LjgyLjEyMS4xNzc6NTk3NjE6d3M6L1hRVE9MRTJjcGc3OUFJc09EJTNGZWQlM0QyNTYwOnd3dy5hbWVibG8uanA6bm9uZTp0bHM6d3d3LmFtZWJsby5qcDpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.164:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xNzciLCJwb3J0IjoxMjU4Nywic2N5IjoiYXV0byIsInBzIjoiMDQxNuW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2ZjdjYzZiOC01OTJmLTRkYTgtOGQxNC01OGU2ZDhhZTIwNjIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiLzh3Y3A4RktjWXNzdXVld2lwWjZOOTRydj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3LmFtZWJsby5qcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.21.130:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 
hysteria2://wXIAU0nf95SVS3NHmO5WGIJMpvkEKkp@45.82.121.177:34231?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=Jg9sV4cg0HFuJKT6dglSxlvxR&os=#0416德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.42.49:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0416德国 



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
