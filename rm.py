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


vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTEzMOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ0Lm1lL3JpcGFvamllZGlhbiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTEzMOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTEzMOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://3e3201b3-8d9a-4007-a7db-fcf00833e947@tw.518181.xyz:55518?insecure=1&sni=ovo.1234567890spcloud.com&alpn=&fp=&mport=&os=#1130台湾 
hysteria2://3e3201b3-8d9a-4007-a7db-fcf00833e947@th.518181.xyz:55518?insecure=1&sni=ovo.1234567890spcloud.com&alpn=&fp=&mport=&os=#1130老挝 
vless://2dfa740c-8069-4993-8b96-c3e5dc540593@nl5.ultima.foundation:22231?flow=xtls-rprx-vision&encryption=none&security=reality&sni=nl.ultima.foundation&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=gtur4bFCYQzGf7M6B40RpdBHl6g1epPNhJCMqKPoVng&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130奥地利 
vless://88ba0958-d6e8-4c7b-9a80-e5180c520989@istanbul.fonixapp.org:25059?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yelp.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=f8rRV7gssAlL-e8teb5xR9q1vRwRJ3pvORgscKSgPAM&sid=1ec404fc&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1130土耳其 
vless://e5603527-ac9b-4f69-906e-34bea11c5835@easygovpnkeys16.com:6093?flow=xtls-rprx-vision&encryption=none&security=reality&sni=eas1goauth.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=W91d6Qp8Avflj9K7rMYGGdhxV_W0Ds_FSu_c996zknk&sid=57e13c11bb421329&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vmess://eyJ2IjoiMiIsImFkZCI6ImUwMzQ5YTUyLXN2OGNnMC10N3VpbmYtaThpZS5oazMucDVwdi5jb20iLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTEzMOmmmea4ryIsIm5ldCI6IndzIiwiaWQiOiI5OTBlOGYzNC1iZDRmLTExZWYtYmRiOS1mMjNjOTFjZmJiYzkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJyb2FkY2FzdGx2LmNoYXQuYmlsaWJpbGkuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJicm9hZGNhc3Rsdi5jaGF0LmJpbGliaWxpLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6ImM1YjMzMWY2LXQ2bmdnMC10YWtzYXktMXRjdWYuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiMzk1MmE1MTQtZWFhNy0xMWVmLTk3ZGEtZjIzYzkxY2ZiYmM5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjNWIzMzFmNi10Nm5nZzAtdGFrc2F5LTF0Y3VmLmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://1c1023ac-3d16-494d-be09-65a248f49cd7@broodmother.fonixapp.org:49722?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yelp.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=eRuDPGgOwmAbFaNZtqzEfgflU4Jaj2MJNYwAQPkp32s&sid=23f89c&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vmess://eyJ2IjoiMiIsImFkZCI6ImIyZDVjYjIwLXN2MnNnMC10N3F5MjYtMTRnNzYuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiNDcyOWI0YzgtMTc5MC0xMWViLTg2ODQtZjIzYzkxM2M4ZDJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJiMmQ1Y2IyMC1zdjJzZzAtdDdxeTI2LTE0Zzc2LmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://2dfa740c-8069-4993-8b96-c3e5dc540593@at.ultima.foundation:22231?flow=xtls-rprx-vision&encryption=none&security=reality&sni=at.ultima.foundation&type=tcp&host=&path=&headerType=none&alpn=&fp=edge&pbk=gtur4bFCYQzGf7M6B40RpdBHl6g1epPNhJCMqKPoVng&sid=a9725715bf4c62ff&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130奥地利 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@98.70.151.190:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpTVnQ2WmlXelJJMVl4ZWlnNHhCWndpSk90NmNlWHdHYQ==@95.111.222.113:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130澳大利亚 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.23:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.23:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.220:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.95.220:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@85.193.92.242:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@83.147.255.67:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@83.142.30.4:2096?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTprMWRCT21PQjRvcWk3VW1wMzdhMWJR@82.38.31.179:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3LmFsaWJhYmEuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoiam9zcy5ncGoxLndlYi5pZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidHJvamFuLmJ1cmdlcmlwLmNvLnVrIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidHJvamFuLmJ1cmdlcmlwLmNvLnVrIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidGlhbmppdS5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@81.200.154.2:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@80.90.187.190:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@80.90.187.190:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@80.76.32.12:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@8.217.180.234:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://e258977b-e413-4718-a3af-02d75492c349@8.212.79.249:443?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vless://e258977b-e413-4718-a3af-02d75492c349@8.212.115.61:443?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjdmMDc0ZjYyLXN2NmhzMC10ZGg5dzctYWhzYi5oazMucDVwdi5jb20iLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTEzMOmmmea4ryIsIm5ldCI6IndzIiwiaWQiOiIyZTQyYzFlZS1hYWFhLTExZWMtYmI3NC1mMjNjOTE2NGNhNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJyb2FkY2FzdGx2LmNoYXQuYmlsaWJpbGkuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJicm9hZGNhc3Rsdi5jaGF0LmJpbGliaWxpLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjdjMWJkNTQ1LXN6OHNnMC10MG9wemktMTl4ZzEuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiZTFkZWU3YzAtY2ZmNy0xMWViLWE4YmYtZjIzYzkxY2ZiYmM5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI3YzFiZDU0NS1zejhzZzAtdDBvcHppLTE5eGcxLmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@77.221.157.32:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjY5ZjU2ODQ5LXQ2bmdnMC10ZDk1cWgtMWlzZWEuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiZDZhYmRiZGEtZmU5ZC0xMWVjLWJiNzQtZjIzYzkxNjRjYTVkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiI2OWY1Njg0OS10Nm5nZzAtdGQ5NXFoLTFpc2VhLmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@68.64.176.135:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=h3&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@68.64.176.135:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
trojan://BxceQaOe@58.152.53.8:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130香港 
trojan://BxceQaOe@58.152.18.95:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130香港 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@51.195.102.180:8443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@49.12.210.182:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@47.79.41.201:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://e258977b-e413-4718-a3af-02d75492c349@47.57.190.228:8388?flow=&encryption=none&security=tls&sni=www.x-aniu----sg.netlib.re&type=ws&host=www.x-aniu----sg.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130新加坡 
vless://e258977b-e413-4718-a3af-02d75492c349@47.57.190.228:8388?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vless://e258977b-e413-4718-a3af-02d75492c349@47.239.69.137:8440?flow=&encryption=none&security=tls&sni=www.x-aniu----sg.netlib.re&type=ws&host=www.x-aniu----sg.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxN1pET1JXSWxpUUh1TzZXUkdIQ2hYWU16ZFJ0QVlWUA==@45.14.245.2:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjM4LjU0Ljk4LjExMCIsInBvcnQiOjIwNTIsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpqazmnaXopb/kupoiLCJuZXQiOiJ0Y3AiLCJpZCI6IjY2NWQ5YjhmLTE1M2QtNDkwNy1hZGFjLWRlMTJhZmQ5Yzg1MSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://e258977b-e413-4718-a3af-02d75492c349@38.147.186.31:555?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
trojan://09e71e3b-1f9f-44ab-9a10-02e0e10e2f05@37.202.200.19:25010?flow=&security=tls&sni=37.202.200.19&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vless://6ec8234b-7192-4603-ac12-2b4bbc9c1113@37.120.191.120:54044?flow=xtls-rprx-vision&encryption=none&security=reality&sni=smallpdf.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=fNizRKQ3b7EsnXk0-aX1XyXM-kdNq6aoYWsOMRxG6Ug&sid=1f86&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://e258977b-e413-4718-a3af-02d75492c349@34.81.148.206:443?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpORFJ5U0lBQkFSYkVyTklWc0NOVmt5WUFIaUJ6aHZlVA==@23.95.75.146:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTptYmhxc1N0bkZRVDFjVFpZQ2RzbWt1Z0dVQzZHVDZycA==@213.159.67.124:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130西班牙 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@210.87.111.61:39738?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://aa7f42cc-616f-4550-9a87-4b85bb409121@210.87.111.61:39738?flow=&encryption=none&security=tls&sni=vless3.datatestvless.click&type=ws&host=vless3.datatestvless.click&path=/%3Fed%3D2560%26telegram%40wangcai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@206.189.25.65:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://00000000-0000-4000-8000-000000000000@203.239.249.99:10927?flow=&encryption=none&security=tls&sni=mot.gike.dpdns.org&type=ws&host=mot.gike.dpdns.org&path=/%40Marisa_kristi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.67:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.54:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@202.85.53.160:7000?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@20.235.105.146:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@194.35.119.49:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@193.124.18.13:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@193.124.18.13:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@193.123.90.82:12648?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130希腊 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp6d0JMTTZiQkU1WXh2d3ZuS2d4QXEzRXJYcHFNWXYyMA==@185.193.48.157:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130摩尔多瓦 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@185.103.252.54:2053?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzYiLCJwb3J0Ijo1OTAwMywic2N5IjoiYXV0byIsInBzIjoiMTEzMOS4reWbvSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://a00d89f6-ab7e-4e30-a5e5-54c701d62c93@178.236.16.98:35728?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=vhUFNoFcvtZAVMo8y5K5eU2V43m5q6yjmWIhp5RkFng&sid=69a2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130哈萨克 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@167.99.86.115:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@154.17.225.73:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPRGZ4aW9LMFZrS3hUZHBWUUo0cnY4SGdsQXUwdnp2Ng==@146.19.49.251:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://2d535288-d08e-4de4-b674-fd8cb3c6e4d3@141.227.172.96:56089?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130法国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@139.185.50.5:14594?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@139.185.34.131:443?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@129.150.49.58:18650?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
trojan://BxceQaOe@112.118.116.66:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpZUUNTS29DRjNRYXpXOFlsdkRCV0E0@109.71.246.210:56689?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130荷兰 
vless://5aba5b77-48eb-4ae2-b60d-5bfee7ac169e@108.162.198.11:2096?flow=&encryption=none&security=tls&sni=kuangbao.xiejiang.dpdns.org&type=ws&host=kuangbao.xiejiang.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130美国 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.85:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.80:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.76:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.64:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.42:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.34:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.30:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.235:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.229:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.228:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.213:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.154:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.114:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.113:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.105:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.104:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.74:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.56:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.35:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.248:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.246:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.239:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.235:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.233:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.222:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.198:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.192:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.191:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.188:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.185:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.181:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.173:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.156:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.142:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130越南 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.182.158:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0U2FDSWF6bGd1bVlrTThGa1B6bG13anB5V0JEWkZCaw==@103.106.3.82:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1130哈萨克 
vless://e258977b-e413-4718-a3af-02d75492c349@101.32.72.125:443?flow=&encryption=none&security=tls&sni=www.x-aniu-----jp.netlib.re&type=ws&host=www.x-aniu-----jp.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130日本 
vless://e258977b-e413-4718-a3af-02d75492c349@101.32.72.125:443?flow=&encryption=none&security=tls&sni=www.x-aniu---hk.netlib.re&type=ws&host=www.x-aniu---hk.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjBlN2YxMDE2LXN2YTc0MC10ZTB2MjgtMW1oNjcuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiZTFjN2ZiYmMtOTZiNi0xMWVmLTg1NjMtZjIzYzkxM2M4ZDJiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIwZTdmMTAxNi1zdmE3NDAtdGUwdjI4LTFtaDY3LmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjBhZWMwMjIyLXQ2bmdnMC10OXA3eWotMWlqaDUuaGszLnA1cHYuY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjExMzDpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiZjdkOTUzNjQtNjA3Yi0xMWVlLTkzYWYtZjIzYzkxMzY5ZjJkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIwYWVjMDIyMi10Nm5nZzAtdDlwN3lqLTFpamg1LmhrMy5wNXB2LmNvbSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://mQRLLpDFCEfSyvESEQSy67F0CPg2Y@45.82.120.208:16971?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=rXjH1Y5E3ncK1OOhoxKBO3m&mport=&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@103.21.244.112:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@103.21.244.89:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMDgiLCJwb3J0IjoxOTQ2Nywic2N5IjoiYXV0byIsInBzIjoiMTEzMOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI1YTk1ZDRmMS0xOWZmLTRlYTQtYjNiMi1iNGMyMDhkZmM4YTQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy55YWhvby5jb20iLCJwYXRoIjoiL3d0WDlMVXRlUG5rP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cueWFob28uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://znOWYd0JaWomHw4a4Y7bE34@45.82.120.208:58087?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#1130德国 
hysteria2://0CD6Tva29NTXT8gdG@45.82.120.208:17394?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=X25VSOGg1opEVKAVwMhQqh57DP6VzvyPAQz&mport=&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@198.41.215.192:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@162.159.18.195:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
anytls://GnB3t06qcLNjMytI55jvYYaM7p2qjYnmqaq@45.82.120.208:45004?insecure=1&sni=www.yahoo.com&alpn=h2&fp=&os=#1130德国 
vless://b2723b49-6164-4876-8554-5d7421eec89f@45.82.120.208:43966?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/b1pGo0ExHOZgE9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@104.16.42.49:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@104.16.228.174:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
hysteria2://ytgmNmFZsenIOR7n6raTtb33wYfshbw6cynVk@45.82.120.208:4369?insecure=1&sni=www.yahoo.com&alpn=&fp=&obfs=salamander&obfs-password=NgXQuYlx4QJGLLNfROu9yAA1k7TeyFzHF8hFtq&mport=&os=#1130德国 
vless://01008f22-1136-4ae8-ad82-a2a434782d7e@45.82.120.208:3028?flow=&encryption=none&security=tls&sni=www.yahoo.com&type=ws&host=www.yahoo.com&path=/SH0Duw89q730frfR2%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@173.245.59.70:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@104.24.46.117:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@173.245.49.233:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@173.245.59.153:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@198.41.196.251:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 
vless://a163ad4b-ab9c-4e12-9749-f3f493112a44@104.27.113.190:443?flow=&encryption=none&security=tls&sni=cake.ryalol.qzz.io&type=xhttp&host=cake.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fcrc32%3D3264f10a&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1130德国 



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
