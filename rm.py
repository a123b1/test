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

vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.16.147.32:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.16.250.22:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.16.250.22:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.17.25.173:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.17.25.173:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.18.185.26:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.18.185.26:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.18.185.26:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://5d455342-2929-45a0-951a-1b273ec39b7c@104.18.7.36:2086?flow=&encryption=none&security=&sni=&type=ws&host=rayan11-0l5mxs7b-v1.rayan-11.workers.dev&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125荷兰 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.224.5:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.224.5:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.224.5:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.227.134:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.227.134:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@114.32.9.249:51443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://d6b1327d-2bec-4366-a3a1-9b1284f95841@138.124.79.3:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125瑞士 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.16.63:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.16.63:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.16.63:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.44.142:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.44.142:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.45.232:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.45.232:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.45.232:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://cc61ea7c-92f2-4c2d-b272-32cfe8fdf99f@176.109.104.107:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=/&headerType=none&alpn=&fp=chrome&pbk=CMkW1axrhEXoiJ6anMz9XEjlfqlAtEZya7L0b5ZPMyw&sid=c7e42004e5f024be&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125印度 
vless://447c45cd-ade0-4bfe-90a0-3e581829f741@178.17.53.28:47539?flow=&encryption=none&security=reality&sni=yandex.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=uapzi5mhLkADHuak0eXEKq9vIl2A8IGrMhjdIG-tn3U&sid=82a55f31981ea6be&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0125芬兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0125波兰 
vless://dd92c4f8-be88-4c61-84eb-d261f798071e@185.234.57.207:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=teamdocs.su&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=Yu1_Agl1_bJb298G9ukjGuvfksVTUs1X7laYJ3VqwwQ&sid=b5e0cd9ca194c0a5&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125亚美尼亚 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@185.251.89.26:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125俄罗斯 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@198.62.62.241:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@198.62.62.241:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
trojan://BxceQaOe@219.76.135.98:443?flow=&security=tls&sni=219.76.135.98&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
vless://5d42cfef-0556-4f0c-bfb7-161aef500ab5@222.102.51.111:51698?flow=&encryption=none&security=reality&sni=lenovoglobal.com&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=chrome&pbk=PPZbDAYSwCYnPCF8BxguTFfAAZTnLnzpsHePCkGZYxo&sid=34&spx=/---v2rayNplus---v2rayNplus---v2rayNplus---v2rayNplus---&allowInsecure=1&fragment=,100-200,10-60&os=#0125韩国 
vless://d4a23188-85b0-4b46-b84b-f1d36d66c03e@43.161.253.78:9527?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
vless://d4a23188-85b0-4b46-b84b-f1d36d66c03e@43.161.253.78:9527?flow=&encryption=none&security=&sni=&type=tcp&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@45.15.127.139:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125芬兰 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@45.67.231.129:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125荷兰 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@5.129.214.27:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125荷兰 
ss://YWVzLTEyOC1nY206dEtrbytZSUF1dVozZDBoc1BYMitEM05xZXB5dEcxSGEwVlJMd0JyZjBBaz0=@5.129.219.21:8080?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@5.181.21.101:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125奥地利 
trojan://BxceQaOe@58.152.25.130:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
trojan://BxceQaOe@58.152.25.130:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
trojan://BxceQaOe@58.152.25.130:443?flow=&security=tls&sni=58.152.25.130&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
trojan://BxceQaOe@58.152.53.45:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
vless://6e6609bf-6867-4fa7-b4c3-d5555d67d724@77.105.137.100:4443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=github.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=5XB_N3ATilH-6tp_MXht-84_y5YaJnx_Z7MbuY2otHE&sid=aa7e96542880027a&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125荷兰 
vless://fd8972d7-cf5e-11f0-9970-45e1d80c4039@78.153.139.68:8443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=images.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=random&pbk=pekfYPV5U8EjfQ4_zS5c6I2NnOZ2jUlyMGAWa4FWPF4&sid=58c512b4422e2517&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125芬兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://cc235335-34f0-4f1b-b3e3-5f32e2eeaa89@87.120.165.175:8443?flow=&encryption=none&security=reality&sni=monolithgate.xyz&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=llSF90j8PQdR0alqH2OGlh7fEtoxO-xfZW_B4bQ4eSw&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125保加利亚 
vless://45e3b7ad-03b6-42fc-b616-1e92bdd0a5b3@94.228.213.219:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=hls-svod.itunes.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=mLmBhbVFfNuo2eUgBh6r9-5Koz9mUCn3aSzlR6IejUg&sid=48720c&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125荷兰 
vless://cc61ea7c-92f2-4c2d-b272-32cfe8fdf99f@95.174.92.156:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=sun6-21.userapi.com&type=tcp&host=&path=/&headerType=none&alpn=&fp=chrome&pbk=CMkW1axrhEXoiJ6anMz9XEjlfqlAtEZya7L0b5ZPMyw&sid=c7e42004e5f024be&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125印度 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/x-aniu/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
trojan://30077070-596e-48ea-9400-14c8ed07bd97@tuntro000.instconn.com:443?flow=&security=tls&sni=hkip5.686911.xyz&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125香港 
trojan://30077070-596e-48ea-9400-14c8ed07bd97@tuntro006.instconn.com:443?flow=&security=tls&sni=torontorm1.686911.xyz&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125加拿大 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDEyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTIuaGRhY2QuY29tIiwicGF0aCI6Ij9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDEyNeiNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhkYWNkLmNvbSIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMTI1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiJjaHJvbWUiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://33a57acf-163f-4cdd-8b23-cc52a58f2362@xhero.kharabetam.de:2053?flow=&encryption=none&security=tls&sni=mrx.xher0.de&type=ws&host=mrx.xher0.de&path=/IfUknowThenUKnow&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://33a57acf-163f-4cdd-8b23-cc52a58f2362@xhero.kharabetam.de:2053?flow=&encryption=none&security=tls&sni=mrx.xher0.de&type=ws&host=mrx.xher0.de&path=/IfUknowThenUKnow&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://33a57acf-163f-4cdd-8b23-cc52a58f2362@xhero.kharabetam.de:2053?flow=&encryption=none&security=tls&sni=mrx.xher0.de&type=ws&host=&path=/IfUknowThenUKnow&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.18.248.218:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
trojan://ba0f6256-2865-45e4-af9f-9e0e01c7e809@45.82.120.238:13067?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/f4vIVNJ%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.242:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
hysteria2://uFV6d9GURMAxtXqLU4CL9T9@45.82.120.238:15089?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=Nwuc6DDgeMyyVQqpib&mport=&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.27.3.204:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.20.251.171:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.18.24.219:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@188.114.96.253:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@3br.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=3br.oceanof.xyz&type=xhttp&host=3br.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://eb0177d1-da1b-44b5-a653-5364d11ceb37@45.82.120.238:11512?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/OpjIXWzv4Vd9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.20.51.130:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@141.101.113.130:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@5mi0.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=5mi0.oceanof.xyz&type=xhttp&host=5mi0.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.86:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.196.128:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@ds3.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ds3.oceanof.xyz&type=xhttp&host=ds3.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMzgiLCJwb3J0Ijo2MTY4NCwic2N5IjoiYXV0byIsInBzIjoiMDEyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlYzY2N2ViMy0yZjIwLTQ1MDEtYjVhOS02MjIyMjJiNTA5NDEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwicGF0aCI6Ii93a2t6a25qbUFwM3lVT2lnYUd2OXE/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.19.133.213:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@3aon.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=3aon.oceanof.xyz&type=xhttp&host=3aon.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://51551189-e8eb-467a-a611-5135fe663f79@45.82.120.238:39480?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/p21%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.160.84:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.203:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@141.101.121.129:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@42.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=42.oceanof.xyz&type=xhttp&host=42.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@ltp3.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=ltp3.oceanof.xyz&type=xhttp&host=ltp3.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@dc2.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=dc2.oceanof.xyz&type=xhttp&host=dc2.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125美国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.155:443?flow=&encryption=none&security=tls&sni=voa.msxoa.dpdns.org&type=xhttp&host=voa.msxoa.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0125德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTMyNGI5MDktNWRjYi00NzBmLTliODgtMzIwM2RlNmQ2NzQ5QDQ1LjgyLjEyMC4yMzg6NTA1ODI6d3M6L0hTTWR4RmlIR0hNUlZqeEFKeCUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0125德国 
anytls://q2nemHtgtr1R0aD7PVNa3Nnnpucz@45.82.120.238:58335?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0125德国 



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
