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

hysteria2://338ce171-d764-4610-8fd5-6688b0d321f0@132.226.162.10:30102?insecure=1&sni=&alpn=&fp=&mport=&os=#1117巴西 
hysteria2://338ce171-d764-4610-8fd5-6688b0d321f0@140.238.137.165:30102?insecure=1&sni=du.wish.ml&alpn=&fp=&mport=&os=#1117加拿大 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0MS4xMDEuMTIxLjMiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTExN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJkOTY3ZmZjYS1kZTkwLTRkYWEtYmQwMC1kNTI3ZTViYWUxMWYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Imdvb2dsZS53aGF0c2FwcC5zbmFwcC50b3JvYi5iYXNhbGFtLmxlb3Nob3BwaW5nNzcuaXIuIiwicGF0aCI6Ii8/QklBX1RFTEVHUkFNKEBBWkFSQkFZSkFCMSlUTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKVRNKEBBWkFSQkFZSkFCMSlUTShAQVpBUkJBWUpBQjEpVE0oQEFaQVJCQVlKQUIxKSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1Mi43MC45Mi42OSIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIxMTE36Z+p5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJiYjljMzk5My1hNGI5LTRkYWQtYWViOS1hYzg2MzcxYWU2OGIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJodHRwIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@178.239.123.216:24443?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560%26Telegram%F0%9F%87%A8%F0%9F%87%B3%40WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@178.239.123.216:24443?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@178.239.123.216:24443?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560%26telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@178.239.123.216:24443?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560%26telegram%40freecodes&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@178.239.123.216:24443?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4LjE0My4yNDguMTU3IiwicG9ydCI6NTM3ODQsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjNhNDgwYTdkLWE0YjMtNDZlMS1kNGM0LTA0MjU2Yjc3ZjA0NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiMTguMTQzLjI0OC4xNTciLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4LjE0My4yNDguMTU3IiwicG9ydCI6NTM3ODQsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjNhNDgwYTdkLWE0YjMtNDZlMS1kNGM0LTA0MjU2Yjc3ZjA0NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4yMjEuMjMuMjUxIiwicG9ydCI6Mjk0MzEsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjhiNzgzNjNlLTNjM2EtNDRhYi1mMGQ4LWYxM2Q5NTBjODU3MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://dd2f25b4c70689de8bc0f7fa9d6591cb@203.198.122.135:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117香港 
trojan://dd2f25b4c70689de8bc0f7fa9d6591cb@203.198.122.135:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwbDJYdFIwcHp3a25RT0d3ZXdid1h0UFlEdzF6bjlWdQ==@213.159.66.206:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1117巴西 
trojan://BxceQaOe@219.79.165.55:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117香港 
trojan://BxceQaOe@219.79.165.55:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjE2NC4xMzEuNzAiLCJwb3J0IjoyNDM1MSwic2N5IjoiYXV0byIsInBzIjoiMTExN+mfqeWbvSIsIm5ldCI6InRjcCIsImlkIjoiNGRiMjBkODItMGE2NS00MzJiLWMxNmItZDJhYWNmZTg4MDczIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjI0Ny4xMzQuMjEzIiwicG9ydCI6NTk1MTYsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjI5MDZlMTllLWM5OWYtNDU2ZS1iY2IzLWM1NDcyZmQ1OTRlNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjI0Ny4xMzQuMjEzIiwicG9ydCI6NTk1MTYsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjI5MDZlMTllLWM5OWYtNDU2ZS1iY2IzLWM1NDcyZmQ1OTRlNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiNDMuMjQ3LjEzNC4yMTMiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxN1pET1JXSWxpUUh1TzZXUkdIQ2hYWU16ZFJ0QVlWUA==@45.14.245.2:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1117荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ3LjI0NS4xMDYuMTkzIiwicG9ydCI6MjIyODYsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6Ijg2NDYyMThmLWE2MDAtNGI3My04NzIxLWFhNWQ0NTY3ODE5ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ3LjI0NS4xMDYuMTkzIiwicG9ydCI6MjIyODYsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6Ijg2NDYyMThmLWE2MDAtNGI3My04NzIxLWFhNWQ0NTY3ODE5ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiNDcuMjQ1LjEwNi4xOTMiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://0507fbcd-b983-43a7-8e1d-2c561960ad4f@54d-bd0d-c3f111d0b879.664.qzz.io:443?flow=&security=tls&sni=54D-bD0D-c3F111D0b879.664.Qzz.Io&type=ws&header=none&host=54d-Bd0d-c3f111d0b879.664.QZZ.iO&path=/E2JXJM5geneWfr9noOhn&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
trojan://BxceQaOe@58.152.26.173:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117香港 
vless://00f02ab2-6f2d-449f-a089-d182a2fac59a@81.161.98.228:1443?flow=&encryption=none&security=tls&sni=cdn.filterai.ru&type=ws&host=cdn.filterai.ru&path=/websocketpl&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117保加利亚 
trojan://0507fbcd-b983-43a7-8e1d-2c561960ad4f@a76-4179-8a78-c8b78b3c00cb.664.qzz.io:443?flow=&security=tls&sni=A76-4179-8a78-c8B78B3C00Cb.664.QZz.iO&type=ws&header=none&host=a76-4179-8a78-c8B78B3C00cB.664.qzz.Io&path=/E2JXJM5geneWfr9noOhn&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vless://58a3efa1-94a6-4e03-b5b7-c4a398585979@antimage.fonixapp.org:29000?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=lbo1jWRdkDrMcBkRcVXUBGoEbOun23CERmtkOWDS7Go&sid=a941df4328&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117奥地利 
vmess://eyJ2IjoiMiIsImFkZCI6ImNmLmZvdmkudGsiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjExMTfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiYmY2NzQzN2UtNmM5MC00NWNhLWFiYzItYzcyNDBhNWNlMmFhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJmb3hsdXguZm92aS50ayIsInBhdGgiOiIvZWlzYXNxYSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://90c6cd82-5fad-4d31-9909-8b53b2ea15f4@dwarvensniper.fonixapp.org:21763?flow=xtls-rprx-vision&encryption=none&security=reality&sni=stackoverflow.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=RZax6slpjvfUJ46gHwIfIBApUSapP7i7yPz1f1WwBXE&sid=a193&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1117奥地利 
vless://f99cc0f1-d1a3-45f9-a13b-b33c8d3e0f10@greenwolf.fonixapp.org:30268?flow=xtls-rprx-vision&encryption=none&security=reality&sni=indeed.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=GyvksSpuOucs7XsCfiq2yRn3cxVN_Y8b3Zippb_mYCM&sid=50bcccfb&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1117奥地利 
trojan://a0d6e36b-0233-4985-bc99-db6ed83b8dd8@krhtybay.catcat321.com:20026?flow=&security=tls&sni=iepl.ruz1.cat.bilibili.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117俄罗斯 
vless://53f0bca8-f170-4ef7-8031-c7d441189dbf@norman.ns.cloudflare.com:443?flow=&encryption=none&security=tls&sni=638989641550992554.sonata-amshx.info&type=ws&host=638989641550992554.sonata-amshx.info&path=/cahttingws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowMTRlOTBkZi1hM2VlLTQ2NTQtYTlmNi1kMTE4ZTAyZGQwMmE=@sl.fgmcx.top:41047?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1117新加坡 
vless://f36312ed-c887-48a5-a803-22ca16a153c5@tuskar.fonixapp.org:38390?flow=xtls-rprx-vision&encryption=none&security=reality&sni=smallpdf.com&type=tcp&host=&path=&headerType=none&alpn=&fp=firefox&pbk=a3usSjtSaH2XGzG5oi3oqPYKlhsJOmmJYI4nitX1rn8&sid=2b&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1117奥地利 
vless://393040206-client-475@usa1.tunnelx.space:2087?flow=&encryption=none&security=&sni=ws.usa1.tunnelx.space&type=ws&host=ws.usa1.tunnelx.space&path=/assets/img/banner_v3.webp/%23%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL%2C%40V2RAY_SPATIAL&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMTExN+iNt+WFsCIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4yMzQiLCJwb3J0Ijo4NDA2LCJzY3kiOiJhdXRvIiwicHMiOiIxMTE35b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjE2ZDhkZTIwLWU5ZmUtNDM5Yy04OTkwLTA0MDU1NTYzZDU2MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY20xLmF3c2xjbi5pbmZvIiwicGF0aCI6Ii9pa3VCN2dpYzl3d3RrRVpFOW9LRFVHZ3hSVnllNj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiY20xLmF3c2xjbi5pbmZvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjM3LjExNC40OS4yMzQiLCJwb3J0Ijo2MTg4Niwic2N5IjoiYXV0byIsInBzIjoiMTExN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJkMzRhZDNhMC03MTcyLTRmZjItYjYyNy01OTlmNjZlYzBkOGMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNtMS5hd3NsY24uaW5mbyIsInBhdGgiOiIvZDg3RHNPTTRRZjhPdldDQ3puMjBpMDdyP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJjbTEuYXdzbGNuLmluZm8iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.65.243:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.29.71:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.21.115.63:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@198.41.196.251:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
hysteria2://0ixfJe5TCWmntJpMMutDPmz@37.114.49.234:12543?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=NMPRzZDe3sWSXcJiOhSSbIXDuQSs&mport=&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@162.159.252.125:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
hysteria2://OzeBKK7RGeN9m0Fdu@37.114.49.234:19979?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=4F4PNjFEZRBmp1Eo9xtD0LP0J0YJu78K&mport=&os=#1117德国 
trojan://d34ad3a0-7172-4ff2-b627-599f66ec0d8c@37.114.49.234:31363?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/gTlb0sMrPDDc%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@162.159.192.187:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.4.50:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
trojan://cdd671d1-18c0-4581-a8ec-01d24673cdc0@37.114.49.234:21992?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/rZYfkJjqiKi%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
hysteria2://CA5HiSfFZtukC9Q2r6I@37.114.49.234:48246?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=iGLeFxna3ss4QqTJcXf2n6t&mport=&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@173.245.58.127:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
hysteria2://BQxzZppGYcsDXVpIu@37.114.49.234:26102?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=EBgBw91iQrTxWk9MI5mFciz7KDzLt7c3S9j&mport=&os=#1117德国 
anytls://PjQ4USQvHoROPWqIBXDLwTK0JbptzvhjALId@37.114.49.234:60239?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#1117德国 
hysteria2://hDtb38j2IArH4laSpMIR81oPRYdbawHCK3V45Lj5@37.114.49.234:2756?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=ywZTis80D4odwkZFa5BWhQCFBqj&mport=&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.87.206:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@188.114.98.202:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
trojan://00dae2de-d3a0-43ae-b66d-6e05621b1b5c@37.114.49.234:13377?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/J3OzYUZ%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
hysteria2://iQagbAKtu4DmyvgCNeVrkM0WTRZzgQD8a@37.114.49.234:6934?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=cJB7h8Mny8eyFXNZ4OnSU&mport=&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.6.183:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 
vless://5870db4f-8e2b-42f3-8998-774e6321c5d6@104.27.27.86:443?flow=&encryption=none&security=tls&sni=tie.vmkc9.netlib.re&type=xhttp&host=tie.vmkc9.netlib.re&path=/%3Ftg&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1117德国 


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
