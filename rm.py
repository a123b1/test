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
vmess://eyJ2IjoiMiIsImFkZCI6InYzMC5oZGFjZC5jb20iLCJwb3J0IjozMDgzMCwic2N5IjoiYXV0byIsInBzIjoiMDExN+iNt+WFsCIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJpbWcxNC4zNjBidXlpbWcuY29tIiwicGF0aCI6Ii9vYmoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhkYWNkLmNvbSIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTE36aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.16.250.22:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@104.17.102.95:2096?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@104.17.102.95:8443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.17.25.173:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.18.185.26:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://5d455342-2929-45a0-951a-1b273ec39b7c@104.18.7.36:2086?flow=&encryption=none&security=&sni=&type=ws&host=rayan11-0l5mxs7b-v1.rayan-11.workers.dev&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@104.21.224.5:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@108.162.198.24:2096?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@154.17.10.237:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@154.17.13.69:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@154.17.227.191:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.16.63:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.44.142:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@162.159.45.232:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@172.64.229.220:2096?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://447c45cd-ade0-4bfe-90a0-3e581829f741@178.17.53.28:47539?flow=&encryption=none&security=reality&sni=yandex.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=uapzi5mhLkADHuak0eXEKq9vIl2A8IGrMhjdIG-tn3U&sid=82a55f31981ea6be&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0117伊拉克 
vless://052df1a5-f53f-46dc-8aeb-7ed893310551@185.221.222.202:31779?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117荷兰 
vless://dd92c4f8-be88-4c61-84eb-d261f798071e@185.234.57.207:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=teamdocs.su&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=Yu1_Agl1_bJb298G9ukjGuvfksVTUs1X7laYJ3VqwwQ&sid=b5e0cd9ca194c0a5&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117亚美尼亚 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@217.142.185.111:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://5d42cfef-0556-4f0c-bfb7-161aef500ab5@222.102.51.111:51698?flow=&encryption=none&security=reality&sni=lenovoglobal.com&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=chrome&pbk=PPZbDAYSwCYnPCF8BxguTFfAAZTnLnzpsHePCkGZYxo&sid=34&spx=/---v2rayNplus---v2rayNplus---v2rayNplus---v2rayNplus---&allowInsecure=1&fragment=,100-200,10-60&os=#0117韩国 
vless://8a07740f-b932-4372-a3a2-ed91f184cd33@25.129.197.138:2053?flow=&encryption=none&security=tls&sni=khamenei.dpdns.org&type=ws&host=khamenei.dpdns.org&path=/eyJqdW5rIjoiNDBNWGY3Z0NPd0loZ2YiLCJwcm90b2NvbCI6InZsIiwibW9kZSI6InByb3h5aXAiLCJwYW5lbElQcyI6W119&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117荷兰 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@43.161.222.233:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://7fc953d6-ae75-46fb-a970-10b57d513487@45.139.26.152:7443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=eh.vk.com&type=tcp&host=&path=&headerType=none&alpn=&fp=random&pbk=BTkKaFt2xac4xAHn3EXrBKV0d8ItHSfciMFnxg57BGA&sid=fd88bd27db4cc661&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117俄罗斯 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.0:443?flow=&encryption=none&security=tls&sni=GfV5t2331T.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.0:2087?flow=&encryption=none&security=tls&sni=5JxGp6VrFh.SmArTtEcHzAaL.iNfO&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.0:2096?flow=&encryption=none&security=tls&sni=TzS7v35LfD.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.0:8443?flow=&encryption=none&security=tls&sni=TjLwH7cTdH.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.5:443?flow=&encryption=none&security=tls&sni=GfV5t2331T.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.5:2087?flow=&encryption=none&security=tls&sni=5JxGp6VrFh.SmArTtEcHzAaL.iNfO&type=ws&host=&path=/%3Fed%3D2048HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.5:2096?flow=&encryption=none&security=tls&sni=TzS7v35LfD.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@5.10.214.5:8443?flow=&encryption=none&security=tls&sni=TjLwH7cTdH.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
trojan://BxceQaOe@58.152.110.50:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117香港 
trojan://BxceQaOe@58.152.53.219:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117香港 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@68.64.176.135:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjgyLjE5OC4yNDYuOTciLCJwb3J0IjoxODAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMTfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6ImQxM2ZjMmY1LTNlMDUtNDc5NS04MWViLTQ0MTQzYTA5ZTU1MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidC5tZS9yaXBhb2ppZWRpYW4iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://08c7f096-d057-4d53-82fd-c739d372887b@92.60.70.36:2053?flow=&encryption=none&security=&sni=&type=tcp&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117土耳其 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@api.dark-coffe.com:443?flow=&encryption=none&security=tls&sni=GfV5t2331T.sMaRtTeChZaAl.InFo&type=ws&host=GfV5t2331T.sMaRtTeChZaAl.InFo&path=/&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@api.dark-coffe.com:2087?flow=&encryption=none&security=tls&sni=5JxGp6VrFh.SmArTtEcHzAaL.iNfO&type=ws&host=&path=/%3Fed%3D2048HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN--HiByeVPNN&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@api.dark-coffe.com:2096?flow=&encryption=none&security=tls&sni=TzS7v35LfD.sMaRtTeChZaAl.InFo&type=ws&host=TzS7v35LfD.sMaRtTeChZaAl.InFo&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0117德国 
vless://7e58699f-1d5d-4f6b-b181-cb74f0ad9509@api.dark-coffe.com:8443?flow=&encryption=none&security=tls&sni=TjLwH7cTdH.sMaRtTeChZaAl.InFo&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://3e2e3c21-3fc8-468f-9ab5-e782bdf5bf97@cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=l.ayovo.netlib.re&type=ws&host=l.ayovo.netlib.re&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTphZWQ2ZTY4Ny01OGE5LTQ4MzYtYmE2Mi03ZDgxODRjOTRkZjQ=@hk13.network-cdn-gw-yd.net:32061?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0117香港 
vless://63f92f3c-447c-4283-80b9-0af8e164cdad@octopusss5.info:22955?flow=&encryption=none&security=reality&sni=one-piece.com&type=grpc&host=&serviceName=grpc&mode=gun&alpn=&fp=chrome&pbk=9Mt_Y8J_qDb1khlieWnhDSAq-kGtLHw6aOKgkAzOMms&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117奥地利 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@saas.sin.fan:2096?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://b5dbd0aa-22f6-4a00-9bcc-3606fa8fc56d@staticdelivery.nexusmods.com:443?flow=&encryption=none&security=tls&sni=kb.as129394.me&type=ws&host=kb.as129394.me&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117韩国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZGFjZC5jb20iLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDExN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMDExN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ2MTIuaGRhY2QuY29tIiwicGF0aCI6Ij9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@v2.dabache.top:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZGFjZC5jb20iLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDExN+W+t+WbvSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjoyLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://55d9ec38-1b8a-454b-981a-6acfe8f56d8c@www.visa.com:443?flow=&encryption=none&security=tls&sni=sni.meibidi.pp.ua&type=ws&host=sni.meibidi.pp.ua&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@198.41.201.41:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@103.21.244.164:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@tumefy.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=tumefy.oceanof.xyz&type=xhttp&host=tumefy.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@104.19.135.80:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTMyNGI5MDktNWRjYi00NzBmLTliODgtMzIwM2RlNmQ2NzQ5QDQ1LjgyLjEyMC4yMzg6NTA1ODI6d3M6L0hTTWR4RmlIR0hNUlZqeEFKeCUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0117德国 
vless://51551189-e8eb-467a-a611-5135fe663f79@45.82.120.238:39480?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/p21%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMzgiLCJwb3J0Ijo2MTY4NCwic2N5IjoiYXV0byIsInBzIjoiMDExN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlYzY2N2ViMy0yZjIwLTQ1MDEtYjVhOS02MjIyMjJiNTA5NDEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwicGF0aCI6Ii93a2t6a25qbUFwM3lVT2lnYUd2OXE/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://q2nemHtgtr1R0aD7PVNa3Nnnpucz@45.82.120.238:58335?insecure=1&sni=www.digitalocean.com&alpn=h2&fp=&os=#0117德国 
vless://eb0177d1-da1b-44b5-a653-5364d11ceb37@45.82.120.238:11512?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/OpjIXWzv4Vd9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@stripped.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=stripped.oceanof.xyz&type=xhttp&host=stripped.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@nnium.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=nnium.oceanof.xyz&type=xhttp&host=nnium.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
hysteria2://uFV6d9GURMAxtXqLU4CL9T9@45.82.120.238:15089?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=Nwuc6DDgeMyyVQqpib&mport=&os=#0117德国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@104.27.104.179:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
trojan://ba0f6256-2865-45e4-af9f-9e0e01c7e809@45.82.120.238:13067?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/f4vIVNJ%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@173.245.59.153:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@airon.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=airon.oceanof.xyz&type=xhttp&host=airon.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://4ffeb538-72d7-4064-b614-ff3b21636b7d@dedicate.oceanof.xyz:443?flow=&encryption=none&security=tls&sni=dedicate.oceanof.xyz&type=xhttp&host=dedicate.oceanof.xyz&path=/%3Ftelegeam-%40v2_city&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117美国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@104.16.139.79:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 
vless://432df1c2-d01b-4687-b65a-5c4f2ce56b3b@162.159.130.238:443?flow=&encryption=none&security=tls&sni=4b.34892.qzz.io&type=xhttp&host=4b.34892.qzz.io&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0117德国 


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
