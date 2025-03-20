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

vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xNi4xNTUuMTAiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTEwMy01OC0zOS5zMS5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbjEwNC4yNS4yNDkuMjE1IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xNi4xNTUuMTAiLCJwb3J0IjoyMDUyLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE5576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTEwMi0yNDctOTIuczEuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xMDQuMjUuMTc1LjEzNyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://85950277-f447-48f0-9ead-aaf6d5ff3cad@104.21.34.159:443?flow=&security=tls&sni=df6xxxx.2031.pp.ua&type=ws&header=none&host=df6xxxx.2031.pp.ua&path=/I4L1BP2DQVYmx5NYQ76MGGq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@107.172.235.75:29370?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0319美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDIwNTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDIsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6Ijc3MGVlNzMwLTI0NTAtNGUzYy1hNmM2LTM5MzJiZDMyYWZiZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@135.148.206.182:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTozYmY4YzVkYTEwZTAwMjRh@144.126.142.92:21448#0319美国 
trojan://SZAaY0CIRDey6OCSpS3Dl3F2nnDTYFqRS8aClceOwAyTwy39XxDz4FYXZO3AxRaEz2SlN@144.229.29.158:443?flow=&security=tls&sni=dessert.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
vless://c4fa89d4-fcb9-48ba-adbc-665181cc817f@15.204.151.74:443?flow=&encryption=none&security=tls&sni=147135010072.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://Yyjyl3Fwy6pSjTYSaCxg7Z0COIwBYxN38FwC3YBz44678OAypA87p2CEe53SaKel3pCDSZCZaeSaaZS@154.17.1.105:28335?flow=&security=tls&sni=printer.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://jnaO0CFYpYExOygqlESRplzewIaKSFpBaqXy3YX4xBC8KK9ja94Y4S8aS7zjq96XSxO7CDu5BCYFCZg@154.17.13.71:443?flow=&security=tls&sni=lnitak.starspace.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://lBSSFOalI3yXZDOAwADg9a8zTCexE6pjxeX4D3a0FgSSYRqlCyCOYcz83w3aYR3cTZDF8@154.17.20.103:443?flow=&security=tls&sni=length.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://2OnySp6YC3SZcF32XACEjlD5aDOqx9SeR6yRFDwEXAu3Fc8w3Z3Y4AqZ0OSzlN8NCeYIA@154.17.9.26:28333?flow=&security=tls&sni=bathtub.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.236.137.219:443#0319美国 
ss://YWVzLTEyOC1jZmI6c2hhZG93c29ja3M=@184.170.241.194:443#0319美国 
trojan://576c81b6-4976-4fe3-b1a9-05a9c302e98e@192.3.130.103:443?flow=&security=tls&sni=us10-01.iran2030.ggff.net&type=grpc&mode=none&host=&serviceName=i8oL7PsxV002zYFTmiIeg&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@192.9.236.144:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjIwNy45MC4yMzguMTM2IiwicG9ydCI6MjAwMTAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMzRhN2QwY2QtYjBiYS00NDBkLWFiNzgtODA0Nzc1MzAzYTExIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@23.132.228.217:20118?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0319美国 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.210.253.95:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.211.230.161:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.71.252:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.221.169.63:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.86.111.233:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.216.191:443#0319美国 
vless://0a44145f-59dc-4e5b-a233-677b97f5114c@51.81.18.62:443?flow=&encryption=none&security=tls&sni=147135011033.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.184.74.88:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.202.63.169:443#0319美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.218.61.43:443#0319美国 
vmess://eyJ2IjoiMiIsImFkZCI6IkxBMDQuODkwNjAzLlhZeiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImxhMDQuODkwNjAzLnh5eiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IkxhMDEuODE4MTg1LlhZWiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://ZI3OeTA9Clx3AFS78DejwENjaZAa3FSwSluxY3EOClyycDqyzpYD0a6DI2eS28q7X3NpC@aluminum.wireshop.net:28334?flow=&security=tls&sni=aluminum.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://2OnySp6YC3SZcF32XACEjlD5aDOqx9SeR6yRFDwEXAu3Fc8w3Z3Y4AqZ0OSzlN8NCeYIA@bathtub.homeofbrave.net:28333?flow=&security=tls&sni=bathtub.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://9FC33glcaEeYYTnOqOS9DOZgBZ5CDazy33SCS2j4Cz36A7AIN88uaKRx5xDyR8pxu3x4D@closet.homeofbrave.net:28332?flow=&security=tls&sni=closet.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://SZAaY0CIRDey6OCSpS3Dl3F2nnDTYFqRS8aClceOwAyTwy39XxDz4FYXZO3AxRaEz2SlN@dessert.taiwanesefood.link:443?flow=&security=tls&sni=dessert.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImxBMDEuODE4MTg1Lnh5WiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImxhMDIuODE4MTg1Llh5WiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://jnaO0CFYpYExOygqlESRplzewIaKSFpBaqXy3YX4xBC8KK9ja94Y4S8aS7zjq96XSxO7CDu5BCYFCZg@lnitak.starspace.link:443?flow=&security=tls&sni=lnitak.starspace.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://6qREZzexS5BDqFaSyzlwlBYXT8CDYOpcDIaeYaAC3X940A73OceAaRR32C3Sx6w9xgyCS@phooey.taiwanesefood.link:443?flow=&security=tls&sni=phooey.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://Yyjyl3Fwy6pSjTYSaCxg7Z0COIwBYxN38FwC3YBz44678OAypA87p2CEe53SaKel3pCDSZCZaeSaaZS@printer.wireshop.net:28335?flow=&security=tls&sni=printer.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://CAlpl3ZOpDFaS9E6Se0plFxu2x3I4eACOcqZSaY3ReS6CjZSCTNKDgEF73TDZ2aB9D3nD@soldier.homeofbrave.net:443?flow=&security=tls&sni=soldier.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
trojan://F7aCRp5cSNRqynagAa8IaX09TFRycpxllaXZeYzzpDeOa3CpXwwCS9awB7BNNeaqYY8aY9ASz8pZAZS@tubular.wireshop.net:443?flow=&security=tls&sni=tubular.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319美国 
ss://YWVzLTI1Ni1nY206UUYzNzdHR1EwMFJBVENNSw==@8tv68qhq.slashdevslashnetslashtun.net:21004#0319台湾 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@gafntaipei.duckdns.org:36019?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0319台湾 
trojan://7pE3OSjFe9xFey8YyCgaIaz3Zu2CORpananc34DRlgSyO83XTyNjC4xAIue30YKFCCDlx@sohtsa.taiwanesefood.link:443?flow=&security=tls&sni=sohtsa.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319台湾 
ss://YWVzLTI1Ni1nY206RjdYR0dOOU1QMERHUExJSQ==@w72tapyb.slashdevslashnetslashtun.net:21007#0319台湾 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@156.146.40.194:989#0319斯洛伐克 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0319斯洛文尼亚共和国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.215.250.172:443#0319新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.229.233.60:443#0319新加坡 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0319新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.138.125:443#0319新加坡 
trojan://8jqRgpyc5lEe34TzC9A8DuFD23aS3ZyCleIFuCxp3xOYnZRCeA3Oc3yCga8C2DKYBDaRp@18.142.45.201:443?flow=&security=tls&sni=mention.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MzkwMiwic2N5IjoiYXV0byIsInBzIjoiMDMxOeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0319新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.151.230.240:443#0319新加坡 
trojan://N5T0K3aYpYFSO4O3gnD73OcFwp6BCqCyCa3jlIxDXyZRDE282ljCASADaTN4CzZZYllFI@54.179.175.19:18333?flow=&security=tls&sni=pricing.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319新加坡 
ss://YWVzLTI1Ni1nY206SUhXTFlaU1NTWDRHU0tMQQ==@8tv68qhq.slashdevslashnetslashtun.net:16013#0319新加坡 
trojan://OCxO7za3SXnwpEacKD7AZxujyISD840CZgSCSFFp6Z3eXFeOZDyzlTy3lA8AgBea3SDEC@luber.protocolbuffer.com:443?flow=&security=tls&sni=luber.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319新加坡 
ss://YWVzLTI1Ni1nY206OWFjZmM1NzQtYWNjMy00YzJiLWFiM2ItNDkxZDQzYTZlYjgz@okanc.node-is.green:21115#0319新加坡 
trojan://AYA7NTRlglF7qI9qF83a33aZugxSl34OSDcCZDSepF5eOK8OSlACCnxX9ZxBpzBD8T26w@pevoy.protocolbuffer.com:28337?flow=&security=tls&sni=pevoy.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319新加坡 
ss://YWVzLTI1Ni1nY206QkZZQ09LSFRDOEhJV1dSQg==@ti3hyra4.slashdevslashnetslashtun.net:16006#0319新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Ni4zMi4zNS4xNDgiLCJwb3J0IjoyMTAxMywic2N5IjoiYXV0byIsInBzIjoiMDMxOeS/hOe9l+aWryIsIm5ldCI6IndzIiwiaWQiOiI0NTVjZTczYS0yNDJjLTQ1MDItYjdjNi0xOTA3NDQ5YzE5NWEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4yMi4xNTIuMjM2IiwicG9ydCI6MjMwMTcsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnkv4TnvZfmlq8iLCJuZXQiOiJ3cyIsImlkIjoiNmM5ODdhZjUtNmNmZS00YzJjLTk1OGUtYWFhYjIxYjRmMTRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0319波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE55rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTptQ2Vvc1JhY3NnRlJ0bkpQcTN6Y3Rx@77.83.246.74:443#0319波兰 
ss://YWVzLTI1Ni1nY206WDZXTVE5N1I5QUs3UFgwSQ==@109.104.154.131:20000#0319荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp3MkhkWm5HYjVpYmg=@89.221.225.88:443#0319摩尔多瓦 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo4NzdjM2IwNjljMzM1ZmZj@163.171.181.49:12317#0319科威特 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0319日本 
trojan://p0axgx3pXT6yjp4SwSRaaYeCDxCFOFaAlRYDNaRjF8OycXn3ZE3ABaYgnDIx3Eeq9C0ce@43.206.220.255:443?flow=&security=tls&sni=huzzah.meijireform.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319日本 
ss://YWVzLTI1Ni1nY206WU1CM1FMODVMN0YxS0pSNw==@8tv68qhq.slashdevslashnetslashtun.net:18013#0319日本 
trojan://p0axgx3pXT6yjp4SwSRaaYeCDxCFOFaAlRYDNaRjF8OycXn3ZE3ABaYgnDIx3Eeq9C0ce@huzzah.meijireform.com:443?flow=&security=tls&sni=huzzah.meijireform.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319日本 
ss://YWVzLTI1Ni1nY206UkFLTDVaRzRRTkZBNzJWWA==@ti3hyra4.slashdevslashnetslashtun.net:18007#0319日本 
ss://YWVzLTI1Ni1nY206ODRITVJBV0lMS0I0OVFVWg==@ti3hyra4.slashdevslashnetslashtun.net:18002#0319日本 
ss://YWVzLTI1Ni1nY206S0cxOENWNkhXUjdDWFdQNg==@ti3hyra4.slashdevslashnetslashtun.net:18001#0319日本 
vless://753fa8e8-a3e8-442e-abf7-875ed776eacb@104.17.221.248:443?flow=&encryption=none&security=tls&sni=is.oldcloud.online&type=ws&host=is.oldcloud.online&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319以色列 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0319以色列 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989#0319以色列 
trojan://telegram-id-privatevpns@108.128.8.151:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319爱尔兰 
trojan://Fl4B9jyFAwE4XgFxuICw8pD0NCYIneA22OyYO30enl8Kxe3a3xcpDEyqa79CTNSpRA5D8@13.40.166.49:443?flow=&security=tls&sni=young.golfland.club&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319英国 
trojan://telegram-id-directvpn@18.130.57.147:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319英国 
ss://YWVzLTI1Ni1nY206RlMzN0Y2MUdCQUlYSkY2RQ==@206.245.211.13:19003#0319英国 
ss://YWVzLTI1Ni1nY206UkhQU0pTRUZMSEdPV0NCNg==@206.245.211.14:19004#0319英国 
ss://YWVzLTI1Ni1nY206MU1EN1kxSEU4RkZIQUIwTg==@206.245.211.18:19008#0319英国 
ss://YWVzLTI1Ni1nY206RThDTTNSM0JXWFFRTllNTQ==@206.245.211.22:19012#0319英国 
ss://YWVzLTI1Ni1nY206NTVOMDlOQ1hXRUg3R1FNRg==@206.245.211.25:19015#0319英国 
trojan://telegram-id-privatevpns@35.176.148.28:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImR4djQucGFpNTAyODgudWsiLCJwb3J0IjoxNDEwMCwic2N5IjoiYXV0byIsInBzIjoiMDMxOeiLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiZjY4NjZiMGItZjk0Ni00YTAzLThkZjAtYzdlMDAxNmI1NWFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://Fl4B9jyFAwE4XgFxuICw8pD0NCYIneA22OyYO30enl8Kxe3a3xcpDEyqa79CTNSpRA5D8@young.golfland.club:443?flow=&security=tls&sni=young.golfland.club&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319英国 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0319法国 
trojan://RXO4SlDD8qRKaxz3cBgSa3AXZuFnpu3Ce3KZFAN3YCxC7EEj2lTRN4Y6FyOcBp50IzD3D@bottling.coffeekit.net:443?flow=&security=tls&sni=bottling.coffeekit.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319法国 
vmess://eyJ2IjoiMiIsImFkZCI6IjY1LjEwOS4xNzkuMTEzIiwicG9ydCI6MjA4OCwic2N5IjoiYXV0byIsInBzIjoiMDMxOeiKrOWFsCIsIm5ldCI6InRjcCIsImlkIjoiMTk0YzBkMmYtOTMwNy00YTNmLWIyMjctNTE2MzlkZDEzYWRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoiaHR0cCIsImhvc3QiOiJ6dWxhLmlyIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0319丹麦 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@212.115.124.224:57194?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0319德国 
trojan://telegram-id-directvpn@35.158.198.221:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319德国 
vless://24a4aa9b-b341-4717-9d4a-00d74c2b84e0@104.17.147.22:2096?flow=&encryption=none&security=tls&sni=7G6gLgL6fJ.mYsPdMmEtI.cOm&type=ws&host=7G6gLgL6fJ.mYsPdMmEtI.cOm&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319塞浦路斯 
ss://YWVzLTI1Ni1nY206WjJHQjRPMVI0UklWRFZGMg==@91.148.135.48:20039#0319塞浦路斯 
ss://YWVzLTI1Ni1nY206TFpRMFI5Qkw2OUdDQzZGUw==@8tv68qhq.slashdevslashnetslashtun.net:15005#0319中国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk01.x.quickcht3.club:52611#0319中国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk02.x.quickcht3.club:52612#0319中国 
ss://YWVzLTI1Ni1nY206SllRNTBHWExLVjJGNlpYVA==@qh62onjn.slashdevslashnetslashtun.net:15015#0319中国 
ss://YWVzLTI1Ni1nY206UkJOMVVOR1ZQRjFCUVhQSw==@ti3hyra4.slashdevslashnetslashtun.net:15006#0319中国 
vmess://eyJ2IjoiMiIsImFkZCI6InZjLmZseS5kZXYiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnkuK3lm70iLCJuZXQiOiJ3cyIsImlkIjoiMzUzNzkyMTktNjUzNS00ZjJlLWE0ZmUtM2U0NGY2MWUwZWVlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjozMiwidHlwZSI6Im5vbmUiLCJob3N0IjoidmMuZmx5LmRldiIsInBhdGgiOiIvdmMiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://a38c9e28-9960-4e31-9f18-ed2495a756aa@vt-bana2-cn-11.ghpgwqswodgzv.com:40021?flow=&security=tls&sni=vt-bana2-cn-11.ghpgwqswodgzv.com&type=ws&header=none&host=vt-bana2-cn-11.ghpgwqswodgzv.com&path=/dl_media&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319中国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@84.17.53.160:989#0319瑞士 
ss://YWVzLTI1Ni1nY206UFJDVUo4SU5QTjlLWlc3Mg==@185.186.78.220:20035#0319加拿大 
ss://YWVzLTI1Ni1nY206OUYyRzJFUDhFVDFQTDZRNQ==@185.213.20.36:20029#0319加拿大 
ss://YWVzLTI1Ni1nY206OUQ1STI2VEU4NVNQOTI4Vw==@185.213.22.93:20026#0319加拿大 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo2MjBjNWI1MTA4MTIwYTcy@23.162.56.206:11201#0319加拿大 
ss://YWVzLTI1Ni1nY206VkNSNkhOOFVMVTRTNE4yNw==@45.154.207.246:20030#0319加拿大 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0319孟加拉国 
hysteria2://7RACOJWhZu3hbH8CHh@109.71.253.251:21599?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=7sqyCdAR8awtyUKHECrFGPUCHA&os=#0319德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjdjNzFmZTctZDRmNy00ODBmLTkxMDgtOWE4MmU3OWRmOWM4QDEwOS43MS4yNTMuMjUxOjMwODYyOndzOi9YMk9VRiUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0319德国 
vless://f7c71fe7-d4f7-480f-9108-9a82e79df9c8@109.71.253.251:28424?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/WNcQYzMbjQn%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319德国 
hysteria2://7CrTncd6QfhBEUvsi9Cuzhe@109.71.253.251:53646?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=SOMnIfqY5yZYXbwf1tgFufg5JCrCWSS&os=#0319德国 
vless://a9f3c319-bc7c-4efa-bcf9-bbb2adaff5f4@109.71.253.251:6042?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/jcLQVZcAP129P9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319德国 
hysteria2://cg1Sp4q4An7z9XnO7pZHlhZ9N@109.71.253.251:33936?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=k3siqzZNMXUGYktoPA0lBd6&os=#0319德国 
hysteria2://BmiUivYWEzh37sOERZ56Kkpdc@109.71.253.251:19735?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=rBA7MhmhIM99puQMDsgrmQxp9m6uKQ&os=#0319德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTU1MjhlYzQtNzI1YS00MWI2LWJlZGQtOGFkZTcyYzYzZDIwQDEwOS43MS4yNTMuMjUxOjI4MDgyOndzOi9pUDBGMnQ1eFFtVFRtODI0UDVKRTU5ZjFpSWQlM0ZlZCUzRDI1NjA6d3d3LmRpZ2l0YWxvY2Vhbi5jb206bm9uZTp0bHM6d3d3LmRpZ2l0YWxvY2Vhbi5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0319德国 
hysteria2://kwsQm64kkqJlltynSf3kQ97b2XlAqdCsL@109.71.253.251:63514?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=xQMU3yu6zgnyrfWgypSFmrebcY9bu86LH70oRmQ&os=#0319德国 
trojan://8e8357a9-64af-49e5-a08b-3f95ac47674b@109.71.253.251:38754?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/ulRNTZXvP%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMjUxIiwicG9ydCI6MTI2MDIsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTnlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZTVhYWI0MzktYjg0NS00OGQxLTg5ZTMtNmI3MjZlZDA5YmE4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsInBhdGgiOiIvP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMjUxIiwicG9ydCI6NDE1Mywic2N5IjoiYXV0byIsInBzIjoiMDMxOeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmN2M3MWZlNy1kNGY3LTQ4MGYtOTEwOC05YTgyZTc5ZGY5YzgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwicGF0aCI6Ii96P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://ccb9a257-dd06-4c94-bc9e-64574b8b7f31@109.71.253.251:46673?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/MxlB1TycYDOOCnNSI0Z8doG%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0319德国 
hysteria2://WaWwehKjc13hOB8ykbm@109.71.253.251:37470?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=posY9IRh18L6uCT7T&os=#0319德国 
hysteria2://pSclcnoTlXQLeD8bcnnrHIH@109.71.253.251:48555?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=r1P1MDy33hShVgrs&os=#0319德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OGU4MzU3YTktNjRhZi00OWU1LWEwOGItM2Y5NWFjNDc2NzRiQDEwOS43MS4yNTMuMjUxOjU5Njk1OndzOi9HcEdGUmJRcjI3TSUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0319德国 


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
