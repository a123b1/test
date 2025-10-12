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


ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.183.154:8388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007香港 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.162:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.166:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.175:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.196:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.154.220:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.15:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.209:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.213:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.28:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.60:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.77:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007越南 
vless://6016845b-61d0-49c5-b20c-d61e860778d4@141.227.134.240:54983?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://98b988ba-fe55-402e-824a-6f7bb3436f22@141.227.136.11:11716?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://49ffd741-9736-40fb-9217-76a8fcfb3ffd@141.227.138.82:18541?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://7fe2935c-0b1a-4bff-a392-79081b23d820@141.227.140.55:51079?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://9b49cf25-e2f2-4ef6-9c54-ef0b785db804@141.227.180.39:22291?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.62.168:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007韩国 
vless://88b6ee92-883b-450c-a83d-77f71e1db388@155.254.35.78:16274?flow=&encryption=none&security=reality&sni=miro.com&type=xhttp&host=&path=/&mode=auto&alpn=&fp=chrome&pbk=MqVGNyGgn2-d-VrmwbViA73YFlfwe4O8Cu1qQqpOSXI&sid=f35490&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://951e35bf-fe55-410f-9ed3-815765188996@170.9.18.160:443?flow=&encryption=none&security=tls&sni=ks.lepc.vip&type=ws&host=ks.lepc.vip&path=/hybrid-dedicated-servers&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007美国 
hysteria2://d7ee9b93-b5b0-44e4-988a-dc3c465c0c9f@172.252.236.213:43649?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007瑞士 
hysteria2://f901861b-6491-450c-b500-606b2e921625@172.252.236.213:43649?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007法国 
hysteria2://ebbeef45-0fd8-40cd-aca5-1e2ce18abeff@172.252.236.213:43649?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007瑞士 
vless://afc9d688-520a-46fa-a98d-4511d1198cdd@172.67.131.76:443?flow=&encryption=none&security=tls&sni=EEeE3.222767.xYz&type=ws&host=eeee3.222767.xyz&path=/Bla4bwO5lnIT6TyxDFklcPSbclvX&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007美国 
hysteria2://d7ee9b93-b5b0-44e4-988a-dc3c465c0c9f@185.126.255.78:47230?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007乌克兰 
hysteria2://48c2c901-72e6-46d4-ac78-169d73264cbf@185.126.255.78:47230?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007乌克兰 
hysteria2://1045aedf-053c-4585-875d-e2fc3f3ea6dd@185.126.255.78:47230?insecure=1&sni=real.getafreenode.sbs&alpn=&fp=&mport=&os=#1007乌克兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007波兰 
vless://53fff6cc-b4ec-43e8-ade5-e0c42972fc33@193.151.135.21:44443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.speedtest.net&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=XHjKkrNBYXOaamOx8IUCrwX0zp5dAQRVErHiQ5bwAEQ&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://ed97e008-2b8d-4415-94c7-3da4919d361a@194.31.157.238:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007哈萨克 
hysteria2://dongtaiwang.com@208.87.243.187:22222?insecure=1&sni=www.bing.com&alpn=&fp=&mport=&os=#1007美国 
vless://81e9e522-2efd-4709-996d-74e46f4edaf8@213.176.94.129:443?flow=&encryption=none&security=reality&sni=www.amazon.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=flIlSQ8NWZl0ofim794-EaQhz2OnH1hN7imrQAPheRY&sid=53ba1e37&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007荷兰 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.237.185.230:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjM2LjEzOS4yMDEuMzUiLCJwb3J0IjoxMDAwMiwic2N5IjoiYXV0byIsInBzIjoiMTAwN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiOGQ3MTdlNWEtZGFiNS00Yjk5LWFmNGYtZWEyOWVmOGVlYmVkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://253bc477d4e43c209f2d427272968280@36.156.102.88:1801?flow=&security=tls&sni=www.nintendogames.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007日本 
vless://7ad71a16-f67c-410b-968e-187fd5b49f94@46.62.206.155:31000?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007芬兰 
vless://fc3d2ca2-0f38-48dc-8938-688b78c403f2@46.62.206.155:32000?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007芬兰 
vless://fe837fd0-840d-4cee-9334-0dc6c2b15c1c@5.181.20.219:17422?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=0r5rlmvACX09qUTPuxrbuKWSAn66NnNyHIfIMwalYAA&sid=33&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007芬兰 
vless://72c17850-c1a8-4915-a437-45de2645a6e1@51.89.230.180:25365?flow=&encryption=none&security=&sni=&type=grpc&host=&serviceName=ZEDMODEON-ZEDMODEON-ZEDMODEON-bia-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON-ZEDMODEON&mode=gun&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007英国 
ssr://NjIuMTAwLjIwNS40ODo5ODk6b3JpZ2luOmFlcy0yNTYtY2ZiOnBsYWluOlpqaG1OMkZEZW1OUVMySnpSamh3TXc9PS8/b2Jmc3BhcmFtPSZwcm90b3BhcmFtPSZyZW1hcmtzPU1UQXdOK2lMc2VXYnZRPT0mb3M9 
vless://8377aac9-f3b3-42df-a5ea-9254f37e7b34@62.133.63.138:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=tr.eu-ffast.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=-tePObR3oZwGAUOb5kqTYkNWl6rtUKl0RFuzuu06wgw&sid=50&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007土耳其 
vless://8377aac9-f3b3-42df-a5ea-9254f37e7b34@62.133.63.138:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=tr.eu-ffast.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=-tePObR3oZwGAUOb5kqTYkNWl6rtUKl0RFuzuu06wgw&sid=50&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007土耳其 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007斯洛文尼亚共和国 
vless://c80bbc09-837d-495f-bebc-3e8ac5dede41@91.147.92.153:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=hls-svod.itunes.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=mLmBhbVFfNuo2eUgBh6r9-5Koz9mUCn3aSzlR6IejUg&sid=f79448a30d&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007哈萨克 
vmess://eyJ2IjoiMiIsImFkZCI6IjkxLjk4LjE5My4xOTMiLCJwb3J0Ijo4MDgwLCJzY3kiOiJhdXRvIiwicHMiOiIxMDA35b635Zu9IiwibmV0IjoidGNwIiwiaWQiOiI3NWJjNjY4ZS01MGI0LTRjMzUtZjMzMS0xZjE0ZGM0ZmE1MjkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://2e532561-7a61-4fdf-a534-706682c2e209@94.143.231.62:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://8496c102-4094-4dd3-ad63-7bb7a35cbaee@94.182.137.12:20532?flow=&encryption=none&security=&sni=&type=tcp&host=Telewebion.com&path=&headerType=http&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://71504eaf-29ac-4190-89d1-dd9ce2c9ee14@backus1.dh03.shop:443?flow=&encryption=none&security=tls&sni=backus1.dh03.shop&type=ws&host=backus1.dh03.shop&path=/higate&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007美国 
vless://ed97e008-2b8d-4415-94c7-3da4919d361a@bridge.iskra-connect.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
ss://YWVzLTI1Ni1nY206ZTliMGZhMGItNzJmYi00OTkzLWEyNTEtOWY1MTg1MTJmZWM4@entrance02.qqa678.cc:47084?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007美国 
vless://8da7bd17-70ab-472d-a925-cc827857dc35@hk01.youyacloud.me:28888?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.tvb.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=slSuocOAiBpxoouM2bOV03TG7LRqrGyKDivA__DEric&sid=&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007香港 
vless://6006efbc-2751-44c5-8789-d38304d4303a@ico.org.uk:2087?flow=&encryption=none&security=tls&sni=frag2.mAhSaAMiNi.CC&type=ws&host=&path=/CPI&headerType=none&alpn=h2%2Chttp/1.1&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://0e8a6896-ad90-4a3b-89a3-77d64aa409e2@ilta-wzxrxkdhbjpnprhkkpplsjwawhssvollvxzdhqshiqckwdgrdm.orbnet.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=i2pd.website&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=YVDo7U4O-AT2fa5H9E7hyYHKgfZd1vB6UdbAf2ggWQE&sid=55e6af1a35e64a98&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007以色列 
hysteria2://62616dc7-6757-478f-b420-a63c3c5af8d0@kr1.aeccghuyjftyg.shop:20000?insecure=0&sni=&alpn=&fp=&obfs=salamander&obfs-password=fdrccJDGatdFDDRp&mport=&os=#1007韩国 
vless://ed97e008-2b8d-4415-94c7-3da4919d361a@kz.connect-iskra.ru:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007哈萨克 
vless://fe27c0c7-6602-4b20-a8e4-d8eff275dbee@lva-0001-xr.packet-drop-society.net:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=hls-svod.itunes.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=llaiqC-oIhL_bjc236FPq26LSn7IVhIa4cIC6OVytws&sid=31&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007立陶宛 
vless://fe27c0c7-6602-4b20-a8e4-d8eff275dbee@lva-0001-xr.packet-drop-society.net:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=hls-svod.itunes.apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=llaiqC-oIhL_bjc236FPq26LSn7IVhIa4cIC6OVytws&sid=31&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007立陶宛 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTozNjBlMjFkMjE5NzdkYzEx@pl.vpnsparta.pro:57456?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1007波兰 
vless://2e532561-7a61-4fdf-a534-706682c2e209@univovh.iskra-connect.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMTAwN+mmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMTAwN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyOSwic2N5IjoiYXV0byIsInBzIjoiMTAwN+iLseWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYyOS5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMTAwN+aWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIxMDA35oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY5LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA5LCJzY3kiOiJhdXRvIiwicHMiOiIxMDA36aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmFpZHUuY29tIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://c30ec165-fcb4-47af-8e68-70d88a3b2910@vpn-srv-2.circlevpn.net:37096?flow=&encryption=none&security=tls&sni=vpn-srv-2.circlevpn.net&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007法国 
vless://2b8f686c-a425-11f0-a31f-52540015866d@yofree.top:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=yofree.top&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=AWyicEDYi7KB3qzo8OEvEd1HK0gZhCHAENBd_buyhQk&sid=fa2f&spx=/&allowInsecure=1&fragment=,100-200,10-60&os=#1007荷兰 
vless://ed97e008-2b8d-4415-94c7-3da4919d361a@yt.connect-iskra.ru:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=deepl.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=V6i1V9804ZfgT8nutUwDs5IDQdcY9pK5uO075SW4ml4&sid=2d46a79deebf50fd&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007俄罗斯 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.59.77:443?flow=&encryption=none&security=tls&sni=sn.ckosuz.dpdns.org&type=xhttp&host=sn.ckosuz.dpdns.org&path=/ZETj2YLh24mig7%3FBla4bwBla4bwO5lnIT6TyxDFklcPSbclv%3FXO5lnIT6TyxDFklcPSbclvX&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
trojan://7795bea8-7fab-4f98-aed1-02b6b511019d@45.82.121.39:6004?flow=&security=tls&sni=api.namasha.co&type=ws&header=none&host=api.namasha.co&path=/gw7ZTAY94hhSa1s01AFZK%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://a73dcf71-cc2e-4c04-a74f-9ded78a512d6@109.71.253.8:61619?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/McwRZ%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://c183973b-cd93-4d55-8068-b4df8e6f7dca@109.71.253.8:16974?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/nioYRQO2jjEpkhhUy8Br%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
hysteria2://jPC59G4CL18DvOcEYB9jdeorkZO@109.71.253.8:26908?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=8k1C61696odkHsLE&mport=&os=#1007德国 
vless://5b81f396-c9dd-49d3-a026-3608a7b0625d@109.71.253.8:27050?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/iYtDEvY8jd2A%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
trojan://44cb96b5-d20f-42e6-bb61-844663f4d1ff@109.71.253.8:9704?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/frn%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NWI4MWYzOTYtYzlkZC00OWQzLWEwMjYtMzYwOGE3YjA2MjVkQDEwOS43MS4yNTMuODo2MDQwOTp3czovT3JyWm5na2dzMFRtZHdQcU8wbDduQVJsdW4lM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1007德国 
anytls://pEwTpElwz957roMFvu3FnArg71@109.71.253.8:41850?insecure=1&sni=download.windowsupdate.com&alpn=h2&fp=&os=#1007德国 
hysteria2://N4CzJ5kBQwMkdytJIyau@109.71.253.8:40715?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=iCRxEp3MQ4rBHJ3oqB9RE9lLJW&mport=&os=#1007德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZGMzODNhZjMtMmJkMS00MjhmLWJkZDYtNmJmZTgwMTBjOGViQDEwOS43MS4yNTMuODoxMzAxNjp3czovRVlyTHVuUlEyZnVGUVBoRFQ3OHhqanFvRjFXNVMlM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#1007德国 
hysteria2://KC6tOX5yDwbnYyXgLYzglNanXUmlpvSM4V4iq@109.71.253.8:63759?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=491bPqRJYE2JrapD7nKSzT54YcR&mport=&os=#1007德国 
trojan://2d272ef8-f3f0-40bc-8816-34621d800a6e@109.71.253.8:16564?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/A6F2%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@103.21.244.150:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@190.93.247.114:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.20.64.155:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.24.9.3:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@103.21.244.191:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.25.97.141:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@198.41.215.192:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@162.159.18.195:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.228.174:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@173.245.59.70:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.16.42.49:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 
vless://790e3dea-6b04-4483-b1e7-01bde71aa84d@104.18.21.130:443?flow=&encryption=none&security=tls&sni=dart.34892.qzz.io&type=xhttp&host=dart.34892.qzz.io&path=/ZETj2YLh24mig7%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d%3F790e3dea-6b04-44%3F83-b1e7-01bde71aa84d&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1007德国 

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
