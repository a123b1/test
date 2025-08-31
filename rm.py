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

vmess://eyJ2IjoiMiIsImFkZCI6IjEwMi4xMzIuMTg4LjI0OSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MzDnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNTNlYzU0NzEtNTMyZC0zNzFmLWE0OTktYzE1MjAwNjQ5M2I4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@102.177.189.251:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.182.191:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830香港 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.160.204.145:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.129.167.161:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.16.80.73:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=gun&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://ccbe6b7c-9264-40c4-8bc1-ef8f6205d7a4@104.17.147.22:8443?flow=&encryption=none&security=tls&sni=hetzner-8.cache.name.ng&type=ws&host=hetzner-8.cache.name.ng&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830芬兰 
vless://f19ed531-81cb-433e-8746-1a69e009f9df@104.18.13.145:443?flow=&encryption=none&security=tls&sni=usa.rtot.me&type=ws&host=usa.rtot.me&path=/bing&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://a4291a2a-d62c-4eb9-ac7a-ac7355d1eda2@104.21.24.195:443?flow=&encryption=none&security=tls&sni=9999UUuU.999836.XYZ&type=ws&host=9999uuuu.999836.xyz&path=/MIrEVIUviSe8ydvnmRKWDa8&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@104.21.3.219:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.26.2.186:443?flow=&encryption=none&security=tls&sni=pqh31v7.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@104.26.3.186:443?flow=&encryption=none&security=tls&sni=vp33.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://66683d2c-ae9c-427e-be17-4aa54a248d7b@104.26.6.89:443?flow=&encryption=none&security=tls&sni=parsdl.xyz&type=ws&host=nb-de.parsdl.xyz&path=/hajmi&headerType=none&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=tlshello,1-10,0-1&os=#0830德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@134.209.147.198:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830印度 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@154.83.2.167:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.63.177:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830韩国 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://27b61a3e-ef8c-4bc8-923f-f4ac433d1056@157.230.16.250:50395?flow=&encryption=none&security=&sni=&type=kcp&host=&seed=K1nVjOzkLe&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
hysteria2://7GEEGxAfgQaVPQX0PGk7lIuj3I@158.41.110.234:10820?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0830英国 
vless://d8dd94fd-540e-461d-b5d4-acebef02c22a@158.41.110.94:34045?flow=&encryption=none&security=reality&sni=visit-this-invitation-link-to-join-tg-enkelte-notif.ekt.me&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=cDaDzPr3PlS3NM8lreHZbdo-Mhqz8vMBzMSkHXhGIUA&sid=e8ab71d0&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE2NS4xNDAuMjE2LjE0MSIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDgzMOe+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiZTdkNzJhOGQtMjZmMi00YjU0LWIzNjYtMGM0M2UwYmNiYTdkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://45471789-5063-4721-949a-7d3fdaa07b9f@165.227.149.23:49968?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
hysteria2://peEduuHzbExjK7UQHzazXwqgA@166.88.164.9:27704?insecure=1&sni=bing.com&alpn=&fp=&mport=&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@167.68.42.168:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://bcf2fc80-a116-4ac5-9b28-953ae97a9f2b@172.238.117.145:2020?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.speed.cloudflare.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=rOvec6JPMjotfQPOFZbfNWo97CmogfIUgmtbG_MXwis&sid=cd4dbb5b68dfd2a6&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
hysteria2://6b65de44-e010-4044-abb5-9b25af54292a@172.252.236.213:49303?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830法国 
hysteria2://e31ad3e6-e341-42ac-bdc7-bea02d126fc1@172.252.236.213:49303?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830法国 
hysteria2://80b2ac81-ba69-41f9-bb46-820b7b3af4dd@172.252.236.213:49303?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830法国 
hysteria2://48c2c901-72e6-46d4-ac78-169d73264cbf@172.252.236.213:49303?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830英国 
vless://ce921385-2b31-45fe-84c5-1843e8ae845b@172.67.149.202:443?flow=&encryption=none&security=tls&sni=LlLLLlLLLLLkjh.222560.xyZ&type=ws&host=lllllllllllkjh.222560.xyz&path=/1xrOld7e5RpK3I98dxLkez&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4xNTAuMTMyIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwODMw576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjIwZTg5YTk1LWNlZGYtNGZlMy05NDIxLTUxN2NlNjZiZTE3MCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZWVlZGRjdmZnLjQ0NDY4Mi54eXoiLCJwYXRoIjoiL1NIVG9SY3FmaXJhWWt6T2RmIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZWVlZGRjdmZnLjQ0NDY4Mi54eXoiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://57ba2ab1-a283-42eb-82ee-dc3561a805b8@172.67.153.156:8443?flow=&encryption=none&security=tls&sni=ovhwuxian.pai50288.uk&type=ws&host=ovhwuxian.pai50288.uk&path=/57ba2ab1&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830韩国 
vless://401374e6-df77-41fb-f638-dad8184f175b@172.67.68.36:443?flow=&encryption=none&security=tls&sni=pqh23v2.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yNDAuMjQ1LjI1MCIsInBvcnQiOjQ3MjcyLCJzY3kiOiJhdXRvIiwicHMiOiIwODMw576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpueDB0NzI4cTNBZmZmd1JvMHE0bjFK@185.110.217.66:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
hysteria2://6b65de44-e010-4044-abb5-9b25af54292a@185.126.255.78:43429?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830乌克兰 
hysteria2://0cb527d9-6117-4bcf-a52b-1704b3458cef@185.126.255.78:43429?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830乌克兰 
hysteria2://c6e02cd8-ce11-40f0-afeb-e2c412b6cc3a@185.126.255.78:43429?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830乌克兰 
hysteria2://45cc0b3a-0adb-4dcc-8f54-4ba3d2cc274e@185.126.255.78:43429?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830乌克兰 
hysteria2://9c859345-959f-491b-b6fc-65cd7a57aeb3@185.126.255.78:43429?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#0830乌克兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830波兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@185.59.218.168:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://3b82c3ef-d428-4a62-ae97-f53c305f883d@188.245.39.111:48889?flow=&encryption=none&security=&sni=&type=tcp&host=speedtest.net&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830荷兰 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192.227.152.86:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&mport=&os=#0830美国 
vless://6c11247b-6078-461a-93d5-22e4df284e6d@198.62.62.229:443?flow=&encryption=none&security=tls&sni=mirror.fullmargintraders.com&type=ws&host=mirror.fullmargintraders.com&path=/wsv/6c11247b-6078-461a-93d5-22e4df284e6d&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://784646e5-8e84-4672-8670-efc9cafcd2cc@212.95.34.12:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://784646e5-8e84-4672-8670-efc9cafcd2cc@212.95.34.27:443?flow=&encryption=none&security=tls&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTplaGMzUzJpUXFCa25Gckw2SWVjQXAy@213.111.128.57:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830法国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpCMDNyaTdZb0p3TWpUZjU1YmVuWTBY@213.183.48.134:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0830俄罗斯 
vmess://eyJ2IjoiMiIsImFkZCI6IjI1LjEyOS4xOTYuMjQ5IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDgzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJkNWVkMzIzYy0wMTllLTM3YzctYjdhNy1jZjdkYzY5OWU5YzQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnMyLmRiLWxpbmswMi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjI1LjEyOS4xOTcuMjQ5IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDgzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI4Yzc1N2NmOC1kMjZjLTM0MmMtOTBjYS00NWI0NTVkNTVjYTgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnMyLmRiLWxpbmswMi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjI1LjEyOS4xOTkuMjQ5IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDgzMOe+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJiNDE3YzU2Ni05MmM1LTM0ZGQtYjMyNC0xYTMyOTU5Y2NkOGYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnMyLmRiLWxpbmswMi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://05519058-d2ac-4f28-9e4a-2b2a1386749e@3.74.129.76:22224?flow=&encryption=none&security=tls&sni=trojan.burgerip.co.uk&type=ws&host=&path=/telegram-channel-vlessconfig&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
trojan://telegram-id-directvpn@3.74.129.76:22223?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjEyLjMxLjIyNCIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA4MzDnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiN2E2MWNiMWMtZTVlYS0zMWVmLWI4ODUtMDAxODM5MGVlYzVlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiVEcuV2FuZ0NhaTIuczQuZGItbGluazAyLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.159.218.165:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.86:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://3c1c08fd-4755-454a-9746-72efc50249ed@45.91.81.111:8881?flow=&encryption=none&security=reality&sni=addons.mozilla.org&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=gupSTIXodm3AFVUeU6rfxp_2jID7P7FK_I6CjyLO2ns&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://0878df61-09ac-4c68-af57-db1523e9fd3b@46.31.76.33:868?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
hysteria2://79c4fe11-9787-406b-bf94-c1c1dbf59e28@77.223.214.193:31468?insecure=1&sni=www.bing.com&alpn=&fp=&mport=&os=#0830德国 
vless://2a9ed01e-5455-44b4-a66a-76ee8165f0ac@77.73.232.61:19747?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=ZO9dTeg1slvTXgVsBsaJ1BDvz_YUImTLJjbHs-GdVyM&sid=2001&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830哈萨克 
vless://TELEGRAM-CONFiGLiNE@83.136.254.131:443?flow=&encryption=none&security=reality&sni=stackoverflow.com&type=grpc&host=&serviceName=telegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE%2Ctelegram-CONFiGLiNE&mode=gun&alpn=&fp=chrome&pbk=dMcDsJc1oYAr-1f45ZfQLEjvkUVwTJD1R6-uWXUgUkY&sid=a7cc00af65e84b&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#0830英国 
vless://18ce358e-b507-4cde-8c83-94806aedf467@85.239.53.46:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=stackoverflow.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=nyid7jiXERXF6qkkRVsub0wfX9xGKKAsVzQERxhqZHc&sid=c8e8e4b7&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@89.116.180.248:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://00651706-0d2d-448b-80f2-7678f3e5187c@93.185.158.14:443?flow=&encryption=none&security=tls&sni=uk.rtot.me&type=ws&host=uk.rtot.me&path=/bing&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830英国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.140.0.141:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vless://54559d31-a4f0-4648-beeb-8323045a36c8@cb14.connectbaash.info:4414?flow=&encryption=none&security=&sni=&type=tcp&host=varzesh3.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://789d4f30-c31b-4762-8116-ed42574d5e85@cdn25.saloonak.ir:8443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://b4b8aa1f-77d2-4851-a5a4-f78886f3e997@deu246.bypassall.org:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.bing.com&type=tcp&host=---&path=&headerType=none&alpn=&fp=chrome&pbk=BhTJ3phnq-Z-10aFKSsj1lzhA8mULR4L6leE4-0WTAs&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830荷兰 
vless://5c1bf6a3-d378-45c8-b1fa-f94a256380cf@gzyd.cg.xxality.cn:35000?flow=xtls-rprx-vision-udp443&encryption=none&security=tls&sni=cggb.hysality.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0830英国 
vmess://eyJ2IjoiMiIsImFkZCI6ImhrdC5nb3RvY2hpbmF0b3duLm5ldCIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwODMw6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6IjkzZmI2OWZjLTc3Y2YtMTFlZS04NWVlLWYyM2M5MTM2OWYyZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiaGt0LmdvdG9jaGluYXRvd24ubmV0IiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://b4539287-4fb2-4baa-a522-c7212a1207fc@holn.xmonys.com:625?flow=&encryption=none&security=&sni=&type=tcp&host=zhaket.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830荷兰 
vless://66683d2c-ae9c-427e-be17-4aa54a248d7b@ipw.gfdv54cvghhgfhgj-njhgj64.info:443?flow=&encryption=none&security=tls&sni=zzula.ir&type=ws&host=nb-de.zzula.ir&path=/hajmi&headerType=none&alpn=http/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,1-10,0-1&os=#0830德国 
vless://a8749fa0-2f18-4ccd-a6d0-81c996e0fefa@lopp.mciickoir.ir:9620?flow=&encryption=none&security=&sni=&type=tcp&host=&path=/&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830英国 
vless://e1e72956-40dc-4211-864f-fcef0b0c2a9d@mci.itbookshop.sbs:443?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://a8749fa0-2f18-4ccd-a6d0-81c996e0fefa@sd.mciickoir.ir:9620?flow=&encryption=none&security=&sni=&type=tcp&host=&path=/&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://472bde55-7a33-45a5-e0f2-713160432c6d@sia.ziv.bahmannn.shop:1001?flow=&encryption=none&security=reality&sni=ea.com&type=tcp&host=&path=/&headerType=http&alpn=&fp=chrome&pbk=UhQ4jCERmj1tVoBOTio7icwyOkVkRPYcwxQEyzFeMGs&sid=&spx=/join_telegram-&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://88538870-5626-4cd7-9cda-1e0b6253c9ce@tgju.org:443?flow=&encryption=none&security=tls&sni=6389113402676776506.VtNeT.infO&type=ws&host=6389113402676776506.VtNeT.infO&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://b4539287-4fb2-4baa-a522-c7212a1207fc@uk.hotspoto.news:625?flow=&encryption=none&security=&sni=&type=tcp&host=zhaket.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwODMw576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwODMw5oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://ccbe6b7c-9264-40c4-8bc1-ef8f6205d7a4@www.speedtest.net:8443?flow=&encryption=none&security=tls&sni=lease-20.access.name.ng&type=ws&host=lease-20.access.name.ng&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830英国 
hysteria2://YJVR5swOvxYhr0zesQFfEXgUWTVvM8Xq9HNX6Y9I@45.82.121.53:55297?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=uBoCSepc8FVG5SvOrE5vhtsUbfwJYev&mport=&os=#0830德国 
hysteria2://4Au0b0WhanaIqkFBURJ2mWnj2IZZ1TD7VOs7ZW@45.82.121.53:46354?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=zb8s2caVCtOTlRbfCh&mport=&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@141.101.113.112:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZmYxNzJjNzEtMjJhOC00YThkLTg2MTctNzc0NmY5ZDIxMDIyQDQ1LjgyLjEyMS41MzoyMzY3Mzp3czovaEYzVTBPRGtOd3ZLeDBzVFRuUEE0WVklM0ZlZCUzRDI1NjA6YnVyZ2VyaXAuY28udWs6bm9uZTp0bHM6YnVyZ2VyaXAuY28udWs6W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@198.41.203.120:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS41MyIsInBvcnQiOjUyODM4LCJzY3kiOiJhdXRvIiwicHMiOiIwODMw5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjJhNWNkMjg0LWE3MWUtNGZjMC04YWU5LWU5YWU2NjZlYjcxOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYnVyZ2VyaXAuY28udWsiLCJwYXRoIjoiL2c2P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJidXJnZXJpcC5jby51ayIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://gr4HFA8K6EpwGmRAJdXmXPAksNJVD@45.82.121.53:60054?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=xF2RkFctKnQQkeHEireYH5Eh&mport=&os=#0830德国 
trojan://5f30d955-1aa0-4ef0-a276-adbb6c315b24@45.82.121.53:17694?flow=&security=tls&sni=burgerip.co.uk&type=ws&header=none&host=burgerip.co.uk&path=/cOfQYANlY9oao7Dqb368OlI5z%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjI2YWUxMmYtZDQ1Ny00YWM0LWI3YTQtNTQ0NmE1NGJjYjM0QDQ1LjgyLjEyMS41MzoxMTgxNDp3czovVnhpT1YyZmxGeDNPTkVaell2VGNDbkw1JTNGZWQlM0QyNTYwOmJ1cmdlcmlwLmNvLnVrOm5vbmU6dGxzOmJ1cmdlcmlwLmNvLnVrOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@162.159.128.248:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
anytls://Kxt9Sht0kfyzl1rgNqhixmfneodHFAP@45.82.121.53:24477?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0830德国 
anytls://GCnPeKndJHTrVba5Ba571oF1RyNbAnJD8ouZMl@45.82.121.53:38495?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#0830德国 
hysteria2://lnDTQVAeudv0cW60gmEYUZ2e0s92L21@45.82.121.53:64310?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=IlzNASnRGeE6tack431W2LrOCg6cO8dg&mport=&os=#0830德国 
hysteria2://PsMrhiqMFcrHP51Eo74WRUObJrEiBHi89TPzFyB@45.82.121.53:30989?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=P42aic0HewMzA3xG8XhHy0&mport=&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@108.162.192.139:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.26.13.81:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.6:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@103.21.244.150:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@190.93.247.114:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@190.93.244.134:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.18.108.128:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.59.110:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.19.204.212:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.19.243.241:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@173.245.49.233:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 
vless://30f01e9f-7d32-48b2-a21c-e034064374dc@104.23.117.19:443?flow=&encryption=none&security=tls&sni=real.ujhyidfghj.dpdns.org&type=xhttp&host=real.ujhyidfghj.dpdns.org&path=/ZETj2YLh24mig7%3Fed%3D2560&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0830德国 



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
