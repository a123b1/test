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

vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xNy4yMTMuMjQxIiwicG9ydCI6MjA4Miwic2N5IjoiYXV0byIsInBzIjoiMDExM+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI0YjM2NjI1Yy1iOWQ5LTNlYTYtYWVkNS04NmQ2MmM3MGUxNmQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjEwMC02LTIwNC0xMjkuczMuZGItbGluazAxLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xMDQuMjUuMjA0LjExNyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@104.22.53.235:80?flow=&encryption=none&security=&sni=cc.ailicf.us.kg&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
ss://bm9uZTo5MmNlM2RkNC02ZTA3LTk5NDktOWQ5OC03OTFiNjRkNDM1MTk=@106.75.128.205:46257#0113澳大利亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA5NzIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMTPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6Ijc3MGVlNzMwLTI0NTAtNGUzYy1hNmM2LTM5MzJiZDMyYWZiZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAxMTPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://7daf833c-37b9-4afc-8495-96590f03f781@120.232.217.96:21332?flow=&security=tls&sni=120.232.217.96&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@129.232.134.112:990#0113南非 
vless://55520747-311e-4015-83ce-be46e2060ce3@129.80.177.42:443?flow=&encryption=none&security=tls&sni=uxf.vs2024.us.kg&type=ws&host=uxf.vs2024.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
vless://4d8426b2-0af1-4eb5-a231-b62152d7b9b9@151.101.130.133:443?flow=&encryption=none&security=tls&sni=live.989bull.com&type=ws&host=aft.vc&path=/TorVipxyy%3Fed%3D&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vless://7d47e46d-ee53-4f86-8c9a-da2e9aa91bde@151.101.130.228:80?flow=&encryption=none&security=&sni=&type=ws&host=wWw.SpEeDtEsT.NeT.ZuLa.aIr.IkCoSaLeS.iR.D662599.v03.feadlenetwork19922h.net&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113加拿大 
vless://4d8426b2-0af1-4eb5-a231-b62152d7b9b9@151.101.2.133:443?flow=&encryption=none&security=tls&sni=live.989bull.com&type=ws&host=aft.vc&path=/TorVipxyy%3Fed%3D&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuMi4yMTYiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDExM+azleWbvSIsIm5ldCI6IndzIiwiaWQiOiJjNjlmMzAyOS1hZTFlLTQ1Y2EtYWEwOC03MDk3MGYxNGRmZDIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InRlbGVncmFtLUlTVnZwbi5pciIsInBhdGgiOiIvcmFjZXZwbj90ZWxlZ3JhbUBJU1Z2cG4tdGVsZWdyYW1ASVNWdnBuLXRlbGVncmFtQElTVnZwbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InRlbGVncmFtLUlTVnZwbi5pciIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://25b8f4b0-4f7d-400f-bc4a-f10e5b8796a2@151.101.66.133:443?flow=&encryption=none&security=tls&sni=anchor.fm&type=ws&host=magdl.ir&path=/stream/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@154.197.26.237:8388#0113香港 
trojan://94d219c9-1afc-4d42-b090-8b3794764380@160.30.21.105:443?flow=&security=tls&sni=std1.loadingip.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113越南 
vless://55520747-311e-4015-83ce-be46e2060ce3@160.79.104.98:443?flow=&encryption=none&security=tls&sni=uxf.vs2024.us.kg&type=ws&host=uxf.vs2024.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
ss://YWVzLTI1Ni1nY206ZmFCQW9ENTRrODdVSkc3@167.88.63.21:2375#0113美国 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@172.64.35.129:80?flow=&encryption=none&security=&sni=&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@172.67.27.46:80?flow=&encryption=none&security=&sni=cc.ailicf.us.kg&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNDguMTU4IiwicG9ydCI6NTAwNTIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMTPnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NjYwMSwic2N5IjoiYXV0byIsInBzIjoiMDExM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NDEwNCwic2N5IjoiYXV0byIsInBzIjoiMDExM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MzAwMiwic2N5IjoiYXV0byIsInBzIjoiMDExM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo0NjYwMiwic2N5IjoiYXV0byIsInBzIjoiMDExM+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.193.49.88:989#0113爱沙尼亚 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@185.22.155.228:23456#0113俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NC44Ny42OS41MCIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjFjYzU5YTNhLTk2MjUtNDBmNy1iMGU2LWUyMzMyODZhZTgyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NC44Ny42OS41MiIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjFjYzU5YTNhLTk2MjUtNDBmNy1iMGU2LWUyMzMyODZhZTgyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpnaEJ1SjlwWk9GOU1vaGhHeVBqbzNydmlsUWhsdzlOekJEbE9WRG9uUU4wPQ==@195.15.254.25:54748#0113瑞士 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS40MiIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjFjYzU5YTNhLTk2MjUtNDBmNy1iMGU2LWUyMzMyODZhZTgyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS41MCIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjFjYzU5YTNhLTk2MjUtNDBmNy1iMGU2LWUyMzMyODZhZTgyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS44NiIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjFjYzU5YTNhLTk2MjUtNDBmNy1iMGU2LWUyMzMyODZhZTgyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://e7934134-5395-47a7-bd90-f68a467e3971@198.41.192.239:443?flow=&encryption=none&security=tls&sni=usb.warpo.me&type=ws&host=usb.warpo.me&path=/bing&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0113美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=207.148.22.93&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0113美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=vkvd127.mycdn.me&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0113美国 
trojan://vzhXXZVw@223.113.54.145:36442?flow=&security=tls&sni=223.113.54.145&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113香港 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.141.82.165:8848#0113德国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.142.21.211:8848#0113英国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.18.5.163:8848#0113卡塔尔 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.58.159.18:8848#0113美国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.194.227.32:8848#0113台湾 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.220.163.233:8848#0113香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.88.145.21:443#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.89.145.123:443#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.90.11.23:443#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.94.25.109:443#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.94.52.140:443#0113美国 
trojan://vzhXXZVw@36.150.215.220:48544?flow=&security=tls&sni=36.150.215.220&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113香港 
trojan://vzhXXZVw@36.150.215.222:12524?flow=&security=tls&sni=36.150.215.222&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDExM+azouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://55520747-311e-4015-83ce-be46e2060ce3@4.255.56.137:443?flow=&encryption=none&security=tls&sni=uxf.vs2024.us.kg&type=ws&host=uxf.vs2024.us.kg&path=/uxf.vs2024.us.kg&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.206.222.22:443#0113日本 
ss://YWVzLTI1Ni1nY206ZGZjNzg1OTM4MDhkNGY2OA==@45.130.147.138:16112#0113俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://dongtaiwang.com@46.17.41.189:50717?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0113俄罗斯 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@46.183.184.60:989#0113克罗地亚共和国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozNTUzMywic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhYmNhODYyNi0yMTZjLTQ3NDktOTJhOS1hZGJmM2NiZGEzYzYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL2hxelh5eXJMTzNlaWRlb3FyS0o1U0EiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://b76d7483-c4a2-4193-a068-ab303bee666c@5.180.253.233:14585?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/tdQoc0SEYmmdt&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
trojan://2cc669af-8ebf-4c8c-af72-9255a3547708@5.180.253.233:37413?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/PUocdh&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
trojan://abca8626-216c-4749-92a9-adbf3cbda3c6@5.180.253.233:45918?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/o76jGk2YOFFdLeuXVVIHN&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0ODYzMiwic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJiNzZkNzQ4My1jNGEyLTQxOTMtYTA2OC1hYjMwM2JlZTY2NmMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL05ZajFoY3ZCcnBpVmN6WGVHVE9LWGpCUFZBSkciLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://09762e27-f941-4dea-a3aa-68c5cf6e8329@5.180.253.233:34884?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/zY3ga07TDIe5&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoyODEzOSwic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlOGQxODkwOC1mMGJhLTQ5NmQtOTNkNy1iNjk0YjE2MjAyOWEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL0ZudzQwN1pVY3hMQnNTbEdKaTgiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NjgyNSwic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhOGI2ZjBmOC0xZGJhLTQ1YjgtYWNhOC1iNjBmNWQ3NTNkOTUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL1FGbyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InN3ZGlzdC5hcHBsZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MmNjNjY5YWYtOGViZi00YzhjLWFmNzItOTI1NWEzNTQ3NzA4QDUuMTgwLjI1My4yMzM6NDMwOTY6d3M6L3BUWTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0113德国 
vless://e8d18908-f0ba-496d-93d7-b694b162029a@5.180.253.233:18842?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/VGTunvxH8iXDCpHP&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozODI1NSwic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlZTYxM2MyMy01NDdkLTQ0NzYtOTEwNy1iNDNkMzM2MGJkYTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiLzdtcmdOVWkwNEFyTGNDaXRqbUlsIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3dkaXN0LmFwcGxlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://3c1712d3-5262-46ce-bf03-3fcec59b2c12@5.180.253.233:51128?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/mMUuxvvNh3m2&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NDMwLCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjA5NzYyZTI3LWY5NDEtNGRlYS1hM2FhLTY4YzVjZjZlODMyOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic3dkaXN0LmFwcGxlLmNvbSIsInBhdGgiOiIvVHpNR0s3d1RxT0E2UCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InN3ZGlzdC5hcHBsZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://2cc669af-8ebf-4c8c-af72-9255a3547708@5.180.253.233:31972?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/0T4fj50Da&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZThkMTg5MDgtZjBiYS00OTZkLTkzZDctYjY5NGIxNjIwMjlhQDUuMTgwLjI1My4yMzM6NDYzNjc6d3M6L3QzVFYzMk1vbDg6c3dkaXN0LmFwcGxlLmNvbTpub25lOnRsczpzd2Rpc3QuYXBwbGUuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozODY0OCwic2N5IjoiYXV0byIsInBzIjoiMDExM+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0ZTViYTA3Ni1kZjcwLTQxZGUtYWY3Ny1lYjdkNTU5NWNmMWYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL0k3IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3dkaXN0LmFwcGxlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://e8d18908-f0ba-496d-93d7-b694b162029a@5.180.253.233:65041?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/xeoVPAhtG6gq0kWNQrR8rcHn0XG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
hysteria2://jOIQlQeu6Dr2S8nNd3KbWnOr9rXVPgSNx3@5.180.253.233:31457?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=0TZocFD68AYt3qEL3hMl6KkQkM1nN3AC0Ul&os=#0113德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDk3NjJlMjctZjk0MS00ZGVhLWEzYWEtNjhjNWNmNmU4MzI5QDUuMTgwLjI1My4yMzM6NDI1MTQ6d3M6L0hodHk0dHY1REFFRWhOTjRRNTdCMmhoZkVZVTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0113德国 
hysteria2://nZubKitZaiTluI4uOOChjjt@5.180.253.233:51356?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=Bnk1ibZbyY1kOASu9yQ&os=#0113德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YWJjYTg2MjYtMjE2Yy00NzQ5LTkyYTktYWRiZjNjYmRhM2M2QDUuMTgwLjI1My4yMzM6NjM5MTU6d3M6L1luNE1sdGRraEpPTUMyUW53aDpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0113德国 
vless://4e5ba076-df70-41de-af77-eb7d5595cf1f@5.180.253.233:36393?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/NFCAksdlm9rUolG2da&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
hysteria2://tRGsPx3KRcgiWLWtIsy5HNu@5.180.253.233:27016?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=APahzFBbvrcmWnEkES0QjMPEzvApwYkxQ&os=#0113德国 
vless://abca8626-216c-4749-92a9-adbf3cbda3c6@5.180.253.233:53674?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/KEVPLATcoECbdpcuJ8h4ocQZ6lS&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YThiNmYwZjgtMWRiYS00NWI4LWFjYTgtYjYwZjVkNzUzZDk1QDUuMTgwLjI1My4yMzM6NDQ5OTc6d3M6L2FJRnMyWHlWTmhKNTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0113德国 
hysteria2://A9WyLgW8Bci5ECw5xmTH3pyfT7Qv@5.180.253.233:50366?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=e42EoD3M00uiqY5Gg2cwavS&os=#0113德国 
trojan://a8b6f0f8-1dba-45b8-aca8-b60f5d753d95@5.180.253.233:28024?flow=&security=tls&sni=swdist.apple.com&type=ws&header=none&host=swdist.apple.com&path=/oNm40r3vFhgB1zBuCY3w&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
hysteria2://FBBDnJTaKOBVkpA4NLwwJ0xTaZS9Tvuozo30@5.180.253.233:30912?insecure=1&sni=swdist.apple.com&alpn=&fp=&obfs=salamander&obfs-password=XdasqYtROh4rDlzkJZMPdePwIEjpD&os=#0113德国 
vless://5c533153-975a-4c4e-a3a2-c7f25446b0cd@5.180.253.233:42818?flow=&encryption=none&security=tls&sni=swdist.apple.com&type=ws&host=swdist.apple.com&path=/2zDw13TagRwLgu9IiB3A&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMzkuMjUyLjIwNCIsInBvcnQiOjU1ODk5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6Ijc5MWE5YWFkLTFhOGItNDM1ZC04NjJlLTYyN2Y0MTAyNWQ3MyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@51.81.36.172:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@57.180.61.213:443#0113日本 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0113英国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0113美国 
hysteria2://18240b2dfdd76484@70.34.207.153:443?insecure=1&sni=70.34.207.153&alpn=&fp=&obfs=salamander&obfs-password=d2648ec2&os=#0113瑞典 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp6VVF2RmlvYWU3S3pBWjJHQ01nTnVt@83.147.216.173:9848#0113英国 
ss://YWVzLTI1Ni1nY206TU1SVElZVkVDTjMzMDE4VA==@8tv68qhq.slashdevslashnetslashtun.net:18001#0113日本 
ss://YWVzLTI1Ni1nY206TkZZRFZYRTNETVdJMk0zVw==@8tv68qhq.slashdevslashnetslashtun.net:15005#0113香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjkyLjI0Mi4yMjAuMjIiLCJwb3J0IjozNzg4NSwic2N5IjoiYXV0byIsInBzIjoiMDExM+Whnua1pui3r+aWryIsIm5ldCI6InRjcCIsImlkIjoiOGRlZTE5YWItNTBjZS00ZDA2LWJlNDItNWU1M2M4OTg5Y2NjIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://2d7c7aa5-364a-4dbb-937a-f8e4f5f73007@94.131.111.195:443?flow=&encryption=none&security=tls&sni=de4.connecton.surf&type=ws&host=de4.connecton.surf&path=/vless&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@94.250.246.200:8080?flow=&encryption=none&security=tls&sni=a.mifeng.us.kg&type=ws&host=a.mifeng.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113岛 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@95.164.116.22:2501?flow=&encryption=none&security=tls&sni=a.mifeng.us.kg&type=ws&host=a.mifeng.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113新加坡 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@95.164.51.24:2501?flow=&encryption=none&security=tls&sni=a.mifeng.us.kg&type=ws&host=a.mifeng.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@api.namasha.co:443#0113阿拉伯酋长国 
vless://6657eaa4-6e21-4fd1-9a7f-157b23236aa4@bbq3.kuailejc.xyz:2052?flow=&encryption=none&security=&sni=jjjp.kuailejc.xyz&type=ws&host=jjjp.kuailejc.xyz&path=/kuaile2024&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113日本 
vless://4d8426b2-0af1-4eb5-a231-b62152d7b9b9@cloud.xmsvx.com:443?flow=&encryption=none&security=tls&sni=live.989bull.com&type=ws&host=aft.vc&path=/TorVipxyy%3Fed%3D2048fp%3Dchrome&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113德国 
vless://4d8426b2-0af1-4eb5-a231-b62152d7b9b9@cloud2.xmsvx.com:80?flow=&encryption=none&security=&sni=afc.fi&type=ws&host=afc.fi&path=/AfkNFgg%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113芬兰 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@cmc6.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc6.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113越南 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmMTZkMzc1Mi03YmFlLTQ3NGUtODdkYy1mODkyZGYyY2FlYWY=@ctmm.gscloud.bond:31620#0113新加坡 
vless://95f176dc-a297-5782-8760-9c964c27a528@faculty.ucdavis.edu:443?flow=&encryption=none&security=tls&sni=faculty.ucdavis.edu&type=ws&host=ELiV2--ELENA.COM&path=/%40mobilesignal----%40mobilesignal----%40mobilesignal----%40mobilesignal----%40mobilesignal----%40mobilesignal----%40mobilesignal----%40mobilesignal%3Fed%3D443ed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113捷克 
vless://1d0926e1-9fd3-4a48-8dd5-fa73928723f9@jsxzcm.concubine.top:46029?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113香港 
vless://08b18b09-a414-4a00-b17f-6da9cce559c7@jsxzcm.concubine.top:14627?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113香港 
vless://d028d7ab-4d81-4be8-838b-fd081bb1a5ba@lactation.ucdavis.edu:443?flow=&encryption=none&security=tls&sni=lactation.ucdavis.edu&type=ws&host=speedtest.net.ftp.debian.org.1.2.3.a.s.m.kkkkkkk.netspeedtest.net.ukwa.njsdl.ir&path=/vless&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113直布罗陀 
trojan://e279c494-c426-443a-a034-a04516409242@naiu-jp.05vr9nyqg5.download:13012?flow=&security=tls&sni=cloudflare.node-ssl.cdn-alibaba.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113日本 
vless://d7a6f3c2-5c25-46d9-bf7d-2b0e8cf1703d@phx-plus-1ddns.faforex.eu.org:18443?flow=&encryption=none&security=reality&sni=www.tesla.com&type=tcp&host=&path=&headerType=none&alpn=&fp=edge&pbk=8233FxCRw1a_aCJ8d1HwHBMD_fABUNNW7rsrFe3vK0s&sid=e6658462&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113美国 
vmess://eyJ2IjoiMiIsImFkZCI6InByaW1lci5pYmlsaWJpLmxpIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTEz5rOV5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImU1ODUyMzkzLWNhNTItNGM5MC1hMjM3LWQ2M2NiYmI1N2YyMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoibG9raS5vcmFjbGUiLCJwYXRoIjoiL2ZhcmNyeT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1nY206RkFKVDI2UElNN0NCNzFPWg==@qh62onjn.slashdevslashnetslashtun.net:16003#0113新加坡 
trojan://38571ca6-6692-4559-b901-0bc5826b7661@ru0195.alibabaokz.com:60194?flow=&security=tls&sni=ru0195.alibabaokz.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113俄罗斯 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@series-a2-mec.varzesh360.co:443#0113阿拉伯酋长国 
vless://f06e3012-30bc-56e2-ae73-74b7a6f5fe91@speedtest.net:80?flow=&encryption=none&security=&sni=hajlab.ucdavis.edu&type=ws&host=tg.ELIV2RAY.IR&path=/eli&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0113塞浦路斯 
ss://YWVzLTI1Ni1nY206WVBOTkJYR1JOQ0FYQjlONw==@ti3hyra4.slashdevslashnetslashtun.net:15010#0113香港 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:571#0113美国 
ss://YWVzLTI1Ni1nY206RDU2UlA0STVFMUNXTEFFMw==@w72tapyb.slashdevslashnetslashtun.net:18016#0113日本 



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
