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


ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.106.229.219:989#0305新加坡 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@103.149.182.191:8388#0305香港 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.112:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.155:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.174:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@103.21.244.86:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.16.155.114:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.20.192.155:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.24.46.117:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.25.160.84:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
trojan://1e63e585ab2fef3adcc9ea75a62abc23@104.251.227.182:443?flow=&security=tls&sni=hezijiasuqi.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305香港 
vless://819664e1-26f2-49db-8025-b18adee8fd2c@107.172.157.148:30944?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305美国 
hysteria2://09d00f2f-d8da-4c02-a305-303d736eb2e2@107.172.235.75:43615?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzU1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDIwNTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDQwMTQsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NTAwOTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQxIiwicG9ydCI6MzIwNzcsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:15084#0305日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.250.31.57:443#0305新加坡 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@135.148.163.90:443?flow=&encryption=none&security=tls&sni=147135001178.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305美国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0305以色列 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0305孟加拉国 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0305新加坡 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0305日本 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0305法国 
ss://Y2hhY2hhMjA6QURabVJRVUdIVHdY@14.18.253.178:8339#0305韩国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@147.135.10.103:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuMTk0LjE2OCIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkYzc4NTgyLTg4YTgtNGI0Yy05ZTNlLTUwODMxZDY3Mjc2NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYW1kLmFsIiwicGF0aCI6Ii9YRVNBTElTVEhFQkVTVD9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1kLmFsIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuNjYuMTY4IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMDXlvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiN2RjNzg1ODItODhhOC00YjRjLTllM2UtNTA4MzFkNjcyNzY2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJhbWQuYWwiLCJwYXRoIjoiL1hFU0FMSVNUSEVCRVNUP2VkPTIwNDgiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhbWQuYWwiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.179.9.121:443#0305日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.236.83.127:443#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MjEyMCwic2N5IjoiYXV0byIsInBzIjoiMDMwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MzkwMiwic2N5IjoiYXV0byIsInBzIjoiMDMwNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0305丹麦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0305波兰 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.96.253:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpXVlUyN0xxdUFNT2VYbVllU3RJODk3@188.126.83.62:32448#0305瑞典 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.196.128:443?flow=&encryption=none&security=tls&sni=www.secge.us.kg&type=xhttp&host=www.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0305新加坡 
ss://YWVzLTI1Ni1nY206WTZSOXBBdHZ4eHptR0M=@23.154.136.132:5000#0305美国 
ss://YWVzLTI1Ni1nY206ZzVNZUQ2RnQzQ1dsSklk@23.154.136.132:5004#0305美国 
ss://YWVzLTI1Ni1nY206WTZSOXBBdHZ4eHptR0M=@23.154.136.132:5601#0305美国 
trojan://telegram-id-privatevpns@3.78.108.122:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.217.73.31:443#0305美国 
trojan://telegram-id-directvpn@35.176.22.5:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305英国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.86.89.247:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.198.93:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.216.191:443#0305美国 
trojan://90c0bc87-d7dd-4233-9b1a-cc9e7cf30649@36.151.251.12:12003?flow=&security=tls&sni=36.151.251.12&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305香港 
vless://51e44d01-5fa0-47d3-8ee3-ad1f04d3abcc@37.202.237.107:23297?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vless://eba63659-e1c0-4fba-a089-bf54b21e05ca@37.202.237.107:45495?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
ss://YWVzLTI1Ni1nY206S2l4THZLendqZWtHMDBybQ==@38.114.114.77:5500#0305美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMwNeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.201.0.67:443#0305韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.244.103:443#0305韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo2MjQ1OSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmZjRhMDExYy1lZGZlLTQ2OTEtYmIwMi0wNjkxZjdmNjhkODYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9kP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZmY0YTAxMWMtZWRmZS00NjkxLWJiMDItMDY5MWY3ZjY4ZDg2QDQ1LjgyLjEyMC4yMTM6NzI5Mjp3czovRXNYZmpYWFlBc2NVS2hEMmclM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0305德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDllYzhjYzItZDdlYS00ODA3LTkwOTgtNTdhYjlmMDFlYjllQDQ1LjgyLjEyMC4yMTM6NTg1NDE6d3M6L3h3bWJKOGEzV2s4UkJGbmplcyUzRmVkJTNEMjU2MDpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpub25lOnRsczpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0OTE5Niwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzNGQ2MzU2OC1lNDgyLTQxMDMtYTg0Yi1lMGQyZTZjYjI5NTYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9NT2hkb1lYMWZ0OEJMN2pvP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6Yjg4Mzk3Y2MtZjI0NC00YzUxLWFhYzgtZTRmOWNiZTA3MjI2QDQ1LjgyLjEyMC4yMTM6MTgzNTE6d3M6L2V0TFBjTGZhSXdXdE5aWUJubE40cEQ0cHNIJTNGZWQlM0QyNTYwOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOm5vbmU6dGxzOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0305德国 
trojan://09ec8cc2-d7ea-4807-9098-57ab9f01eb9e@45.82.120.213:58516?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/rhGEw0v8%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0MzA0MSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxYzkzNWZmNi05NGRmLTQ1MTctYjRmYy03MmYxOTZkMDhjZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9aRVRqMllMaDI0bWlnNz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://pK4C8WfmMOnKNBjHAwROTVL757dKhuzp44fZEP@45.82.120.213:8225?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=eN7VVR0DXY9E66j1ztqmqhia&os=#0305德国 
hysteria2://VzZnrla6nT4vqgGeczY5VGZv8i@45.82.120.213:38418?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=8IkmF1ay9BO80r5Xaojdoych5TUMwdFgO&os=#0305德国 
vless://1c935ff6-94df-4517-b4fc-72f196d08ce7@45.82.120.213:19388?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/EZDyNk64ay%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
hysteria2://bVDGZOaRRDJTlzTowS0l1knXdyefP7YvVoNy3gk@45.82.120.213:20118?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=zE46bkyxuTVoAZJEHvv&os=#0305德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0NzQxOSwic2N5IjoiYXV0byIsInBzIjoiMDMwNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2MzQ3YzA4Yi0wODU4LTRkMTUtODkyNi03ZjFhMTBjODkzMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9GeGhTMkgwbW1XSGZDODlRRzRnZno4V1U/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://LT4jmgqbbBFxNhVpf0y@45.82.120.213:46557?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=szigIuqcobUucjuriYyWRcaq&os=#0305德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmJjMzVhOTItODdlYS00YmRhLTg0ZTQtOTJlYmRiMTU1MjM0QDQ1LjgyLjEyMC4yMTM6NDE0MzQ6d3M6L3VwcElpcVdCcXl1RWRqNTV3SlVlclglM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0305德国 
hysteria2://vbmNANpOabqnEUDz3qlg92fZg9X82fPu@45.82.120.213:36549?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=xCncNDjXpqom367KZtCx&os=#0305德国 
vless://bbc35a92-87ea-4bda-84e4-92ebdb155234@45.82.120.213:60456?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/WoPSjTaQoSTdf9vqh%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305德国 
hysteria2://Uich6OFjOgs9lfz0OrxuTX4lh@45.82.120.213:63352?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=to3kHHGYIspVSF70e34UB9GfZp62&os=#0305德国 
hysteria2://gINIT5FbIGPciJ4gW9ziFQAQcYECqX6@45.82.120.213:44118?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=UVb6xjf1685JdZopGPgsGZ6annfGRBW9jULa&os=#0305德国 
hysteria2://dongtaiwang.com@46.17.41.189:51224?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0305俄罗斯 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.13.119.156:443#0305美国 
trojan://telegram-id-privatevpns@52.215.25.147:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305爱尔兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.204.173:443#0305美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.65.101.11:443#0305日本 
hysteria2://pPgOLFwmkmYYBZi6q6ZjzK6gJTQ@64.23.178.208:8243?insecure=1&sni=bing.com&alpn=&fp=&os=#0305美国 
vless://8b54a6c7-2544-4a07-9520-b4e5252ba2b7@89.187.28.126:8443?flow=&encryption=none&security=tls&sni=ul-japan1.09vpn.com&type=ws&host=&path=/vless/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305日本 
ss://YWVzLTI1Ni1nY206SUhXTFlaU1NTWDRHU0tMQQ==@8tv68qhq.slashdevslashnetslashtun.net:16013#0305新加坡 
ss://YWVzLTI1Ni1nY206WU1CM1FMODVMN0YxS0pSNw==@8tv68qhq.slashdevslashnetslashtun.net:18013#0305日本 
ss://YWVzLTI1Ni1nY206V05XNU1aSlg1N1pKVU5RVQ==@8tv68qhq.slashdevslashnetslashtun.net:16009#0305新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0305斯洛文尼亚共和国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpPREEyTUdaaA==@95.164.36.59:8388#0305奥地利 
vless://1a7a39e4-8c9b-4052-b8b2-c0929536bba5@95.164.4.88:8443?flow=&encryption=none&security=tls&sni=pq-brazil1.09vpn.com&type=ws&host=&path=/vless/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0305巴西 
ss://YWVzLTI1Ni1nY206MDQwN1dLSUVJWE1UTEdDNg==@qh62onjn.slashdevslashnetslashtun.net:16007#0305新加坡 
ss://YWVzLTI1Ni1nY206RkNFVU9BU1JRSkMwTE4wSw==@qh62onjn.slashdevslashnetslashtun.net:15009#0305香港 
ss://YWVzLTI1Ni1nY206UkJOMVVOR1ZQRjFCUVhQSw==@ti3hyra4.slashdevslashnetslashtun.net:15006#0305香港 
ss://YWVzLTI1Ni1nY206QkZZQ09LSFRDOEhJV1dSQg==@ti3hyra4.slashdevslashnetslashtun.net:16006#0305新加坡 
ss://YWVzLTI1Ni1nY206ODRITVJBV0lMS0I0OVFVWg==@ti3hyra4.slashdevslashnetslashtun.net:18002#0305日本 
ss://YWVzLTI1Ni1nY206WTJVNThTOTBFM0dTVDFBUQ==@ti3hyra4.slashdevslashnetslashtun.net:21001#0305台湾 
hysteria2://4a48871d49c3f20fd93d365c49e45f78@v.ccs.vaala.cat:443?insecure=0&sni=v.ccs.vaala.cat&alpn=&fp=&os=#0305美国 
ss://YWVzLTI1Ni1nY206NFM4NUxGMlEzUUs5MjE3MQ==@w72tapyb.slashdevslashnetslashtun.net:18008#0305日本 
vmess://eyJ2IjoiMiIsImFkZCI6Ind3dy5hZXR2LmNvbSIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzA15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjdkYzc4NTgyLTg4YTgtNGI0Yy05ZTNlLTUwODMxZDY3Mjc2NiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYW1kLmFsIiwicGF0aCI6Ii9YRVNBTElTVEhFQkVTVD9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1kLmFsIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://999fe97a-5cd1-4f9f-9826-85db2b50a6ef@yingguo1.su8.lol:8899?insecure=0&sni=yingguo1.su8.lol&alpn=&fp=&os=#0305英国 
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
