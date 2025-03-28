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
vmess://eyJ2IjoiMiIsImFkZCI6IjBmODEwYi44NmJlLTQ0N2EtZWFmMS5jZmQiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDMyN+S4reWbvSIsIm5ldCI6IndzIiwiaWQiOiI0YmYwNzRmNC03ZTljLTRlNGItYTEwZC0xNTZlMjYxOTk3MjkiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImhrMDFzLjg2YmUtNDQ3YS1lYWYxLmNmZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiaGswMXMuODZiZS00NDdhLWVhZjEuY2ZkIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOC4xNDkuNzUiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfoi7Hlm70iLCJuZXQiOiJ3cyIsImlkIjoiNjIxOGM2NTQtZmY2MS00NTcwLThjMWYtZGM5NzJkMTVkMWMzIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1ay5pbnNib3QuZmlsZWdlYXItc2cubWUiLCJwYXRoIjoiL2FhIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidWsuaW5zYm90LmZpbGVnZWFyLXNnLm1lIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS4xOC4yMjciLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTUwZGI2YWEtNDkyNi00NjE2LTgxNmUtZWMwMzEyZGNiODdiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJqYWhma2poYS5jZmQiLCJwYXRoIjoiL2xpbmt3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImphaGZramhhLmNmZCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://85950277-f447-48f0-9ead-aaf6d5ff3cad@104.21.34.159:443?flow=&security=tls&sni=df6xxxx.2031.pp.ua&type=ws&header=none&host=df6xxxx.2031.pp.ua&path=/I4L1BP2DQVYmx5NYQ76MGGq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
trojan://6040a753-e35b-4384-8713-96f3c639b621@104.21.69.41:443?flow=&security=tls&sni=kju84.890602.XYZ&type=ws&header=none&host=kju84.890602.xyz&path=/WxWOWO1YA9bs2HOmaeWimvT3&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
hysteria2://BmiUivYWEzh37sOERZ56Kkpdc@109.71.253.251:19735?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=rBA7MhmhIM99puQMDsgrmQxp9m6uKQ&os=#0327德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMjUxIiwicG9ydCI6MTI2MDIsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZTVhYWI0MzktYjg0NS00OGQxLTg5ZTMtNmI3MjZlZDA5YmE4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsInBhdGgiOiIvP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://a9f3c319-bc7c-4efa-bcf9-bbb2adaff5f4@109.71.253.251:6042?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/jcLQVZcAP129P9%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327德国 
vless://f7c71fe7-d4f7-480f-9108-9a82e79df9c8@109.71.253.251:28424?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/WNcQYzMbjQn%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjdjNzFmZTctZDRmNy00ODBmLTkxMDgtOWE4MmU3OWRmOWM4QDEwOS43MS4yNTMuMjUxOjMwODYyOndzOi9YMk9VRiUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0327德国 
vless://ccb9a257-dd06-4c94-bc9e-64574b8b7f31@109.71.253.251:46673?flow=&encryption=none&security=tls&sni=www.digitalocean.com&type=ws&host=www.digitalocean.com&path=/MxlB1TycYDOOCnNSI0Z8doG%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327德国 
hysteria2://7CrTncd6QfhBEUvsi9Cuzhe@109.71.253.251:53646?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=SOMnIfqY5yZYXbwf1tgFufg5JCrCWSS&os=#0327德国 
hysteria2://WaWwehKjc13hOB8ykbm@109.71.253.251:37470?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=posY9IRh18L6uCT7T&os=#0327德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTU1MjhlYzQtNzI1YS00MWI2LWJlZGQtOGFkZTcyYzYzZDIwQDEwOS43MS4yNTMuMjUxOjI4MDgyOndzOi9pUDBGMnQ1eFFtVFRtODI0UDVKRTU5ZjFpSWQlM0ZlZCUzRDI1NjA6d3d3LmRpZ2l0YWxvY2Vhbi5jb206bm9uZTp0bHM6d3d3LmRpZ2l0YWxvY2Vhbi5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0327德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMjUxIiwicG9ydCI6NDE1Mywic2N5IjoiYXV0byIsInBzIjoiMDMyN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmN2M3MWZlNy1kNGY3LTQ4MGYtOTEwOC05YTgyZTc5ZGY5YzgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Ind3dy5kaWdpdGFsb2NlYW4uY29tIiwicGF0aCI6Ii96P2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ3d3cuZGlnaXRhbG9jZWFuLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://kwsQm64kkqJlltynSf3kQ97b2XlAqdCsL@109.71.253.251:63514?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=xQMU3yu6zgnyrfWgypSFmrebcY9bu86LH70oRmQ&os=#0327德国 
hysteria2://cg1Sp4q4An7z9XnO7pZHlhZ9N@109.71.253.251:33936?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=k3siqzZNMXUGYktoPA0lBd6&os=#0327德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OGU4MzU3YTktNjRhZi00OWU1LWEwOGItM2Y5NWFjNDc2NzRiQDEwOS43MS4yNTMuMjUxOjU5Njk1OndzOi9HcEdGUmJRcjI3TSUzRmVkJTNEMjU2MDp3d3cuZGlnaXRhbG9jZWFuLmNvbTpub25lOnRsczp3d3cuZGlnaXRhbG9jZWFuLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0327德国 
trojan://8e8357a9-64af-49e5-a08b-3f95ac47674b@109.71.253.251:38754?flow=&security=tls&sni=www.digitalocean.com&type=ws&header=none&host=www.digitalocean.com&path=/ulRNTZXvP%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327德国 
hysteria2://7RACOJWhZu3hbH8CHh@109.71.253.251:21599?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=7sqyCdAR8awtyUKHECrFGPUCHA&os=#0327德国 
hysteria2://pSclcnoTlXQLeD8bcnnrHIH@109.71.253.251:48555?insecure=1&sni=www.digitalocean.com&alpn=&fp=&obfs=salamander&obfs-password=r1P1MDy33hShVgrs&os=#0327德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzQwOTMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjEyMyIsInBvcnQiOjUxMDUyLCJzY3kiOiJhdXRvIiwicHMiOiIwMzI3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjMxOTk4LCJzY3kiOiJhdXRvIiwicHMiOiIwMzI3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.112.73.126:443#0327日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.124.229.107:443#0327韩国 
trojan://telegram-id-privatevpns@13.37.18.215:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327法国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@137.175.113.215:8388#0327美国 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0327法国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0327日本 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0327新加坡 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0327孟加拉国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0327以色列 
trojan://2cba4104747d49d18319e5ade1b93ab5@161.35.34.48:443?flow=&security=tls&sni=yourjobnavigator.online&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327英国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.139.23:443#0327新加坡 
trojan://telegram-id-privatevpns@18.169.179.112:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0327英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1NTc1NCwic2N5IjoiYXV0byIsInBzIjoiMDMyN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0IjozMTkxOSwic2N5IjoiYXV0byIsInBzIjoiMDMyN+mmmea4ryIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTEyOC1jZmI6c2hhZG93c29ja3M=@184.170.241.194:443#0327美国 
vless://24a4aa9b-b341-4717-9d4a-00d74c2b84e0@185.146.173.37:2096?flow=&encryption=none&security=tls&sni=MnWzF164yO.mYsPdMmEtI.cOm&type=ws&host=MnWzF164yO.mYsPdMmEtI.cOm&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327摩尔多瓦 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4xNzQuMTM4LjE5NiIsInBvcnQiOjIwODIsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiM2Y2MzhmMzQtOGRiYS00MTg2LWJjNDMtMjcxNmE3ZGRkNGJlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ5ZWxsb3ctcGFwZXItMDI5Yy55dm9ubmEud29ya2Vycy5kZXYiLCJwYXRoIjoiL2F6MDUuYmV5b25keS5jZmQvbGluaz8vVE1AQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjEvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0327波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4Ni4xOTAuMjE1LjkzIiwicG9ydCI6MjIzMjQsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfnkZ7lo6siLCJuZXQiOiJ0Y3AiLCJpZCI6IjA0NjIxYmFlLWFiMzYtMTFlYy1iOTA5LTAyNDJhYzEyMDAwMiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://5CBqBh6MeDq6GajcilBiDg%3D%3D@192-227-152-86.nip.io:61001?insecure=1&sni=192-227-152-86.nip.io&alpn=&fp=&os=#0327美国 
vless://51435e51-e048-4a32-a9e6-1e6fa56a576d@192.200.160.188:2087?flow=&encryption=none&security=tls&sni=crm.iranigamebaz.ir&type=ws&host=crm.iranigamebaz.ir&path=/V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban------V2RayMizban&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327芬兰 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@192.9.236.144:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@194.5.215.59:8080#0327美国 
hysteria2://f93fdbc9-3789-44b4-8ece-51b9c2780ba8@195.133.5.127:33007?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=NDhhNmY5YTY0MGYzOTgxYQ==&os=#0327俄罗斯 
hysteria2://dongtaiwang.com@195.154.33.70:59967?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0327法国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0327新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.36.26.148:443#0327韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.36.72.86:443#0327韩国 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.71.252:443#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.222.2.112:443#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.161.163.245:443#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.87.29.54:443#0327美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989#0327以色列 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMyN+azouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.202.67.225:443#0327韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.207.157.253:443#0327日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0Mi4xMjAuMTkwIiwicG9ydCI6MjA4Miwic2N5IjoiYXV0byIsInBzIjoiMDMyN+azleWbvSIsIm5ldCI6IndzIiwiaWQiOiIzZjYzOGYzNC04ZGJhLTQxODYtYmM0My0yNzE2YTdkZGQ0YmUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InllbGxvdy1wYXBlci0wMjljLnl2b25uYS53b3JrZXJzLmRldiIsInBhdGgiOiIvYXowNS5iZXlvbmR5LmNmZC9saW5rIyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzI35rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NS4xNjUuMTE0IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzI35rOV5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjliNDU2YzJhLWYyYzEtNDVlMS04N2E5LWI3NjI4YjA0YmIyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYmV5b25kZHN6LmNmZCIsInBhdGgiOiIvbGlua3dzIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYmV5b25kZHN6LmNmZCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0YTJyZml4b3BoZGpmZmE4S1ZBNEFh@45.87.175.192:8080#0327荷兰 
hysteria2://dongtaiwang.com@46.17.41.217:37481?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0327俄罗斯 
hysteria2://dongtaiwang.com@46.29.163.171:18626?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0327俄罗斯 
trojan://telegram-id-directvpn@51.44.200.31:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327法国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@51.81.36.120:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.169.188.214:443#0327新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.187.221.114:443#0327美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.254.9.107:443#0327新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpNTGFBQ2plWlR1MEVjVFdLYUlNeXJN@61.72.28.169:49539#0327韩国 
vless://fe069d77-882c-4175-b48e-c79e3fe65a81@65.109.191.227:443?flow=&encryption=none&security=tls&sni=nextgenerationaiplatform.ir&type=ws&host=nextgenerationaiplatform.ir&path=/fsafasfsafA&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327芬兰 
hysteria2://c8ed6f77-3a96-46f9-9959-79118f9c1019@85.194.246.115:53252?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0327波兰 
vmess://eyJ2IjoiMiIsImFkZCI6Ijg2LjM4LjIxNC41MiIsInBvcnQiOjg0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMjfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMTkxYmFiYzUtMmFhZi00ZmU1LWE1NjMtZjE0MjQ0YWVmYjRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJsYXgxLmliZ2Z3LnRvcCIsInBhdGgiOiIveHJlbnZ3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImxheDEuaWJnZncudG9wIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0327斯洛文尼亚共和国 
trojan://7f2a9642-1f5f-485e-ab88-b9bf1a2f0a53@aafrtpfxr.sgl02i9zjfegelp.5xfsur8v62.gosdk.xyz:42881?flow=&security=tls&sni=q08m.vgraxiw73s.hasyaf.cn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327新加坡 
ssr://Y20yLnhjb25lLnh5ejo1NjEzODpvcmlnaW46YWVzLTI1Ni1jZmI6dGxzMS4yX3RpY2tldF9hdXRoOmRXbEJRM0Z5U1hJPS8/b2Jmc3BhcmFtPWMyY3lMV05rYmkxeWIzVjBaUzVqYjNWc1pHWnNZWEpsTFdOa2JpNWpiMjA9JnByb3RvcGFyYW09JnJlbWFya3M9TURNeU4rYVdzT1dLb09XZG9RPT0mb3M9 
vless://32561a76-b738-48b9-b3f2-37856346fbd8@hyun.cloudflare.182682.xyz:443?flow=&encryption=none&security=tls&sni=mo.4056860.xyz&type=ws&host=mo.4056860.xyz&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327澳门 
hysteria2://914e64f7-f8e6-44ce-9e5a-97669a18d605@jp.tuanzi.xyz:20701?insecure=1&sni=&alpn=&fp=&os=#0327日本 
ss://YWVzLTI1Ni1nY206OWFjZmM1NzQtYWNjMy00YzJiLWFiM2ItNDkxZDQzYTZlYjgz@okanc.node-is.green:21114#0327新加坡 
ss://YWVzLTEyOC1nY206QjdFMkUxQjgtRTgxMC00QkEwLUEzMDAtNTYzMkI5MTIwMTlE@prem.pythoncdn.com:13864#0327香港 
vmess://eyJ2IjoiMiIsImFkZCI6InMyLmRiLWxpbmswMi50b3AiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDMyN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI0YjM2NjI1Yy1iOWQ5LTNlYTYtYWVkNS04NmQ2MmM3MGUxNmQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjEwMC02Ni0yMDEtMzUuczIuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xMDQuMjAuNzYuNjciLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIxMDAtNjYtMjAxLTM1LnMyLmRiLWxpbmswMi50b3AiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InN0YW4ucHl0aG9uY2RuLmNvbSIsInBvcnQiOjE0NjAxLCJzY3kiOiJhdXRvIiwicHMiOiIwMzI36aaZ5rivIiwibmV0IjoidGNwIiwiaWQiOiJCM0E5ODNDQi0wQTRBLTQzOEUtOUE0NS05NDM4QjBEMzYyQjAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://caf21c96-35ef-4d5e-97c8-a9d8d4edcc5b@sub-us.yangxiansheng.online:51228?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0327美国 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2003?insecure=0&sni=is01.akebi.cc&alpn=&fp=&os=#0327以色列 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2020?insecure=0&sni=ua01.akebi.cc&alpn=&fp=&os=#0327乌克兰 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2000?insecure=0&sni=hk03.akebi.cc&alpn=&fp=&os=#0327香港 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2005?insecure=0&sni=fr01.akebi.cc&alpn=&fp=&os=#0327法国 
hysteria2://82febca6-8856-41fe-84df-c8bda0b72c7b@tw3.akebi.cc:2006?insecure=0&sni=au01.akebi.cc&alpn=&fp=&os=#0327澳大利亚 
vless://576c81b6-4976-4fe3-b1a9-05a9c302e98e@us10-04.852224.ggff.net:443?flow=&encryption=none&security=tls&sni=us10-04.852224.ggff.net&type=ws&host=us10-04.852224.ggff.net&path=/HlAPZV9g9xmyAVVtopw90eoXel&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
vless://576c81b6-4976-4fe3-b1a9-05a9c302e98e@us10-07.852224.ggff.net:443?flow=&encryption=none&security=tls&sni=us10-07.852224.ggff.net&type=ws&host=us10-07.852224.ggff.net&path=/HlAPZV9g9xmyAVVtopw90eoXel&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327美国 
vmess://eyJ2IjoiMiIsImFkZCI6InVzMTAtMDkuODUyMjI0LmdnZmYubmV0IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzI3576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjU3NmM4MWI2LTQ5NzYtNGZlMy1iMWE5LTA1YTljMzAyZTk4ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidXMxMC0wOS44NTIyMjQuZ2dmZi5uZXQiLCJwYXRoIjoiL1NOd05kdW53MjhsVnp0b3B3OTBlb1hlbCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVzMTAtMDkuODUyMjI0LmdnZmYubmV0IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://6e8b9913-5277-4627-95b0-86766ae65ad6@wb.kaiqsz.com:42765?flow=&security=tls&sni=mmbiz1.redapricotcloud.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327台湾 
trojan://2cba4104747d49d18319e5ade1b93ab5@yourjobnavigator.online:443?flow=&security=tls&sni=yourjobnavigator.online&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0327英国 

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
