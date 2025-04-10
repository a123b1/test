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

vless://99b7f7d7-0c5f-463c-8f3c-548e15f5ae28@91.107.244.16:443?flow=&encryption=none&security=reality&sni=mw8.niassa.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=7Dd-Z14Mxvy_CJmFe5Q-StNR2ZloyDeMAC6MEVSq4yg&sid=e9&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://c71464ab-6abf-41b8-ac35-323b82fa24db@www.speedtest.net:2086?flow=&encryption=none&security=&sni=&type=httpupgrade&host=www.isvpy.ir&path=/telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn-telegram-%40ISVvpn%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://e423b953-f182-4353-ab41-276deea064d0@95.81.86.61:44402?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409法国 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2020?insecure=0&sni=ua01.akebi.cc&alpn=&fp=&os=#0409乌克兰 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2003?insecure=0&sni=is01.akebi.cc&alpn=&fp=&os=#0409以色列 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0409以色列 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0409孟加拉国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0409斯洛文尼亚共和国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0409新加坡 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0409新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQwOeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0409日本 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2005?insecure=0&sni=fr01.akebi.cc&alpn=&fp=&os=#0409法国 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0409法国 
hysteria2://dongtaiwang.com@195.154.33.70:59967?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0409法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0409波兰 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2006?insecure=0&sni=au01.akebi.cc&alpn=&fp=&os=#0409澳大利亚 
trojan://6040a753-e35b-4384-8713-96f3c639b621@104.21.69.41:443?flow=&security=tls&sni=kju84.890602.XYZ&type=ws&header=none&host=kju84.890602.xyz&path=/WxWOWO1YA9bs2HOmaeWimvT3&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
trojan://6040a753-e35b-4384-8713-96f3c639b621@172.67.204.22:443?flow=&security=tls&sni=kju84.890602.XYZ&type=ws&header=none&host=kju84.890602.xyz&path=/WxWOWO1YA9bs2HOmaeWimvT3&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjMxOTk4LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2000?insecure=0&sni=hk03.akebi.cc&alpn=&fp=&os=#0409香港 
hysteria2://dongtaiwang.com@108.181.5.133:15544?insecure=1&sni=apple.com&alpn=&fp=&os=#0409美国 
hysteria2://Telegram-SiNAVM-SiNAVM-SiNAVM-SiNAVM@sinavm.soft10.ir:443?insecure=1&sni=&alpn=h3&fp=&obfs=salamander&obfs-password=@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM-@SiNAVM&os=#0409塞浦路斯 
hysteria2://a914681a-8dda-4c98-8468-c313f5539b14@sg3.eyucdn.xyz:2056?insecure=1&sni=sg3.eyucdn.xyz&alpn=&fp=&os=#0409新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xLjExNyIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDA55be06KW/IiwibmV0Ijoid3MiLCJpZCI6IjIyNDc0Y2M0LTIyYTktNGM3NC1iYWU4LTQzZjA4YTFjNmVkNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMjAyNTA0MTAwODI2NDE0Njk0Ni5zMTUuY2hpYmFiYS5maWxlZ2Vhci1zZy5tZSIsInBhdGgiOiIvczE1Lmh0bWwiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://573ae74e-5eea-467a-abc1-fdc65b8aa4fa@aafrtpfxr.jpl04i9zjfegelp.5xfsur8v62.gosdk.xyz:22269?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0409日本 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDQwOemfqeWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.79.172.127:443#0409韩国 
ss://YWVzLTI1Ni1nY206NzUxVTNUNVBQQVZXVk1SMg==@206.245.211.12:19002#0409英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpkMzE2ZmNhMy1lNGNhLTQ3NzQtODIzMC0yNGE4ZmI5Zjk5ZjY=@120.234.255.106:26912#0409香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk02.x.quickcht3.club:52612#0409香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.78.247.197:443#0409韩国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.223.20.79:989#0409台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4Ni4xOTAuMjE1LjE5MyIsInBvcnQiOjIyMzI0LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA555Ge5aOrIiwibmV0IjoidGNwIiwiaWQiOiIwNDYyMWJhZS1hYjM2LTExZWMtYjkwOS0wMjQyYWMxMjAwMDIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://dee29869-ae36-4504-89f5-8f06b7dc7a6a@94.159.107.136:1443?insecure=0&sni=de2.587458.xyz&alpn=&fp=&os=#0409德国 
hysteria2://dongtaiwang.com@51.159.226.1:61770?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0409法国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.182.61:8388#0409香港 
vless://103104c5-a3f5-4c48-8d8f-a72a56959799@104.17.92.98:443?flow=&encryption=none&security=tls&sni=ZyzZzoAo.pUTaTA.EU.Org&type=ws&host=zyzzzoao.putata.eu.org&path=flow%3D-udp443&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409 
hysteria2://dongtaiwang.com@46.17.41.5:12904?insecure=1&sni=apple.com&alpn=&fp=&os=#0409俄罗斯 
hysteria2://dongtaiwang.com@46.29.163.171:35751?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0409俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6IjAzZDkyOWVmLXN1azlzMC10Y21kdHMtMW1tdTYuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDnmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjJlZThmODMwLTA5ZTItMTFmMC05MGUyLWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://073d062a-3170-4e8c-9123-aaa32155152d@111.119.207.186:29831?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0409新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjZmMzE2MDcxLXN1azlzMC1zd3R6YTktMXE5MXAuY201LnA1cHYuY29tIiwicG9ydCI6MTcyMzEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDnmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6ImMxMWZmNTBjLWY1ODItMTFlZS05NGRmLWYyM2M5MTY0Y2E1ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://fb8812ae-dcb5-11ef-a57d-f23c9313b177@90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk:443?insecure=0&sni=90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk&alpn=&fp=&os=#0409美国 
hysteria2://3c461e2c-9d13-11ef-8563-f23c913c8d2b@4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net:8443?insecure=0&sni=4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
hysteria2://4e84400e-f4bc-11ef-81b7-f23c932f2c32@57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk:443?insecure=0&sni=57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk&alpn=&fp=&os=#0409美国 
hysteria2://82efba2c-f420-11ef-9529-f23c93141fad@d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk:443?insecure=0&sni=d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk&alpn=&fp=&os=#0409美国 
hysteria2://b72ba5d5-2d5e-45b7-93b5-236d343baa7c@164.152.19.229:47262?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0409美国 
hysteria2://be8ba532-0dcf-11f0-9a65-f23c9164ca5d@8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net:8443?insecure=0&sni=8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
hysteria2://564b440a-700f-11ee-a90c-f23c9313b177@71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk:443?insecure=0&sni=71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk&alpn=&fp=&os=#0409美国 
hysteria2://8de795d2-a06f-11ed-8edf-f23c913c8d2b@bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net:8443?insecure=0&sni=bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjZlMDBkNDEwLXN1a3cwMC1zdnhydDItNjNicC5iLmZvc2FudC5jb20iLCJwb3J0IjozNjk1LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI5MmIyYTNkNC1mMzUzLTExZWYtYjcxNC1mMjNjOTMxMzZjYjMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
hysteria2://2ee8f830-09e2-11f0-90e2-f23c913c8d2b@5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net:8443?insecure=0&sni=5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
hysteria2://7af3db60-b2d9-11ef-88ab-f23c913c8d2b@b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net:8443?insecure=0&sni=b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net&alpn=&fp=&os=#0409美国 
hysteria2://61e5f38d-87f8-4f51-854d-b2aaef51e2f9@92.112.126.122:53917?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0409乌克兰 
vless://b4ed05e0-34a7-4b77-89fe-01172ff58f59@mrconfigchannel.hajalii.com:2086?flow=&encryption=none&security=tls&sni=mrconfigchannel-cdn.hajalii.com&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@219.76.13.180:443?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozOTAzOSwic2N5IjoiYXV0byIsInBzIjoiMDQwOeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MjU1MCwic2N5IjoiYXV0byIsInBzIjoiMDQwOeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NDI4OTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDnmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://61e5f38d-87f8-4f51-854d-b2aaef51e2f9@107.172.235.75:20186?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0409美国 
vmess://eyJ2IjoiMiIsImFkZCI6InVzMTAtMDguODkwNjA2Lnh5eiIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjU3NmM4MWI2LTQ5NzYtNGZlMy1iMWE5LTA1YTljMzAyZTk4ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXMxMC0wOC44OTA2MDYueHl6IiwicGF0aCI6Ii9TTndOZHVudzI4bFZ6dG9wdzkwZW9YZWwiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1czEwLTA4Ljg5MDYwNi54eXoiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InVzMTAtMDkuODUyMjI0LmdnZmYubmV0IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjU3NmM4MWI2LTQ5NzYtNGZlMy1iMWE5LTA1YTljMzAyZTk4ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXMxMC0wOS44NTIyMjQuZ2dmZi5uZXQiLCJwYXRoIjoiL1NOd05kdW53MjhsVnp0b3B3OTBlb1hlbCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVzMTAtMDkuODUyMjI0LmdnZmYubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://18d8ce6f-a27c-461e-ada8-a7d0a97a023b@hyun.cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=ad.oldcloud.online&type=ws&host=ad.oldcloud.online&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409安道尔 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@192.9.236.144:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://18d8ce6f-a27c-461e-ada8-a7d0a97a023b@104.19.48.236:443?flow=&encryption=none&security=tls&sni=ad.oldcloud.online&type=ws&host=ad.oldcloud.online&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409安道尔 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@176.105.253.98:443?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@51.81.37.15:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://0cda5f7e-cc55-4ff2-8ad8-268b9b99dd01@104.21.77.44:443?flow=&encryption=none&security=tls&sni=Us6-03.890603.XyZ&type=ws&host=us6-03.890603.xyz&path=/GuJUq5kZ2d6MQzxVoMQ&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
trojan://Aimer@107.172.8.109:443?flow=&security=tls&sni=epccy.ambercc.filegear-sg.me&type=ws&header=none&host=epccy.ambercc.filegear-sg.me&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
trojan://Aimer@23.95.248.118:443?flow=&security=tls&sni=epccr.ambercc.filegear-sg.me&type=ws&header=none&host=epccr.ambercc.filegear-sg.me&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vmess://eyJ2IjoiMiIsImFkZCI6InM0LmRiLWxpbmswMS50b3AiLCJwb3J0IjoyMDUyLCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTItOTYtMjAyLnM0LmRiLWxpbmswMS50b3AiLCJwYXRoIjoiL2RhYmFpLmluMTA0LjE2LjIyOS4xNiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IjEwMC0yLTk2LTIwMi5zNC5kYi1saW5rMDEudG9wIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://78905d87-0266-4825-868d-3069e88d1201@zula.ir:2053?flow=&encryption=none&security=tls&sni=all22.kikforwindows.com&type=ws&host=all22.kikforwindows.com&path=/containers/de&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@192.227.247.49:2083?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
trojan://Aimer@192.227.247.49:2083?flow=&security=tls&sni=epccy.ambercc.filegear-sg.me&type=ws&header=none&host=epccy.ambercc.filegear-sg.me&path=/%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://eb50d091-51ed-4f89-bc4e-8b04320585d7@141.193.213.20:2096?flow=&encryption=none&security=tls&sni=premium.vkehi.shop&type=ws&host=premium.vkehi.shop&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409新加坡 
vless://eb50d091-51ed-4f89-bc4e-8b04320585d7@141.193.213.21:2096?flow=&encryption=none&security=tls&sni=premium.vkehi.shop&type=ws&host=premium.vkehi.shop&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409新加坡 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@104.129.166.131:8443?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@65.75.194.43:10511?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDQwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk01.x.quickcht3.club:52611#0409香港 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@47.76.130.197:60001?flow=&encryption=none&security=tls&sni=edccr.aimercc.filegear-sg.me&type=ws&host=edccr.aimercc.filegear-sg.me&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
trojan://%40NoForcedHeaven%40NoForcedHeaven%40NoForcedHeaven@195.133.52.153:8443?flow=&security=tls&sni=ru2.asc-sam.io&type=tcp&header=http&host=ru2.asc-sam.io&path=&alpn=h3%2Ch2%2Chttp/1.1&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA56aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpkMzE2ZmNhMy1lNGNhLTQ3NzQtODIzMC0yNGE4ZmI5Zjk5ZjY=@120.234.255.61:10239#0409香港 
trojan://telegram-id-privatevpns@34.241.39.28:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409爱尔兰 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@152.69.209.132:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
trojan://telegram-id-directvpn@13.216.192.206:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0409美国 
trojan://33fe5d7f-c9c1-4fd3-a2db-d0f3db6e5fba@tro-us02.gproxy.gratis:443?flow=&security=tls&sni=tro-us02.gproxy.gratis&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://35f591c6-0932-4c68-a831-4fe6ecf00b85@170.64.171.83:36402?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409澳大利亚 
vless://35f591c6-0932-4c68-a831-4fe6ecf00b85@asoff.qwertyuioaasdfghjkzxcvbnmdfghvqsadwqewqeqwqsxqaztghbhjntgbrfded.top:36402?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409澳大利亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4OC4xMTQuOTcuNzkiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MDnms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiZWRiYjEwNTktMTYzMy00MjcxLWI2NmUtZWQ0ZmJhNDdhMWJmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJsaW5kZTA2LmluZGlhdmlkZW8uc2JzIiwicGF0aCI6Ii9saW5rd3MiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJsaW5kZTA2LmluZGlhdmlkZW8uc2JzIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://7c317161-5cf8-4cbc-811a-d1297c41bb23@yapc-1.afshin.ir:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=yapc-1.afshin.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409瑞士 
vless://7c317161-5cf8-4cbc-811a-d1297c41bb23@152.67.68.116:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=yapc-1.afshin.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409瑞士 
trojan://02926f9e-153a-42c8-8ecd-8fade7009ad1@144.22.250.122:443?flow=&security=tls&sni=golinkwuxian.top&type=ws&header=none&host=8888.golinkwuxian.top&path=/apple&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409巴西 
vless://8b04ca95-4b92-4622-96bb-4372d1f22913@91.107.176.168:443?flow=&encryption=none&security=tls&sni=mw7.transitkala.com&type=ws&host=mw7.transitkala.com&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@193.108.119.230:8080#0409德国 
vless://6f786c4e-6402-4269-98d3-c383fb1708da@204.10.194.78:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=yfnl1.xn--4gq62f52gppi29k.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://78905d87-0266-4825-868d-3069e88d1201@104.21.69.44:2053?flow=&encryption=none&security=tls&sni=all22.kikforwindows.com&type=ws&host=all22.kikforwindows.com&path=/containers/de&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://459b4a80-bd61-4ecd-a26b-e9c1809d9e45@agaungzhou01.bumbleshrimp.com:31800?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.nvidia.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=qhTzYYIgBzDLNYR79oxftqdo1kzL-1_hGJKfqrOliCY&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409香港 
vless://0d751e96-72bc-484b-8f0e-ceb8a733fba3@188.245.43.225:48046?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989#0409以色列 
trojan://VMhGp5wEIyCDf90T@gysz0000.dynu.net:38340?flow=&security=tls&sni=hk39.work.gd&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409新加坡 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@38.38.251.220:443?flow=&encryption=none&security=tls&sni=edccy.ambercc.filegear-sg.me&type=ws&host=&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@154.17.224.83:443?flow=&encryption=none&security=tls&sni=edccy.ambercc.filegear-sg.me&type=ws&host=&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://ee6774c0-9b19-4ff1-8b30-2da4b71977e2@221.144.200.91:12527?flow=&encryption=none&security=tls&sni=edccy.ambercc.filegear-sg.me&type=ws&host=&path=/%3Fed%3D2560%26proxyip%3Dts.hpc.tw&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409台湾 
vless://576c81b6-4976-4fe3-b1a9-05a9c302e98e@104.21.23.115:443?flow=&encryption=none&security=tls&sni=us10-04.852224.ggff.net&type=ws&host=us10-04.852224.ggff.net&path=/HlAPZV9g9xmyAVVtopw90eoXel&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://cd0e795a-4f26-4f8c-9981-ed8b7dcb6126@dfgtyupo.852224.ggff.net:443?flow=&encryption=none&security=tls&sni=DFGtYUpO.852224.gGFF.nEt&type=ws&host=dfgtyupo.852224.ggff.net&path=/ekUVEk0GkPbqU8RhisheV&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://c4fa89d4-fcb9-48ba-adbc-665181cc817f@135.148.98.5:443?flow=&encryption=none&security=tls&sni=147135010072.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImRmZ1R5dXBPLjg1MjIyNC5HZ0ZmLm5FdCIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDQwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjZDBlNzk1YS00ZjI2LTRmOGMtOTk4MS1lZDhiN2RjYjYxMjYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRmZ3R5dXBvLjg1MjIyNC5nZ2ZmLm5ldCIsInBhdGgiOiIvU3BYaWRhUkE5UGJxVThSaGlzaGVWIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZGZndHl1cG8uODUyMjI0LmdnZmYubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://d67cfeaf-b277-44ac-ab99-9dd02a7c5299@172.67.200.11:443?flow=&encryption=none&security=tls&sni=Hu9L7.890606.XyZ&type=ws&host=hu9l7.890606.xyz&path=/jAcfFDEOj85lz42MdhsCLV&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@135.148.163.90:443?flow=&encryption=none&security=tls&sni=147135001178.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@15.204.191.46:443?flow=&encryption=none&security=tls&sni=147135001178.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0MS4xMDEuMTIwLjcxIiwicG9ydCI6MjA1Mywic2N5IjoiYXV0byIsInBzIjoiMDQwOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiIzODFjYjZkMS02YWQ0LTQ5MDktODQ5NC1iOGQ3ODZjZjc4Y2UiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjE3NDQwMDc1Nzguc3BlZWQubWFtaGEuY2NjcC5mcmVlZmx5LnBwLnVhIiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIxNzQ0MDA3NTc4LnNwZWVkLm1hbWhhLmNjY3AuZnJlZWZseS5wcC51YSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@15.204.153.29:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://32561a76-b738-48b9-b3f2-37856346fbd8@mo.4056860.xyz:443?flow=&encryption=none&security=tls&sni=mo.4056860.xyz&type=ws&host=mo.4056860.xyz&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409澳门 
trojan://telegram-id-privatevpns@3.74.83.179:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3MC4xMTQuNDUuNTMiLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjQ5YjkwNDc1LTlmNDUtNDU4OS04ZGU0LWE2MDNmNGY2NTZhOCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXN0b3VjampuaWQxOHNqNnVzLmxvdmViYWlwaWFvLmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXN0b3VjampuaWQxOHNqNnVzLmxvdmViYWlwaWFvLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1Mi42OS4xOTcuNjAiLCJwb3J0IjoxMDY5LCJzY3kiOiJhdXRvIiwicHMiOiIwNDA55pel5pysIiwibmV0IjoidGNwIiwiaWQiOiJhYzhlMjZmZS04MTUwLTRiNjAtYWU2NC04MmZjNzdlYmEyY2YiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://0a44145f-59dc-4e5b-a233-677b97f5114c@135.148.237.61:443?flow=&encryption=none&security=tls&sni=147135011033.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
trojan://c6677829-5644-427a-996d-5ac4d3223c03@250407.jichang.my:29978?flow=&security=tls&sni=sydney2.678789.xyz&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409澳大利亚 
trojan://c6677829-5644-427a-996d-5ac4d3223c03@250407.jichang.my:34865?flow=&security=tls&sni=zurich.678789.xyz&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409瑞士 
vless://0a44145f-59dc-4e5b-a233-677b97f5114c@15.204.187.172:443?flow=&encryption=none&security=tls&sni=147135011033.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
vless://ea286109-d20f-415e-849e-4af20ab04b65@135.148.195.57:443?flow=&encryption=none&security=tls&sni=147135001195.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409美国 
hysteria2://epmU3PzZ62jEP0cBVY@45.82.121.195:49208?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=kI7UtVA4MEC3BlSNac&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.244.36:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.245.122:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.233.114:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
hysteria2://yoK9abYlzmSt55F6eIpMKsfUjYf@45.82.121.195:46105?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=fvIbtt8ylRF5SJUIqiVHeAu7hGO6&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.254.11:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.110.201:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjoyMjk2NCwic2N5IjoiYXV0byIsInBzIjoiMDQwOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIyYWI5Zjc4My03NjFiLTRmODgtODIyZi0zYjQwYjVkYjM2ZDIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIveHFrRmp1ZUlQMEZpajU/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5iaW5nLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://QZMiGl8J3jSOlidtiPCd2dnc6@45.82.121.195:3636?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=SxZJc5rAediXCC0seCI0PqVCe&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
hysteria2://ww1uAKR8WJ5PLbJSXJWZfqFKx3sY3B1hdJTWL@45.82.121.195:17868?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=ayzE70UDtgCSO5UF5x5Do5ZMkB&os=#0409德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6N2U4NmNiZWQtNjk1OC00OWVmLTljN2UtZjZiMGE0NDQ0OWI1QDQ1LjgyLjEyMS4xOTU6Mzk3Mzp3czovajdlV2RSaG13M1hkYXN1RkhBb2Y4d3pEdXlaViUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0409德国 
trojan://2fa6149d-3af6-418f-86b3-ba719d6ec9a8@45.82.121.195:32569?flow=&security=tls&sni=www.bing.com&type=ws&header=none&host=www.bing.com&path=/6xqBoVVOTeM%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.35.78:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://bec3a7a2-95d5-47b7-9e1e-831d8edd5fc4@45.82.121.195:20083?flow=&encryption=none&security=tls&sni=www.bing.com&type=ws&host=www.bing.com&path=/3eheAU58Jo0glH0yHJ%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.95.192:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.242.204:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.179.173:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
trojan://54690d9b-d0f0-4269-8504-87ad2dd6b669@45.82.121.195:8503?flow=&security=tls&sni=www.bing.com&type=ws&header=none&host=www.bing.com&path=/ZOl8dZaHdRHyVKWKQT70XsbP0i9XmnoW%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OTgzNGMwZGQtNzA2OC00ZWIxLTgxMWUtNjJhNjA4ZjFjN2FlQDQ1LjgyLjEyMS4xOTU6MTM5NzM6d3M6LzBFaGtrbjBQa3lQNTVKZ0hRUW1pOUF3WnZ0M2xCazVSJTNGZWQlM0QyNTYwOnd3dy5iaW5nLmNvbTpub25lOnRsczp3d3cuYmluZy5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.115:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xOTUiLCJwb3J0IjozNzgzMCwic2N5IjoiYXV0byIsInBzIjoiMDQwOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4MmYyOTgyOS0wNjFkLTQ3OGUtOGMwNy1hZDhlY2RiM2ZlYWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5iaW5nLmNvbSIsInBhdGgiOiIvaW1sP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuYmluZy5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.97.75:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
hysteria2://M6fKIMkZLAvdyJZKM0aEW9uNs@45.82.121.195:25686?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=dbUph9CMIgy629KH4&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.3:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.98.15:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.115.238:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
hysteria2://beCnBmTpUWkqWNmhsujjorgFrRRRUapc@45.82.121.195:37622?insecure=1&sni=www.bing.com&alpn=&fp=&obfs=salamander&obfs-password=HxuTklKoSkn9BhduQIOW9OsT&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.235.139:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.144:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzY2YTljOTctYTc2OS00MWUwLWJhYWEtZTE3NmVhNzU1YmUzQDQ1LjgyLjEyMS4xOTU6MTg5OTY6d3M6LyUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0409德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzVkMmJjODgtMThlOS00NDYwLWI4NTktNjkxMWUwMTAzNmMyQDQ1LjgyLjEyMS4xOTU6Mzk4NTE6d3M6L212cWhNVmpSQzBkSk1kNUhybSUzRmVkJTNEMjU2MDp3d3cuYmluZy5jb206bm9uZTp0bHM6d3d3LmJpbmcuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0409德国 
vless://2ab9f783-761b-4f88-822f-3b40b5db36d2@45.82.121.195:54247?flow=&encryption=none&security=tls&sni=www.bing.com&type=ws&host=www.bing.com&path=/Q8puPCmE89SsxxBE3qZOAF5v3IqYnZP%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0409德国 

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
