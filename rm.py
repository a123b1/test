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

vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI05Lit5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY3LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA3LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI0576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJvY2JjLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY2LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA2LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI0IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY0MC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDg0MCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwicGF0aCI6Ii9pbmRleCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImFwaTEwMC1jb3JlLXF1aWMtbGYuYW1lbXYuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDQyNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6Im9jYmMuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJhaWR1LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@us04.ijgelrkasd.click:44130#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@us03.jigreliewolf.click:43330#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@us02.jgrtoioceaw.help:44907#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@us01.jgrtoioceaw.help:48129#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@tw02.ijgelrkasd.click:22610#0424台湾 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@tw01.jigreliewolf.click:30995#0424台湾 
trojan://802ab87d-b427-4334-b789-f00949d917c4@sla.cn.964e995b760.gogodns.xin:22271?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424日本 
trojan://24d15505-30d1-4b32-a4e4-3797699939ed@sla.cn.964e995b760.gogodns.xin:22269?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424日本 
trojan://481fa6e1-94ad-4613-afec-de356e2e7d4e@sla.cn.964e995b760.gogodns.xin:43383?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424马来西亚 
trojan://5db9b45b-e4be-4ad6-b50c-1342d907cc21@sla.cn.964e995b760.gogodns.xin:33506?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://a884ae5e-c0c6-482c-b59e-61c6c6911023@sla.cn.964e995b760.gogodns.xin:27001?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://851f12e2-4a5e-407c-af77-2b05968e6d61@sla.cn.964e995b760.gogodns.xin:43592?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://9a12f453-71e7-4778-a9ad-fb057fb70bff@sla.cn.964e995b760.gogodns.xin:43591?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://82d028c4-bb90-42df-9a2e-268fbb69ca5d@sla.cn.964e995b760.gogodns.xin:42882?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://0537f6e2-c69e-4a26-a44f-0744bbd91e73@sla.cn.964e995b760.gogodns.xin:43394?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://ea6025a3-a4f7-44c4-855f-9a9754e8327e@sla.cn.964e995b760.gogodns.xin:46926?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://147c2fdf-2e05-4595-9ed1-87bc0305e67b@sla.cn.964e995b760.gogodns.xin:34017?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://ce4ba710-f050-4234-9ba5-4104e12a41d1@sla.cn.964e995b760.gogodns.xin:44397?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://71e539de-1358-49f2-b8af-e9a37255dc59@sla.cn.964e995b760.gogodns.xin:43393?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://2d3d96a4-6f61-4f70-a248-f6d9d4eaa7bd@sla.cn.964e995b760.gogodns.xin:27401?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424新加坡 
trojan://3e53dc4b-d573-4aaa-8bad-a568e8921ab1@sla.cn.964e995b760.gogodns.xin:42881?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424新加坡 
trojan://4d6167d1-ecff-4ed4-ab2c-e8d979702007@sla.cn.964e995b760.gogodns.xin:43397?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424土耳其 
hysteria2://369745b1-46a1-4794-9bdf-7ba7c673ff22@sg05.tkgow.top:8080?insecure=0&sni=&alpn=&fp=&os=#0424新加坡 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@sg04.jgrtoioceaw.help:17971#0424新加坡 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@sg03.ijgelrkasd.click:23716#0424新加坡 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@sg02.jigreliewolf.click:40574#0424新加坡 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@sg01.jgrtoioceaw.help:55559#0424新加坡 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@my02.ijgelrkasd.click:25519#0424马来西亚 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@my01.jigreliewolf.click:52408#0424马来西亚 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@ko02.jigreliewolf.click:50181#0424韩国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@ko01.jgrtoioceaw.help:46108#0424韩国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@jp04.ijgelrkasd.click:58223#0424日本 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@jp03.jigreliewolf.click:33414#0424日本 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@jp02.jgrtoioceaw.help:47462#0424日本 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@jp01.jgrtoioceaw.help:58645#0424日本 
ss://YWVzLTEyOC1nY206Vk1oR3A1d0VJeUNEZjkwVA==@gysz0000.dynu.net:56277#0424印度 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@gb02.jigreliewolf.click:52762#0424英国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@gb01.jgrtoioceaw.help:27765#0424英国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@fr02.jigreliewolf.click:45265#0424法国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@fr01.ijgelrkasd.click:32568#0424法国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@de02.jigreliewolf.click:52770#0424德国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@de01.jgrtoioceaw.help:20635#0424德国 
hysteria2://82efba2c-f420-11ef-9529-f23c93141fad@d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk:443?insecure=0&sni=d7babeae-sudhc0-svm3vt-czv5.la.shifen.uk&alpn=&fp=&os=#0424美国 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=d7b8355e-suk9s0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
hysteria2://279b8588-616b-11ed-a8bf-f23c91cfbbc9@cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net:8443?insecure=0&sni=cdb71208-suk9s0-sv6oiy-1p1b.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@ca02.ijgelrkasd.click:24053#0424加拿大 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@ca01.jigreliewolf.click:30461#0424加拿大 
hysteria2://80aa5178-f936-11ed-8ce6-f23c91369f2d@c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net:8443?insecure=0&sni=c26d0357-supts0-tfvcxz-1nq4g.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
hysteria2://8de795d2-a06f-11ed-8edf-f23c913c8d2b@bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net:8443?insecure=0&sni=bec3dd81-suk9s0-sxv16d-1k09w.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
hysteria2://7af3db60-b2d9-11ef-88ab-f23c913c8d2b@b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net:8443?insecure=0&sni=b9a88fb8-suk9s0-t7qex7-1supq.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@au02.ijgelrkasd.click:46073#0424澳大利亚 
ss://YWVzLTEyOC1nY206MzY5NzQ1YjEtNDZhMS00Nzk0LTliZGYtN2JhN2M2NzNmZjIy@au01.jgrtoioceaw.help:13460#0424澳大利亚 
vless://459b4a80-bd61-4ecd-a26b-e9c1809d9e45@agaungzhou01.bumbleshrimp.com:31800?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.nvidia.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=qhTzYYIgBzDLNYR79oxftqdo1kzL-1_hGJKfqrOliCY&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424中国 
trojan://c702521f-8953-4bb0-95df-ec0479d68c1a@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27201?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424台湾 
trojan://ad0d6316-d25e-4fde-8945-938f6265a3d7@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:22269?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424日本 
trojan://20583ab9-4fc8-41eb-8468-f16734a55c6e@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:46668?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424韩国 
trojan://1e0a3f8d-dd1a-49f5-9d78-70f191f70ca4@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43396?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://59838af2-1171-4033-8686-02f2198d6f46@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27002?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://aecdedb2-7ed0-4a80-aac8-7e98925d212f@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27401?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://ba92259a-a946-4a96-83b2-fc295f77548e@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43583?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://7d7d5e58-409a-48f7-89bd-dede7cf908f6@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43394?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://3fc99bf3-69b6-4868-9fb6-1b8d2f160214@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:10465?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://42e81557-3749-4d0d-8def-2f730ff60b27@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43395?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://dabb4fca-ae9a-45e9-af87-d9602dc05ef7@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:34017?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://5e101fff-84cc-4e9c-a41d-68449a7b0bd8@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:43393?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424荷兰 
trojan://bd67d078-d885-4acb-99f8-4fdad34faf98@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:42881?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424新加坡 
trojan://3550a087-c802-47ee-84c2-508693b5cb7c@aafrtpfxr.jpl01i9zjfegelp.5xfsur8v62.gosdk.xyz:27202?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424台湾 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowUnNyY0ZKMXZPc1dFcWczUDU1aHZhYWNLZnVTaFQwY2MxaDB0OEFEME5BOHUxdVI=@92.38.171.215:31348#0424西班牙 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0424斯洛文尼亚共和国 
hysteria2://fb8812ae-dcb5-11ef-a57d-f23c9313b177@90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk:443?insecure=0&sni=90f6eaa0-sudhc0-syoixd-bm0y.la.shifen.uk&alpn=&fp=&os=#0424美国 
hysteria2://be8ba532-0dcf-11f0-9a65-f23c9164ca5d@8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net:8443?insecure=0&sni=8b21ebfd-suif40-tcvn0z-1tlyg.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjE4LjU4LjIwNiIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOWTpeS8puavlOS6miIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg5LjE4LjU2LjI0OSIsInBvcnQiOjE4MCwic2N5IjoiYXV0byIsInBzIjoiMDQyNCIsIm5ldCI6InRjcCIsImlkIjoiZDEzZmMyZjUtM2UwNS00Nzk1LTgxZWItNDQxNDNhMDllNTUyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpNV1l5Tg==@85.209.158.11:8388#0424美国 
hysteria2://c11ff50c-f582-11ee-94df-f23c9164ca5d@74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net:8443?insecure=0&sni=74f0ee85-suk9s0-swtza9-1q91p.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
hysteria2://564b440a-700f-11ee-a90c-f23c9313b177@71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk:443?insecure=0&sni=71845bc5-submo0-t0t1z3-1qgn.la.shifen.uk&alpn=&fp=&os=#0424美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0424英国 
hysteria2://2ee8f830-09e2-11f0-90e2-f23c913c8d2b@5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net:8443?insecure=0&sni=5f1f749e-suk9s0-tcmdts-1mmu6.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
hysteria2://4e84400e-f4bc-11ef-81b7-f23c932f2c32@57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk:443?insecure=0&sni=57ad5f46-submo0-sv7alj-ctxx.la.shifen.uk&alpn=&fp=&os=#0424美国 
hysteria2://3c461e2c-9d13-11ef-8563-f23c913c8d2b@4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net:8443?insecure=0&sni=4e4babe3-suk9s0-t234dm-eso8.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 
vless://1619b2f1-eb62-4550-86a2-3c2168c7c269@45.82.121.177:49367?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/wmNE%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://07271067-76e1-4cc5-994b-d9adc42763c6@45.82.121.177:4049?flow=&encryption=none&security=tls&sni=www.ameblo.jp&type=ws&host=www.ameblo.jp&path=/W1UlfU5YmTwtGwuNP3Y3pca%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
hysteria2://wXIAU0nf95SVS3NHmO5WGIJMpvkEKkp@45.82.121.177:34231?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=Jg9sV4cg0HFuJKT6dglSxlvxR&os=#0424德国 
hysteria2://dstDZsD5AspKxNyOv@45.82.121.177:29020?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=CcKNRN1oZGxBvQ2GX1zz84MzIFGl&os=#0424德国 
hysteria2://sFZtXrWnZs9VZtJKXxsk8N4hYhuaveaHLBt@45.82.121.177:55696?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=0DSgdXku5iJGluE4v9qLvVKsszZY5C&os=#0424德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xNzciLCJwb3J0IjoxMjU4Nywic2N5IjoiYXV0byIsInBzIjoiMDQyNOW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2ZjdjYzZiOC01OTJmLTRkYTgtOGQxNC01OGU2ZDhhZTIwNjIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5hbWVibG8uanAiLCJwYXRoIjoiLzh3Y3A4RktjWXNzdXVld2lwWjZOOTRydj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3LmFtZWJsby5qcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://d0f74ab1-5a26-4e40-997e-e09e45667f78@45.82.121.177:5215?flow=&security=tls&sni=www.ameblo.jp&type=ws&header=none&host=www.ameblo.jp&path=/W33YX8vd1MHMTLPAUSOVLqzZud6U%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
hysteria2://EYjdFFIw2AzYgEnsloSrKRDt@45.82.121.177:23678?insecure=1&sni=www.ameblo.jp&alpn=&fp=&obfs=salamander&obfs-password=eSn6D9nZhCzmJOmWd1cLUDb&os=#0424德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989#0424岛 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.144:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NC4xOTUuMTE3LjY2IiwicG9ydCI6MjkxNTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjQiLCJuZXQiOiJ0Y3AiLCJpZCI6IjVjMmVlODQyLThiZmYtNGViNi05OGViLTk4MWFjOGVlZjMyNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192-227-152-86.nip.io:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&os=#0424美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0424波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MzEyMSwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozNDY1Miwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTU1NCwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MzEyMSwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MTI5MSwic2N5IjoiYXV0byIsInBzIjoiMDQyNOaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://5453ae26-250d-4e79-b4ec-016baf806865@172.67.204.22:443?flow=&security=tls&sni=1SdfghJk.890602.xyz&type=ws&header=none&host=&path=/OYzPAeaZdXUq2d6J3gc4aj&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424美国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.45.147:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi4xMDQuMTgxLjE1NiIsInBvcnQiOjYzMzM0LCJzY3kiOiJhdXRvIiwicHMiOiIwNDI0IiwibmV0IjoidGNwIiwiaWQiOiI1YzJlZTg0Mi04YmZmLTRlYjYtOThlYi05ODFhYzhlZWYzMjUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.254.11:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://7c317161-5cf8-4cbc-811a-d1297c41bb23@152.67.68.116:443?flow=xtls-rprx-vision-udp443&encryption=none&security=tls&sni=yapc-1.afshin.ir&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424瑞士 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0MS4xMDEuMTIxLjEyNyIsInBvcnQiOjIwNTMsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTlnKPpqazlipvor7oiLCJuZXQiOiJ3cyIsImlkIjoiMzgxY2I2ZDEtNmFkNC00OTA5LTg0OTQtYjhkNzg2Y2Y3OGNlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIxNzQ0MDA3NTc4LnNwZWVkLm1hbWhhLmNjY3AuZnJlZWZseS5wcC51YSIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiMTc0NDAwNzU3OC5zcGVlZC5tYW1oYS5jY2NwLmZyZWVmbHkucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.115.238:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0424以色列 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0424孟加拉国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0424新加坡 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0424日本 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0424法国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEzOS4xNjIuNzUuMTEzIiwicG9ydCI6MzI4NTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjQiLCJuZXQiOiJ0Y3AiLCJpZCI6IjVjMmVlODQyLThiZmYtNGViNi05OGViLTk4MWFjOGVlZjMyNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEzOS4xNjIuNzUuMTEzIiwicG9ydCI6NTA2MDgsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjQiLCJuZXQiOiJ0Y3AiLCJpZCI6IjVjMmVlODQyLThiZmYtNGViNi05OGViLTk4MWFjOGVlZjMyNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://d431e60a-2a26-46ef-b0a8-644143727c12@138.197.44.242:52605?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424美国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@137.175.113.193:8388#0424美国 
trojan://VMhGp5wEIyCDf90T@123.88.148.42:42303?flow=&security=tls&sni=hk06.run.place&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424中国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6Mzc4MDUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDY1OTcsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6NDQ0OTEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzY2MDksInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTc4NTIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTEwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTAwODIsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6MzUwMDEsInNjeSI6ImF1dG8iLCJwcyI6IjA0MjTnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.151.253:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.22.22.57:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.95.192:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.235.139:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.110.201:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.206.167:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
vless://98feaab6-e89f-46eb-9224-0f973f03af3f@104.18.20.69:443?flow=&encryption=none&security=tls&sni=us1s.pqvip.top&type=ws&host=us1s.pqvip.top&path=/pq/us1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.109.184:443?flow=&encryption=none&security=tls&sni=www.secge.dpdns.org&type=xhttp&host=www.secge.dpdns.org&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0424德国 
hysteria2://203d1d64-3313-11ed-bb74-f23c9164ca5d@0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net:8443?insecure=0&sni=0e1462f1-sum4g0-t8ro7t-1ey07.hy2.gotochinatown.net&alpn=&fp=&os=#0424美国 

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
