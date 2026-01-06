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

vless://c3712f67-6852-4bdd-be90-af89d3701d1f@103.21.244.150:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@103.21.244.191:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@103.241.65.11:8445?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpBUmd2R1p5d0ErZ2FjZ0dWMjZCdm11MDUrd1ptUlcvaitBZFUrWjhCdDQ0PQ==@103.97.203.227:990?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0105印度 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@104.16.65.1:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/fp%3Dchrome&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
trojan://5a2c16f9@104.17.162.3:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
trojan://5a2c16f9@104.19.55.205:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.20.64.155:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.24.9.3:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.25.194.251:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.25.202.125:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
trojan://5a2c16f9@104.26.1.110:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=//&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.27.29.71:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.27.65.243:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@104.27.87.206:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://e258977b-e413-4718-a3af-02d75492c349@156.231.117.147:443?flow=&encryption=none&security=tls&sni=x-hk.xaniusnippets.qzz.io&type=ws&host=x-hk.xaniusnippets.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105英国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.16.63:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@162.159.192.187:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@162.159.252.125:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.44.142:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.45.232:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@173.245.58.127:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@173.245.59.126:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://447c45cd-ade0-4bfe-90a0-3e581829f741@178.17.53.28:47539?flow=&encryption=none&security=reality&sni=yandex.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=uapzi5mhLkADHuak0eXEKq9vIl2A8IGrMhjdIG-tn3U&sid=82a55f31981ea6be&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0105芬兰 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@188.114.98.202:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.126:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.129:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.130:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105日本 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.133:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.136:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105日本 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.14:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.141:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105荷兰 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.149:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://e258977b-e413-4718-a3af-02d75492c349@188.164.248.41:443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@190.93.247.114:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://c3712f67-6852-4bdd-be90-af89d3701d1f@198.41.201.41:443?flow=&encryption=none&security=tls&sni=www.ckosuz.dpdns.org&type=xhttp&host=www.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
vless://e258977b-e413-4718-a3af-02d75492c349@206.237.13.23:8443?flow=&encryption=none&security=tls&sni=ww1.allxniu.qzz.io&type=ws&host=ww1.allxniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105日本 
vless://5d42cfef-0556-4f0c-bfb7-161aef500ab5@222.102.51.111:51698?flow=&encryption=none&security=reality&sni=lenovoglobal.com&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=chrome&pbk=PPZbDAYSwCYnPCF8BxguTFfAAZTnLnzpsHePCkGZYxo&sid=34&spx=/---v2rayNplus---v2rayNplus---v2rayNplus---v2rayNplus---&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://3afad5df-e056-4301-846d-665b4ef51968@223.222.195.84:10000?flow=&encryption=none&security=tls&sni=x.kkii.eu.org&type=ws&host=x.kkii.eu.org&path=/223.222.195.84%3A10000&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://e258977b-e413-4718-a3af-02d75492c349@34.143.159.175:443?flow=&encryption=none&security=tls&sni=x-hk.xaniusnippets.qzz.io&type=ws&host=x-hk.xaniusnippets.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://e258977b-e413-4718-a3af-02d75492c349@34.146.161.25:19000?flow=&encryption=none&security=tls&sni=x-hk.xaniusnippets.qzz.io&type=ws&host=x-hk.xaniusnippets.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105英国 
vless://e258977b-e413-4718-a3af-02d75492c349@43.161.225.77:443?flow=&encryption=none&security=tls&sni=jp.xaniusg2.qzz.io&type=ws&host=jp.xaniusg2.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105荷兰 
vless://e258977b-e413-4718-a3af-02d75492c349@45.66.129.7:21262?flow=&encryption=none&security=tls&sni=www.sgxaniu.qzz.io&type=ws&host=www.sgxaniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://309fa273-6579-4cb2-9143-7cad50401eba@45.89.107.200:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.cloudflare.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=gZGVp5PUdafgsmi1gawa1yLuha_XhXRc_W9SvPiGmTY&sid=7cad5040&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105马来西亚 
hysteria2://VKVu07CQ5bbhyV34meKtdu@5.180.253.81:15058?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=SnP26oOj1sor8s8a1PFhVXjYy&mport=&os=#0105德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My44MSIsInBvcnQiOjY5MDgsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDXlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNTlhMjI3MGQtNGYxZC00ZjliLTgyNTktZDJiYjcyNzdhZjYzIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJidXJnZXJpcC5jby51ayIsInBhdGgiOiIvNkFrOE9xSTM/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJ1cmdlcmlwLmNvLnVrIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://eajvKOxTT9YFTagfHM2WnQZ3cefAy@5.180.253.81:40293?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0105德国 
hysteria2://HmDnhorXVcunmV2cL6KCv2C7mqCQd@5.180.253.81:15663?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=OQeupdc027BIaG8hBV6lb16ieQFmeBx87t9266&mport=&os=#0105德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My44MSIsInBvcnQiOjQ2OTcyLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6ImJkYzNhY2UyLWNiMGItNDk2Ny05ODI2LTBlMmRhYjdlZjJhZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYnVyZ2VyaXAuY28udWsiLCJwYXRoIjoiL04/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJ1cmdlcmlwLmNvLnVrIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://TETUVhtDk3d2N4Lf6Mtruc0sOOgxLCT3NBTu@5.180.253.81:15498?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0105德国 
hysteria2://gkU0REX655Ck8rg2SQaAbC4eV5GN@5.180.253.81:45359?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=YkwlweUwa2uj1NXpPbp0&mport=&os=#0105德国 
hysteria2://43Ky0fXQ4XHsrCJ540UVuYM5cUiE1h@5.180.253.81:20199?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=KVFJrJNCOktQdE8383FTVlbHY58AYGwQN&mport=&os=#0105德国 
trojan://381f2e86233720eacda26d50e9aa26da@58.152.110.104:443?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0105香港 
trojan://BxceQaOe@58.152.25.236:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
trojan://BxceQaOe@58.152.25.86:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
trojan://BxceQaOe@58.152.46.60:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://3afad5df-e056-4301-846d-665b4ef51968@59.3.3.161:8443?flow=&encryption=none&security=tls&sni=x.kkii.eu.org&type=ws&host=x.kkii.eu.org&path=/59.3.3.161%3A8443&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105韩国 
vless://e258977b-e413-4718-a3af-02d75492c349@68.64.178.74:8443?flow=&encryption=none&security=tls&sni=www.sgxaniu.qzz.io&type=ws&host=www.sgxaniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://e258977b-e413-4718-a3af-02d75492c349@8.223.63.150:443?flow=&encryption=none&security=tls&sni=www.sgxaniu.qzz.io&type=ws&host=www.sgxaniu.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://e258977b-e413-4718-a3af-02d75492c349@83.229.124.163:30443?flow=&encryption=none&security=tls&sni=jp.xaniusg2.qzz.io&type=ws&host=jp.xaniusg2.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105日本 
trojan://5a2c16f9@94.140.0.238:2096?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3WangCai2&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@95.182.99.65:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/Telegram%F0%9F%87%A8%F0%9F%87%B3WangCai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
trojan://5a2c16f9@cf.130519.xyz:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
trojan://zzyzzy0512@fast1.swjtu.work:443?flow=&security=tls&sni=fast1.swjtu.work&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
vless://2262242d-1b1c-481c-b60d-cde0e6a48bb2@filma.video-fun-new.com.de:443?flow=&encryption=none&security=tls&sni=filma.video-fun-new.com.de&type=ws&host=filma.video-fun-new.com.de&path=/Mv3kv92GcD3E2KuHxT&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105德国 
trojan://5a2c16f9@freeyx.cloudflare88.eu.org:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
trojan://ba91a84a-6b81-4aef-be19-a76f64a790d1@green2.cdntencentmusic.com:35501?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105美国 
trojan://3c9e4a24-aa0f-4571-970b-d374ccded73b@green2.cdntencentmusic.com:31102?flow=&security=tls&sni=green2.cdntencentmusic.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://eb162ab1-a006-4931-b1b3-8fc88a22b10e@mailru.ookcdn.ru:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=mailru.ookcdn.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=WvNaAxI0W__qfUKbtysH4IwF155YENlv3PG6crCmPkA&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105波兰 
trojan://5a2c16f9@one.cf.cdn.hyli.xyz:443?flow=&security=tls&sni=snippets.kkii.eu.org&type=ws&header=none&host=snippets.kkii.eu.org&path=/&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDEwNemmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDEwNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZGFjZC5jb20iLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDEwNeW+t+WbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@vip2.kaixincloud.top:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://5a2c16f9-e365-4080-8d38-6924c3835586@wangcai.24av.top:443?flow=&encryption=none&security=tls&sni=snippets.kkii.eu.org&type=ws&host=snippets.kkii.eu.org&path=/telegram%F0%9F%87%A8%F0%9F%87%B3%40wangcai2&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105台湾 
vless://e258977b-e413-4718-a3af-02d75492c349@www.udacity.com:8443?flow=&encryption=none&security=tls&sni=x-hk.xaniusnippets.qzz.io&type=ws&host=x-hk.xaniusnippets.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105香港 
vless://e258977b-e413-4718-a3af-02d75492c349@www.wto.org:443?flow=&encryption=none&security=tls&sni=jp.xaniusg2.qzz.io&type=ws&host=jp.xaniusg2.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105荷兰 
vless://e258977b-e413-4718-a3af-02d75492c349@x.cf.090227.xyz:2096?flow=&encryption=none&security=tls&sni=jp.xaniusg2.qzz.io&type=ws&host=jp.xaniusg2.qzz.io&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0105日本 

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
