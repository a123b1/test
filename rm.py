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

vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.27.0.44:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzQ0OTMsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDjmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDjnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA5NzIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDjnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6Ijc3MGVlNzMwLTI0NTAtNGUzYy1hNmM2LTM5MzJiZDMyYWZiZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMTA4576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://3a67aaab-515e-4079-a518-d00cb5e6b20e@151.101.158.204:80?flow=&encryption=none&security=&sni=zmaoz.faculty.ucdavis.edu.&type=ws&host=fatmelo.com&path=/olem/ws%3Fed%3D64&headerType=none&alpn=h2%2Chttp/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108芬兰 
hysteria2://5eaa121d-4362-444d-8219-29b02c35303a@151.249.104.35:34623?insecure=1&sni=jquery.com&alpn=&fp=&os=#0108捷克 
hysteria2://ff006ffb-ad09-4d79-8c27-91dcd9123d8b@151.249.104.35:34623?insecure=1&sni=digitalocean.com&alpn=&fp=&os=#0108捷克 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@154.197.26.237:8388#0108中国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.37.139:989#0108菲律宾 
trojan://94d219c9-1afc-4d42-b090-8b3794764380@160.30.21.105:443?flow=&security=tls&sni=std1.loadingip.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108越南 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.181.162.137:443#0108日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNDguMTU4IiwicG9ydCI6NTAwNTIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDjnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo0MTAyMCwic2N5IjoiYXV0byIsInBzIjoiMDEwOOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NjYwMSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MTcwNCwic2N5IjoiYXV0byIsInBzIjoiMDEwOOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MzAwMiwic2N5IjoiYXV0byIsInBzIjoiMDEwOOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NDEwNCwic2N5IjoiYXV0byIsInBzIjoiMDEwOOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MjExMiwic2N5IjoiYXV0byIsInBzIjoiMDEwOOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0108丹麦 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@185.22.155.228:23456#0108俄罗斯 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@194.5.215.59:8080#0108美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=vkvd127.mycdn.me&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0108美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0108美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=207.148.22.93&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0108美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpucTk2S2Z0clpBajNMdUZRRVNxbW40NE1vNW9DdW8yY2lwb0VzYWUyNW1ybUhHMm9KNFZUMzdzY0JmVkJwTjVEV3RVRUxadXRWaGhYczhMZTVCOGZaOWhMbjl5dHd2YmY=@208.67.105.87:42501#0108荷兰 
ss://YWVzLTI1Ni1jZmI6TTN0MlpFUWNNR1JXQmpSYQ==@217.30.10.18:9011#0108波兰 
ss://YWVzLTI1Ni1jZmI6YzNOdEhKNXVqVjJ0R0Rmag==@217.30.10.18:9084#0108波兰 
ss://YWVzLTI1Ni1jZmI6RVhOM1MzZVFwakU3RUp1OA==@217.30.10.18:9027#0108波兰 
ss://YWVzLTI1Ni1jZmI6RkFkVXZNSlVxNXZEZ0tFcQ==@217.30.10.18:9006#0108波兰 
ss://YWVzLTI1Ni1jZmI6Rkc1ZGRMc01QYlY1Q3V0RQ==@217.30.10.18:9050#0108波兰 
ss://YWVzLTI1Ni1jZmI6QndjQVVaazhoVUZBa0RHTg==@217.30.10.18:9031#0108波兰 
ss://YWVzLTI1Ni1jZmI6ZjYzZ2c4RXJ1RG5Vcm16NA==@217.30.10.18:9010#0108波兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.112.236.3:443#0108德国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.141.82.165:8848#0108德国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.142.21.211:8848#0108英国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.18.5.163:8848#0108卡塔尔 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.211.229.86:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.80.203:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.222.136.128:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.58.159.18:8848#0108美国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.194.227.32:8848#0108台湾 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.220.163.233:8848#0108中国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.85.33.177:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.88.126.102:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.93.31.33:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.122.162:443#0108韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA45rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://dongtaiwang.com@46.17.41.189:50717?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0108俄罗斯 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@46.183.217.232:990#0108拉脱维亚 
vless://4c5f4cf8-b30a-4658-84bb-f0145dd123d4@47.251.95.178:443?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/4c5f4cf8-b30a-4658-84bb-f0145dd123d4&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoxNTE5OSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI5YjZlODAzNS0yMGE1LTQ1NDgtYTE5YS0yNTY4NWM0ZmI1NzkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozNDAzMSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmNTFkNDIxNS0zZmUwLTQ2MGYtYTMxNC1jZjg1OTUwMmI2MDYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9tRlhLQXUwYTFtdE1PdDZLcVV4VEZuMmt4MzhVVXpyZCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://f51d4215-3fe0-460f-a314-cf859502b606@5.180.253.233:49996?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/p3N5UOj3O&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6Mzk0NzQ5MjUtMGUxMy00NDQxLTg1OTctYzA3ZTFhMTgwMDFjQDUuMTgwLjI1My4yMzM6NDY2NDc6d3M6L0dIUWNhN3kzNFJxOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo2MjA2Mywic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI3MjhkYzY3Zi0yZGIyLTQyMzQtOTIwMy03Y2RkNGViZTQ0MTkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii8zS2pnYUtsa1JmeGVZQVR1ckhBZm1lSjZKNGlNU2l1IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://wHciLTs7cbgvpu0az5IMT7z49j7jLPk@5.180.253.233:29879?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=F5oQCXMVosXpotsFS96GksmaMHoSYQyw08rVAwwC&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoyMzg2OSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI5YThiMDJlZi1kYjk1LTQ0MjctOGUyYS1mYjgwM2Q3YmIwMTUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9iTzkyRDdkYW1DZ1AwT2R0WDUiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://39474925-0e13-4441-8597-c07e1a18001c@5.180.253.233:48910?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/SQxsoiPxzfBFmnTtcVpSsjftzLiKJsk&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTQ4NDZjNzctODc5ZC00OTNmLWIxOTctNDU4ZjYyZmRiOTZlQDUuMTgwLjI1My4yMzM6MzkyMDp3czovMzVLMEYxUVE2WjhFUUQ5YzloMHFPTm8wY21uQjp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzYxMzAyODctNDUxYy00MDQyLWFlZTUtNjJiNzJhMWM5YWFmQDUuMTgwLjI1My4yMzM6NTk3Mjc6d3M6LzJEOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
trojan://0b56b131-9c3c-414d-9000-8c44f2026d59@5.180.253.233:62497?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/IftZ&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://f51d4215-3fe0-460f-a314-cf859502b606@5.180.253.233:34385?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/cVXiWwJUok41EDpkXugO99pjf&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://9a8b02ef-db95-4427-8e2a-fb803d7bb015@5.180.253.233:41816?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/rovfTekx&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NzI4ZGM2N2YtMmRiMi00MjM0LTkyMDMtN2NkZDRlYmU0NDE5QDUuMTgwLjI1My4yMzM6NDU2NjM6d3M6L2ZNY3pRRnlsUjhMSVlwRFA5VVh6OEgzT005SHA5VEpUOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo2NTIxNywic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxOTIxNDVlYi01MWU2LTRlZGItOGY4Ni02NjhiMGQxZWNkNTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://9b6e8035-20a5-4548-a19a-25685c4fb579@5.180.253.233:17706?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/UdBwF6hrUWTlZJAK3J8gQC2MS1BJEU&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://192145eb-51e6-4edb-8f86-668b0d1ecd51@5.180.253.233:61741?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/ZzbY&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
trojan://39474925-0e13-4441-8597-c07e1a18001c@5.180.253.233:7540?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/tr7OSacOW3MuQ7VUVpyqUSE&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://5a2bfe0b-08c7-499c-a531-3530380bcf72@5.180.253.233:24998?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/tuZaqCYTI8MVYDxrFQUiLgHn53&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWEyYmZlMGItMDhjNy00OTljLWE1MzEtMzUzMDM4MGJjZjcyQDUuMTgwLjI1My4yMzM6NDc5ODg6d3M6L0Z2bmx6SDU4QVc6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0108德国 
hysteria2://xqaKjVP2t2cNKFawWeuVzF487T8vEcbj@5.180.253.233:25434?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=IpJgeZe3unaQNm0By9HwDlq9lMI7&os=#0108德国 
trojan://36130287-451c-4042-aee5-62b72a1c9aaf@5.180.253.233:16087?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/ZIdhzRAVXnVSi49sFKbq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
trojan://8ed60d26-03fb-4625-8446-8a07d4235010@5.180.253.233:64656?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/b&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
trojan://5a2bfe0b-08c7-499c-a531-3530380bcf72@5.180.253.233:32875?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/Ym6MQvxWTqP5KWwojEs9vyXuyWZDN70c&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo2MDI5NSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxNDg0NmM3Ny04NzlkLTQ5M2YtYjE5Ny00NThmNjJmZGI5NmUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii94eTFBSUFQTHE5YjRXNlM5NmxPMFZUTUEiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://192145eb-51e6-4edb-8f86-668b0d1ecd51@5.180.253.233:53415?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/GFcAxQs8aFg1DACxYN8t6145XMJRD&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
hysteria2://TUDZFRAMXtNnjEWBjB4EgpUjvq2AggM1JPfpW7@5.180.253.233:42537?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=5fKAQvMZ75zL8bwbWU7QPzHNmG2GE&os=#0108德国 
trojan://14846c77-879d-493f-b197-458f62fdb96e@5.180.253.233:7576?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/h6IcBXPQndELeQ6OUHGLnja&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTkyMTQ1ZWItNTFlNi00ZWRiLThmODYtNjY4YjBkMWVjZDUxQDUuMTgwLjI1My4yMzM6MzIyMTA6d3M6LzlLbkVqcERIV3EyZDBIYzhENDkwcll5WVBxTzp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0108德国 
trojan://728dc67f-2db2-4234-9203-7cdd4ebe4419@5.180.253.233:54590?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/vmSa&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://540b334c-bc81-4064-8946-f7ff37826f95@5.180.253.233:64332?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/J9VbMdJlILSQor9gEQveLGkSHZfbYe&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
hysteria2://X3eJzygCc72uckuRoqwRGyWiOwH1hwp@5.180.253.233:42430?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=rO6L7ofbY2XSp4tt0fFgHjai6tKskLaAz&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NzgyMSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI1YTJiZmUwYi0wOGM3LTQ5OWMtYTUzMS0zNTMwMzgwYmNmNzIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9IR08wWUV3aktmN3VhQXVNTjhzZlB0d0p1REc4OXRCSiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtcG9seTEzMDU6Y2QzMzZhZjQtNWY5My00NTJhLTk2OGYtNzJkNDBjZWZmOGE2QDUuMTgwLjI1My4yMzM6NjUxNDc6d3M6L2g3RUduZVoyc3k5YWRwSDdTMEZxZ1FrOW44ZWs5dlpKOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoyNjEwMiwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzOTQ3NDkyNS0wZTEzLTQ0NDEtODU5Ny1jMDdlMWExODAwMWMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9KRUF6T1VMckZuMGFxejZadk5DUVBzUFp0IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MGI1NmIxMzEtOWMzYy00MTRkLTkwMDAtOGM0NGYyMDI2ZDU5QDUuMTgwLjI1My4yMzM6MTc1NTU6d3M6L0xsZVBOREU6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0108德国 
hysteria2://rl4VTQY9sSNU2IA5XHVecUABiyeP@5.180.253.233:21008?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=D31UcewWKAVmvWZgwc5d5R0B2&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NDM0Nywic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4ZWQ2MGQyNi0wM2ZiLTQ2MjUtODQ0Ni04YTA3ZDQyMzUwMTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9jM0R0cE55ZG5CTkdhWEg2WCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://cd336af4-5f93-452a-968f-72d40ceff8a6@5.180.253.233:18485?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/48b4I72CTxvlQ7&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://8ed60d26-03fb-4625-8446-8a07d4235010@5.180.253.233:46965?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/Pc0ocrr3KhqbL12KCYqAiLbc&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
hysteria2://pqXGeh0LNXuTmP9McgEv05Ahit5Zxa@5.180.253.233:60836?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=DddNhK84cJATFQxGj&os=#0108德国 
hysteria2://jRYP2XyTj1cKO6WYzWAUSeBXYu@5.180.253.233:36472?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=qLb4jhdYaE94Jyc51ev0P1ByZwJhQCxTtxboyH&os=#0108德国 
trojan://540b334c-bc81-4064-8946-f7ff37826f95@5.180.253.233:15052?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/kCZrKu0OEza48VIKY&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://728dc67f-2db2-4234-9203-7cdd4ebe4419@5.180.253.233:59080?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/ko4LJaUHX8CYeF2A2hQUugrcpc&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://0b56b131-9c3c-414d-9000-8c44f2026d59@5.180.253.233:62270?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/JHUJam98UocWcdL1uKMpprl92oEMyf&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
hysteria2://5WcsLn5U3f0dskZVvQsNvw3iOt7CPPqBw@5.180.253.233:60060?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=LMtckhjGlLYBmgFZzQRcudnAEQxrQLyXnVJomP&os=#0108德国 
vless://36130287-451c-4042-aee5-62b72a1c9aaf@5.180.253.233:44235?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/60m&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OWE4YjAyZWYtZGI5NS00NDI3LThlMmEtZmI4MDNkN2JiMDE1QDUuMTgwLjI1My4yMzM6NDM4OTI6d3M6L1FCbXFLZDRrV2g6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NTQwYjMzNGMtYmM4MS00MDY0LTg5NDYtZjdmZjM3ODI2Zjk1QDUuMTgwLjI1My4yMzM6NTc3NDA6d3M6L05DNXdaQkxHS0dVODp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo1Mjc4MSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIwYjU2YjEzMS05YzNjLTQxNGQtOTAwMC04YzQ0ZjIwMjZkNTkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9NVzdSIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://14846c77-879d-493f-b197-458f62fdb96e@5.180.253.233:50175?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/wWy&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
hysteria2://7bMq11fJ2TcEJS8EM4XBocIM9AygcQQ7G01A8y8@5.180.253.233:8244?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=AZuqkHb6OrKecTuGe6G8&os=#0108德国 
vless://9b6e8035-20a5-4548-a19a-25685c4fb579@5.180.253.233:12022?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/c8fpjoB&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NjUyMiwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjZDMzNmFmNC01ZjkzLTQ1MmEtOTY4Zi03MmQ0MGNlZmY4YTYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9OQ0EzNG5lTThiSHpZQzgiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoyMTczMCwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzNjEzMDI4Ny00NTFjLTQwNDItYWVlNS02MmI3MmExYzlhYWYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9kNDJnZXZHakNTOXVxNW52aVFLN0pLM1ZyOUMiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OGVkNjBkMjYtMDNmYi00NjI1LTg0NDYtOGEwN2Q0MjM1MDEwQDUuMTgwLjI1My4yMzM6NDI2MDQ6d3M6L1JITTNDaVNtNXZFdllNS1llaDNHTXNKcDFhOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
trojan://cd336af4-5f93-452a-968f-72d40ceff8a6@5.180.253.233:18477?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/4dTScY0GIk&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjUxZDQyMTUtM2ZlMC00NjBmLWEzMTQtY2Y4NTk1MDJiNjA2QDUuMTgwLjI1My4yMzM6MTQ0Mzk6d3M6L3o0QjRhUnYxZVVhYnREOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
hysteria2://vAfIqgYpE8oxvCR6kFwHtTwki@5.180.253.233:57515?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=qhASoCXttasn7B188&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozMjk0NSwic2N5IjoiYXV0byIsInBzIjoiMDEwOOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJkNmNhMDBhMC03NDg5LTRmNDItODM4OC04NTk5MjRhZjg0ODUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9FbUFFaGhBd0duWUdKSEZtYmJVTFciLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZDZjYTAwYTAtNzQ4OS00ZjQyLTgzODgtODU5OTI0YWY4NDg1QDUuMTgwLjI1My4yMzM6MTQ4Nzk6d3M6L29mVHdiRTdBOGZ3S1JQV0twM3o2TlRkZkVwdE06dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTo6OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OWI2ZTgwMzUtMjBhNS00NTQ4LWExOWEtMjU2ODVjNGZiNTc5QDUuMTgwLjI1My4yMzM6MjUyNzI6d3M6L0h6ZHZzSDhhdE54OnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0108德国 
hysteria2://0hH3hAldBHQymMz5vTs@5.180.253.233:63354?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=dL2j9GGAamMlxWUo3BVIIa4spJ7sIX&os=#0108德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo2NjIzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA45b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjU0MGIzMzRjLWJjODEtNDA2NC04OTQ2LWY3ZmYzNzgyNmY5NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJwYXRoIjoiL3RrUEpCYWZRSUoiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://9a8b02ef-db95-4427-8e2a-fb803d7bb015@5.180.253.233:58267?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/cjAoJJevk6t2GbUJGLkhF&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpNN3gxbUdOT3doUGlSQjlqU3haSk55@51.13.182.236:6870#0108挪威 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.196.112.58:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.69.160.222:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.89.164.115:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.178.191.236:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.178.84.59:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.186.92.34:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.200.223.152:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.201.172.79:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.202.77.81:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.238.219.226:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.245.207.144:443#0108美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.249.152.9:443#0108日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.69.180.74:443#0108美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0108英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpDalJsODE3Q3hYcFZKMGoybmhKUldh@62.210.88.22:443#0108法国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=wrmelmwxlf.gktevlrqznwqqqozy6hgvqxwfmfsvgvs6c7kjnrubuh.cc&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0108美国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0108美国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=66.135.11.68&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0108美国 
hysteria2://18240b2dfdd76484@70.34.207.153:443?insecure=1&sni=70.34.207.153&alpn=&fp=&obfs=salamander&obfs-password=d2648ec2&os=#0108瑞典 
vless://9e316ce0-8fd3-4058-bc5e-241f9c3a9f56@78.157.59.140:50067?flow=&encryption=none&security=&sni=MgbJP.divarcdn.com%2CLXHRl.snappfood.ir%2C3cubP.yjc.ir%2CXbifM.digikala.com%2CHL56Q.tic.ir&type=ws&host=MgbJP.divarcdn.com%2CLXHRl.snappfood.ir%2C3cubP.yjc.ir%2CXbifM.digikala.com%2CHL56Q.tic.ir&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108德国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@8.218.120.79:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108美国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@8.222.158.140:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowZ29hdGpsR21LZUt0OUVuNnZmc0pG@89.185.85.227:19262#0108荷兰 
ss://YWVzLTI1Ni1nY206SVk4UDJPN1hJUVpWTDlKRQ==@8tv68qhq.slashdevslashnetslashtun.net:17001#0108美国 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@Cmc5.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc5.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108越南 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@api.namasha.co:443#0108阿拉伯酋长国 
vmess://eyJ2IjoiMiIsImFkZCI6ImNtMS5hd3NsY24uaW5mbyIsInBvcnQiOjI1MjMwLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA45L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjI0M2VhYjUyLTlhYzEtNDA1Yy04ODdjLWViMTEyYzA5ODViOCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY20xLmF3c2xjbi5pbmZvIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJjbTEuYXdzbGNuLmluZm8iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@cmc5.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc5.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108越南 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@cmc6.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc6.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108越南 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@cminit.exitlag.xyz:566#0108中国 
vless://d7a6f3c2-5c25-46d9-bf7d-2b0e8cf1703d@phx-plus-1ddns.faforex.eu.org:18443?flow=&encryption=none&security=reality&sni=www.tesla.com&type=tcp&host=&path=&headerType=none&alpn=&fp=edge&pbk=8233FxCRw1a_aCJ8d1HwHBMD_fABUNNW7rsrFe3vK0s&sid=e6658462&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108美国 
ss://YWVzLTI1Ni1nY206VzZMMlo1Q09XRjRUR0M4Uw==@qh62onjn.slashdevslashnetslashtun.net:16015#0108新加坡 
ss://YWVzLTI1Ni1nY206VTVHQVFNTUlGUTJGRDQ0QQ==@qh62onjn.slashdevslashnetslashtun.net:18003#0108日本 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@series-a2-mec.varzesh360.co:443#0108阿拉伯酋长国 
trojan://94d219c9-1afc-4d42-b090-8b3794764380@std1.loadingip.com:443?flow=&security=tls&sni=std1.loadingip.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0108越南 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:571#0108美国 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:573#0108美国 
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
