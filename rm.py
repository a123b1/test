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

hysteria2://dongtaiwang.com@51.159.111.32:31180?insecure=1&sni=apple.com&alpn=&fp=&mport=&os=#0717法国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjNDA2NDFjMWY4OWU3YWNi@62.133.63.212:57456?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717土耳其 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMSIsInBvcnQiOjQ5OTEyLCJzY3kiOiJhdXRvIiwicHMiOiIwNzE3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMSIsInBvcnQiOjU5MjIyLCJzY3kiOiJhdXRvIiwicHMiOiIwNzE3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vless://aaaaaaa1-bbbb-4ccc-accc-eeeeeeeeeee1@web.xhamster.biz.id:443?flow=&encryption=none&security=tls&sni=web.xhamster.biz.id&type=ws&host=web.xhamster.biz.id&path=/Free-CF-Proxy-AT30&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vmess://eyJ2IjoiMiIsImFkZCI6InY4LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA4LCJzY3kiOiJhdXRvIiwicHMiOiIwNzE36aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjguaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwNzE35Lit5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDcxN+S4reWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMDcxN+S4reWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InR3anhsbm5vbGp4YzIuamtoa2dqLnh5eiIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzE35Y+w5rm+IiwibmV0Ijoid3MiLCJpZCI6IjNjZjc5YmNhLTQxZTMtNDdkNS1iYTY3LTg3YTY5YTFhOWU1OSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZmlsZS5kaW5ndGFsay5jb20iLCJwYXRoIjoiL21hcmtldC90dz9lZD01MTIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjNDA2NDFjMWY4OWU3YWNi@tr.vpnsparta.pro:57456?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717俄罗斯 
trojan://74260628090146500@stirring-parakeet.shiner427.skin:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717英国 
vmess://eyJ2IjoiMiIsImFkZCI6InNzc3Nzc3NzdmFlMi5qa2hrZ2oueHl6IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MTfpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiM2IwYWQ3YWItNTdmOS00ZGIyLTk4ZGMtZGFjY2M5ZDU5MzhlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJmaWxlLmRpbmd0YWxrLmNvbSIsInBhdGgiOiIvbWFya2V0L2hrP2VkPTUxMiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p222.panda001.net:15098?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717中国 
vless://55520747-311e-4015-83ce-be46e2060ce3@join.my.telegram.channel.cmliussss.to.unlock.more.premium.nodes.cf.090227.xyz:443?flow=&encryption=none&security=tls&sni=xy.bgm2024.dpdns.org&type=ws&host=xy.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=h3&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vmess://eyJ2IjoiMiIsImFkZCI6Imh5dHR0dGVzZ3Z2eGIyLmpraGtnai54eXoiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDcxN+mmmea4ryIsIm5ldCI6IndzIiwiaWQiOiI2ZTJjNzdiNC1jMzRiLTRmYjQtOTE4Ny0wODc0MmViMGJhMmUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImZpbGUuZGluZ3RhbGsuY29tIiwicGF0aCI6Ii9tYXJrZXQvanAxP2VkPTUxMiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://74260628090146500@huge-turkey.shiner427.skin:443?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717约旦 
trojan://74260628090146500@ample-koi.shiner427.skin:443?flow=&security=tls&sni=ample-koi.shiner427.skin&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0717印度 
vless://55520747-311e-4015-83ce-be46e2060ce3@69.84.182.89:443?flow=&encryption=none&security=tls&sni=xu.bgm2024.dpdns.org&type=ws&host=xu.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vless://55520747-311e-4015-83ce-be46e2060ce3@63.141.128.88:443?flow=&encryption=none&security=tls&sni=xy.bgm2024.dpdns.org&type=ws&host=xy.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vless://55520747-311e-4015-83ce-be46e2060ce3@63.141.128.3:443?flow=&encryption=none&security=tls&sni=xy.bgm2024.dpdns.org&type=ws&host=xy.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vless://55520747-311e-4015-83ce-be46e2060ce3@63.141.128.140:443?flow=&encryption=none&security=tls&sni=xy.bgm2024.dpdns.org&type=ws&host=xy.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=h3&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
vless://55520747-311e-4015-83ce-be46e2060ce3@63.141.128.102:443?flow=&encryption=none&security=tls&sni=xy.bgm2024.dpdns.org&type=ws&host=xy.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=h3&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
ssr://NjIuMTAwLjIwNS40ODo5ODk6b3JpZ2luOmFlcy0yNTYtY2ZiOnBsYWluOlpqaG1OMkZEZW1OUVMySnpSamh3TXc9PS8/b2Jmc3BhcmFtPSZwcm90b3BhcmFtPSZyZW1hcmtzPU1EY3hOK2lMc2VXYnZRPT0mb3M9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717英国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.23.63:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717英国 
vless://401374e6-df77-41fb-f638-dad8184f175b@45.8.211.71:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717英国 
vless://55520747-311e-4015-83ce-be46e2060ce3@45.67.215.92:443?flow=&encryption=none&security=tls&sni=xu.bgm2024.dpdns.org&type=ws&host=xu.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717俄罗斯 
hysteria2://dongtaiwang.com@45.129.2.108:50850?insecure=1&sni=www.bing.com&alpn=&fp=&mport=&os=#0717俄罗斯 
vless://55520747-311e-4015-83ce-be46e2060ce3@43.165.191.25:23023?flow=&encryption=none&security=tls&sni=xu.bgm2024.dpdns.org&type=ws&host=xu.bgm2024.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=h3&fp=random&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@38.54.57.90:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0717美国 
hysteria2://krPSxf8KODI2xsJkmhp19f8CRIfqxX@109.71.253.98:27377?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=dxDpZ1sLdx4JirbLUlJ1tXBGZmT20uascjZf&mport=&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.8.33:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
hysteria2://Dr3ks59KnjHEX82AIRKBf4TfI9ArfoPPfzQps4@109.71.253.98:64131?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=odgqjwuRNKK3afYiDUO8hkZ6EAO1HGlJC&mport=&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.8.8:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.97.75:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
hysteria2://kAZzXrYsqscCoR7G3z@109.71.253.98:9337?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=hkEPzarMhmJDFkQz3moA&mport=&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.35.78:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
hysteria2://eYopKxunYdQ3dULBdekTgtDdHPsp@109.71.253.98:56446?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=RdX73CFlEM3cYMZLnTlH3BQV1AdxdVrwAb6Z&mport=&os=#0717德国 
hysteria2://fknkpbVJeDGdJpyh0sA@109.71.253.98:55850?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=2rOcZBRiEii5eWwY&mport=&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@190.93.246.68:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.123.23:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.59.98:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.115:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
anytls://J5aqeFJ9h0F8TFMomBIwhVDOzg9c6qJhchxgjEf@109.71.253.98:33309?insecure=1&sni=high.work.lzg.me&alpn=h2&fp=&os=#0717德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YjljZGE5N2QtM2IwOC00M2I5LWE2ZDItOWI3M2YxYmVhNGY2QDEwOS43MS4yNTMuOTg6MTU5NzY6d3M6LzZ6eVdwNHJnJTNGZWQlM0QyNTYwOmhpZ2gud29yay5semcubWU6bm9uZTp0bHM6aGlnaC53b3JrLmx6Zy5tZTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0717德国 
hysteria2://j9BgFycuHzHq3Rs7PJHXCHIdIv4W5wVnZ0PADi@109.71.253.98:3961?insecure=1&sni=high.work.lzg.me&alpn=&fp=&obfs=salamander&obfs-password=vJoNr0eHFuYHJjtbW9kMlJ2BXepP&mport=&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.3:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://d93dc0d8-d10e-4e60-b985-4c14805fe15e@109.71.253.98:28055?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/EwOJupJAkNZBGxDUnvAZiJj1%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.184.190:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.245.122:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.179.173:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://f6cc439c-4cda-4077-a33e-f19ea940e535@109.71.253.98:37621?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/l0Oge2wdq1deLhxhr61sWlPDSod8c%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.226.97:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.170:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.22.35.167:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.8.51:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.209.156:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@141.101.121.246:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.213.255:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.209.113:443?flow=&encryption=none&security=tls&sni=v8.vock33.qzz.io&type=xhttp&host=v8.vock33.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0717德国 
 
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
