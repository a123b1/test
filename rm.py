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

ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpBUmd2R1p5d0ErZ2FjZ0dWMjZCdm11MDUrd1ptUlcvaitBZFUrWjhCdDQ0PQ==@103.97.203.227:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221印度 
trojan://5a2c16f9@104.17.162.3:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@104.17.202.10:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@104.19.212.207:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@104.19.220.22:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@104.19.220.22:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@104.19.39.97:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@104.19.55.205:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://3f9c8463-8610-3ed8-86c8-a26713067825@104.26.1.221:443?flow=&encryption=none&security=tls&sni=dabaius2.sylu.net&type=ws&host=dabaius2.sylu.net&path=/db10240eb751d6ab&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
vless://3f9c8463-8610-3ed8-86c8-a26713067825@104.26.1.221:443?flow=&encryption=none&security=tls&sni=dabaius2.sylu.net&type=ws&host=dabaius2.sylu.net&path=/db10240eb751d6ab&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
vless://dd0f3ac0-98db-4ad0-9ac4-a3db5b6aa18e@104.26.6.89:80?flow=&encryption=none&security=&sni=&type=ws&host=elegaNt-PrOJECt4lB40WUCws.wiNDLEr.Co.uK&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://c5b129d7-f133-4b34-a9c6-68c9a8f70248@104.26.6.89:80?flow=&encryption=none&security=&sni=&type=ws&host=EMotioNaL-peRMIsSiONf1bs65u5f4.EcOTOuRISs.Co.uK&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221加拿大 
vless://c5b129d7-f133-4b34-a9c6-68c9a8f70248@104.26.6.89:80?flow=&encryption=none&security=&sni=&type=ws&host=EMotioNaL-peRMIsSiONf1bs65u5f4.EcOTOuRISs.Co.uK&path=/%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221加拿大 
vless://c5b129d7-f133-4b34-a9c6-68c9a8f70248@104.26.6.89:80?flow=&encryption=none&security=&sni=EMotioNaL-peRMIsSiONf1bs65u5f4.EcOTOuRISs.Co.uK&type=ws&host=EMotioNaL-peRMIsSiONf1bs65u5f4.EcOTOuRISs.Co.uK&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221加拿大 
vless://dd0f3ac0-98db-4ad0-9ac4-a3db5b6aa18e@104.26.6.89:80?flow=&encryption=none&security=&sni=&type=ws&host=elegaNt-PrOJECt4lB40WUCws.wiNDLEr.Co.uK&path=/%3Fed&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://dd0f3ac0-98db-4ad0-9ac4-a3db5b6aa18e@104.26.6.89:80?flow=&encryption=none&security=&sni=elegaNt-PrOJECt4lB40WUCws.wiNDLEr.Co.uK&type=ws&host=elegaNt-PrOJECt4lB40WUCws.wiNDLEr.Co.uK&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@108.162.198.185:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@119.59.98.58:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221泰国 
trojan://5a2c16f9@162.159.128.253:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@162.159.235.26:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@162.159.24.131:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@172.64.229.205:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@172.64.229.205:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://e258977b-e413-4718-a3af-02d75492c349@172.64.49.11:2087?flow=&encryption=none&security=tls&sni=bb-67r.pages.dev&type=ws&host=bb-67r.pages.dev&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://fd4b0117-d752-46fd-9a94-21a21e360fdb@178.154.205.131:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=ads.x5.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=r5WB5FnSCt4eeBC1FJMfkWHbzsMuabo0Rc6wuAhlZUs&sid=672ff0&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221摩尔多瓦 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@185.235.241.117:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@185.235.241.124:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@185.235.241.155:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@185.235.241.53:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.236.232.108:80?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpTNmpVSzlGdzVmTUhnTnFscVhPYkhaV3Y4VGY0bkVrbQ==@193.203.203.66:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221加拿大 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpIYU5xdzlwSUU0amN4OThzZzdVUWdIZUdOVE00UjJwaw==@194.246.114.101:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyREdxM2p2VlJnNW4zQ2N4bXlzR0sya21yZ0plU05vZjEyQTc2Y1p2VnhxUHBldHlDMVhFY2lDRnVmcTV4S3ZSV0dHbktWZW1icFRodVVTUWhiWjdHTXNaWTRVVnhFQnc=@208.67.106.73:44884?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221荷兰 
vless://c495cf08-e046-4311-aa4b-82cc16576992@217.16.27.97:501?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=QZiKeygQkG92DFn35fifsUKH2pHT37cAYTvhlG5c_V0&sid=af133bb9dc19d678&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221俄罗斯 
trojan://25a6f104-84d0-4a8b-9827-1937f8816a6e@220.130.58.138:31104?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://17d3bf89-d2f0-4827-bcd0-c199fe54cd2a@220.130.58.138:34411?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221日本 
trojan://04a6a322-b08e-4635-99af-219c01ade7dd@220.130.58.138:31104?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://04a6a322-b08e-4635-99af-219c01ade7dd@220.130.58.138:31104?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://17d3bf89-d2f0-4827-bcd0-c199fe54cd2a@220.130.58.138:34411?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221日本 
trojan://25a6f104-84d0-4a8b-9827-1937f8816a6e@220.130.58.138:31104?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://25a6f104-84d0-4a8b-9827-1937f8816a6e@220.130.58.138:34411?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjE2NS43LjcxIiwicG9ydCI6MTk3NTEsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHlvrflm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjZjZmE2MTAzLTVkMDYtNDBjYi1mNDUyLWI1NjNkYjU3ODI4OCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiNDMuMTY1LjcuNzEiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQzLjE2NS43LjcxIiwicG9ydCI6MTk3NTEsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHlvrflm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjZjZmE2MTAzLTVkMDYtNDBjYi1mNDUyLWI1NjNkYjU3ODI4OCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Imh0dHAiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://fd4b0117-d752-46fd-9a94-21a21e360fdb@51.250.10.228:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=&headerType=none&alpn=&fp=qq&pbk=r5WB5FnSCt4eeBC1FJMfkWHbzsMuabo0Rc6wuAhlZUs&sid=65c7748be8&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://c495cf08-e046-4311-aa4b-82cc16576992@51.250.75.169:444?flow=&encryption=none&security=reality&sni=ads.x5.ru&type=grpc&host=&serviceName=ads.x5.ru&mode=gun&alpn=&fp=chrome&pbk=L0ZCh9LynIMEkK9BZq3gC--mzL6xnR4bkBJmXHSwVCM&sid=0614386789abcdef&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221俄罗斯 
vless://c495cf08-e046-4311-aa4b-82cc16576992@51.250.88.6:446?flow=&encryption=none&security=reality&sni=ads.x5.ru&type=grpc&host=&serviceName=ads.x5.ru&mode=gun&alpn=&fp=chrome&pbk=mMaSUsOC5i3ErLDcaWW9UOOjG0fcKPCwVjzGS1wXQx8&sid=0512567389abcdef&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221俄罗斯 
trojan://BxceQaOe@58.152.25.71:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.25.71:443?flow=&security=tls&sni=%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%5BByEbraSha%5Db2n.ir/v2ray-configs%7C625&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.25.71:443?flow=&security=tls&sni=%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%5BByDukeMehdi%5Db2n.ir/v2ray-configs%7C625&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.25.71:443?flow=&security=tls&sni=%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.26.107:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.26.107:443?flow=&security=tls&sni=%C3%B0%C5%B8%E2%80%9D%E2%80%99%5BByDukeMehdi%5Db2n.ir/v2ray-configs%7C748&type=tcp&header=none&host=&path=&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.26.107:443?flow=&security=tls&sni=%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%5BByDukeMehdi%5D&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://BxceQaOe@58.152.26.107:443?flow=&security=tls&sni=%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD%EF%BF%BD&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
vless://39e5cc2f-1294-4a42-bb58-306a8be785e1@62.60.148.21:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=st.ozone.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=BkAG_uWeUj7BCHqYjrz1JyH0TMvO_KywubV7WJN17ho&sid=ee6f3e8f44b1f0b6&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMjAwMTpiYzg6MzJkNzozMDI6OjEwIiwicGF0aCI6Ii9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZG91ZmVuZy5wYWdlcy5kZXYiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp5Q2JRNGJyeTRvdGZpZks3b2VsNzFOYVhwUEw5cFlKYg==@89.221.225.15:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221以色列 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpQZ0pWNHlSUHBHcG9WLTQwUFM4TjBHNmdTNEJwQlJrRg==@89.23.103.60:1234?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221荷兰 
vless://cf691676-f3e8-4e83-ad05-399638e0e010@94.131.100.167:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/czoxqsws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221芬兰 
vless://cdcec1c7-49f9-4db6-a8f8-6d6b1062ba2c@94.131.100.168:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hzfealws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221芬兰 
vless://0a0d846f-8f54-4db4-940b-b373b1b02e4c@94.131.100.173:443?flow=&encryption=none&security=tls&sni=www.vk.com&type=ws&host=&path=/coxzfsws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221芬兰 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@94.131.110.119:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e615a5ba-fce3-4ffa-9c86-b0327a8a107a@94.131.110.137:443?flow=&encryption=none&security=tls&sni=github.com&type=ws&host=&path=/hormoz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://7e9dfc75-9a4a-4468-bc44-7a7c97d6aab7@94.131.110.205:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/ixjtmaws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://8496c102-4094-4dd3-ad63-7bb7a35cbaee@94.182.137.12:20532?flow=&encryption=none&security=&sni=&type=tcp&host=Telewebion.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221法国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpwUW1uQzAzSk9iYlBoZGg1RkJKSGdENmpuVExjaHNSQQ==@95.164.116.33:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221土耳其 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@ali.nonull.pp.ua:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://e4824193-4f54-453b-d037-88368e85ef0e@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh30v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyREdxM2p2VlJnNW4zQ2N4bXlzR0sya21yZ0plU05vZjEyQTc2Y1p2VnhxUHBldHlDMVhFY2lDRnVmcTV4S3ZSV0dHbktWZW1icFRodVVTUWhiWjdHTXNaWTRVVnhFQnc=@backup.fleetfoxi.link:44884?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1221荷兰 
trojan://5a2c16f9@cf.130519.xyz:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@cf.zhetengsha.eu.org:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@freeyx.cloudflare88.eu.org:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://17d3bf89-d2f0-4827-bcd0-c199fe54cd2a@green2.cdntencentmusic.com:33301?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221新加坡 
trojan://17d3bf89-d2f0-4827-bcd0-c199fe54cd2a@green2.cdntencentmusic.com:31102?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://17d3bf89-d2f0-4827-bcd0-c199fe54cd2a@green2.cdntencentmusic.com:35501?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
trojan://c80870af-749e-406c-bdbd-7aafa46de71d@green2.cdntencentmusic.com:33301?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221新加坡 
trojan://04a6a322-b08e-4635-99af-219c01ade7dd@green2.cdntencentmusic.com:34411?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221日本 
trojan://a213e1a5-3c5a-40f2-b70e-98ffa63ffc8e@green2.cdntencentmusic.com:35501?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
trojan://b06e8208-d522-41b7-a840-6b8b7731b308@green2.cdntencentmusic.com:31103?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221香港 
trojan://Puj01Rc8UcA9IzcFcYOs8KMOhCz6aX2Q@mfyousheng.nl.eu.org:443?flow=&security=tls&sni=mfyousheng.nl.eu.org&type=ws&header=none&host=&path=/tjwsLhx0SFASG4l9FERJ1g&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221卢森堡 
trojan://Puj01Rc8UcA9IzcFcYOs8KMOhCz6aX2Q@mfyousheng.nl.eu.org:443?flow=&security=tls&sni=mfyousheng.nl.eu.org&type=ws&header=none&host=mfyousheng.nl.eu.org&path=/tjwsLhx0SFASG4l9FERJ1g&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221卢森堡 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@nrtcfdns.zone.id:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
trojan://5a2c16f9@one.cf.cdn.hyli.xyz:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221台湾 
vmess://eyJ2IjoiMiIsImFkZCI6InN5NC42MjA3MjAueHl6IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIxMjIx5r6z5aSn5Yip5LqaIiwibmV0Ijoid3MiLCJpZCI6IjUxNmQ4YTdhLTNmMGItNDFkMy1iYWQwLTI0NjExNjM4MTUxNiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic3k0LjYyMDcyMC54eXoiLCJwYXRoIjoiLyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InVzMjQtMy45OTg5OTguYmVzdCIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMTIyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI5NmRjMmExNi1lZTI5LTQ5M2YtOGExMC1iNzNiY2RkNGZjNWYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dzMuZ2FpdW9oci5jbG91ZC1pcC5jYyIsInBhdGgiOiIvcmlvdXRnaGV3aXVvcnJoOTgyM3IiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3czLmdhaXVvaHIuY2xvdWQtaXAuY2MiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMTIyMemmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTIyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTIyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJuMTc0NDQ1NDQ5OC5saWU1ZC5jeW91IiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTIyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMTIyMeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZGFjZC5jb20iLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMTIyMeazleWbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MzUuaGRhY2QuY29tIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://HmDnhorXVcunmV2cL6KCv2C7mqCQd@5.180.253.81:15663?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=OQeupdc027BIaG8hBV6lb16ieQFmeBx87t9266&mport=&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.201.41:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.17.107.191:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
anytls://TETUVhtDk3d2N4Lf6Mtruc0sOOgxLCT3NBTu@5.180.253.81:15498?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1221德国 
hysteria2://gkU0REX655Ck8rg2SQaAbC4eV5GN@5.180.253.81:45359?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=YkwlweUwa2uj1NXpPbp0&mport=&os=#1221德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@i.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=i.oceanof.xyz&type=xhttp&host=i.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
hysteria2://43Ky0fXQ4XHsrCJ540UVuYM5cUiE1h@5.180.253.81:20199?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=KVFJrJNCOktQdE8383FTVlbHY58AYGwQN&mport=&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.16.139.79:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.29.71:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.65.243:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@198.41.196.251:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.4.50:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My44MSIsInBvcnQiOjQ2OTcyLCJzY3kiOiJhdXRvIiwicHMiOiIxMjIx5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImJkYzNhY2UyLWNiMGItNDk2Ny05ODI2LTBlMmRhYjdlZjJhZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYnVyZ2VyaXAuY28udWsiLCJwYXRoIjoiL04/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJ1cmdlcmlwLmNvLnVrIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My44MSIsInBvcnQiOjY5MDgsInNjeSI6ImF1dG8iLCJwcyI6IjEyMjHlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNTlhMjI3MGQtNGYxZC00ZjliLTgyNTktZDJiYjcyNzdhZjYzIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJidXJnZXJpcC5jby51ayIsInBhdGgiOiIvNkFrOE9xSTM/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJ1cmdlcmlwLmNvLnVrIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@vdv.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=vdv.oceanof.xyz&type=xhttp&host=vdv.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@ery.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ery.oceanof.xyz&type=xhttp&host=ery.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@188.114.98.202:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
hysteria2://VKVu07CQ5bbhyV34meKtdu@5.180.253.81:15058?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=SnP26oOj1sor8s8a1PFhVXjYy&mport=&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@103.21.244.164:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@vky.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=vky.oceanof.xyz&type=xhttp&host=vky.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@173.245.58.127:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@2.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=2.oceanof.xyz&type=xhttp&host=2.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221美国 
anytls://eajvKOxTT9YFTagfHM2WnQZ3cefAy@5.180.253.81:40293?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1221德国 
vless://e60002ef-d2d6-4516-9acf-33365839daf9@104.27.104.179:443?flow=&encryption=none&security=tls&sni=www.ryalol.qzz.io&type=xhttp&host=www.ryalol.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1221德国 



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
