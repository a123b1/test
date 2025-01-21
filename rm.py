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

vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjHnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@154.197.26.237:8388#0121香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo0NjYwMiwic2N5IjoiYXV0byIsInBzIjoiMDEyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NDEwNCwic2N5IjoiYXV0byIsInBzIjoiMDEyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NjYwMSwic2N5IjoiYXV0byIsInBzIjoiMDEyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://base64,OWJiNDUyYjEwNmZmYzIxN0AyMDcuMTQ4LjIyLjkzOjQ0Mz9pbnNlY3VyZT0xJnNuaT0mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPWNkMjkwOTlkJm9zPQ==#0121美国 
hysteria2://base64,OWJiNDUyYjEwNmZmYzIxN0AyMDcuMTQ4LjIyLjkzOjQ0Mz9pbnNlY3VyZT0xJnNuaT0yMDcuMTQ4LjIyLjkzJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1jZDI5MDk5ZCZvcz0=#0121美国 
hysteria2://base64,OWJiNDUyYjEwNmZmYzIxN0AyMDcuMTQ4LjIyLjkzOjQ0Mz9pbnNlY3VyZT0xJnNuaT12a3ZkMTI3Lm15Y2RuLm1lJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1jZDI5MDk5ZCZvcz0=#0121美国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.141.82.165:8848#0121德国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.142.21.211:8848#0121英国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.18.5.163:8848#0121卡塔尔 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.58.159.18:8848#0121美国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.194.227.32:8848#0121台湾 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.220.163.233:8848#0121香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.94.25.109:443#0121美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDEyMeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDQ2LjE3LjQxLjE4OTo1MDcxNz9pbnNlY3VyZT0xJnNuaT13d3cuYmluZy5jb20mYWxwbj0mZnA9Jm9zPQ==#0121俄罗斯 
vless://base64,M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDUxLjgxLjM2LjE3Mjo0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9MTQ3MTM1MDEwMTAzLnNlYzE5b3JnLmNvbSZ0eXBlPXRjcCZob3N0PSZwYXRoPSZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121美国 
hysteria2://base64,MTgyNDBiMmRmZGQ3NjQ4NEA3MC4zNC4yMDcuMTUzOjQ0Mz9pbnNlY3VyZT0xJnNuaT03MC4zNC4yMDcuMTUzJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1kMjY0OGVjMiZvcz0=#0121瑞典 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmMTZkMzc1Mi03YmFlLTQ3NGUtODdkYy1mODkyZGYyY2FlYWY=@ctmm.gscloud.bond:31620#0121新加坡 
trojan://base64,Mzg1NzFjYTYtNjY5Mi00NTU5LWI5MDEtMGJjNTgyNmI3NjYxQHJ1MDE5NS5hbGliYWJhb2t6LmNvbTo2MDE5ND9mbG93PSZzZWN1cml0eT10bHMmc25pPXJ1MDE5NS5hbGliYWJhb2t6LmNvbSZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121俄罗斯 
vless://base64,ODA3YjI3MTctZTFhYy00MjA5LTkzM2ItYjA0MDc2Y2RkZGU5QDEwMy4xMTYuNy4xMzM6MjA4Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1hbWVkby5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnR5cGU9d3MmaG9zdD1hbWVkby5hbWJlcmNjLmZpbGVnZWFyLXNnLm1lJnBhdGg9LyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS44MS4xMTUiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZGUwNGFkZDktNWM2OC04YmFiLTk1MGMtMDhjZDUzMjBkZjE4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJub3J0aGZsYW5rLjEwNzQyMS54eXoiLCJwYXRoIjoiL3ZtZXNzIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoibm9ydGhmbGFuay4xMDc0MjEueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@107.148.6.121:8388#0121日本 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@109.104.154.146:33333#0121荷兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.250.116.31:443#0121新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpkcnFpNTVCQ3Z3aTNuT1h1bFlqR0xR@13.79.171.214:25444#0121爱尔兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0MS4xMzYuMzYuMjA2IiwicG9ydCI6NTc5MTgsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjHoi7Hlm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjlhMTdhNWRhLTA3OTgtNGJjMS1iMWIzLWFlYjFhOGU2OWRlZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://base64,YTcwZTc0YjMtM2Y2OS00ZDc5LThjODUtNmRiY2RkZjJlZDJiQDE1MS4xMDEuMi4xMzM6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWxpdmUuc2tvcm5vcnRoLmNvbSZ0eXBlPXdzJmhvc3Q9VW5pdGVkU3RhdGVBbWluY2xvdWQuY29tJnBhdGg9L0ZyZWVkb20tQXphZGkvJTNGZWQlM0QyMDQ4JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121亚美尼亚 
vless://base64,ODA3YjI3MTctZTFhYy00MjA5LTkzM2ItYjA0MDc2Y2RkZGU5QDE1NC4yMTEuOC44NDoyMDgzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWFtZWRvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZob3N0PWFtZWRvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121波兰 
vless://base64,ODA3YjI3MTctZTFhYy00MjA5LTkzM2ItYjA0MDc2Y2RkZGU5QDE1NC4yMTEuOC45MDo0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9YW1lZG8uYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZ0eXBlPXdzJmhvc3Q9YW1lZG8uYW1iZXJjYy5maWxlZ2Vhci1zZy5tZSZwYXRoPS8lM0ZlZCUzRDI1NjAmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121波兰 
vless://base64,MDU0ZDUwM2QtNDc0OC00N2E2LTgxMTgtNzFhOTZjNTFmMmQ5QDE3Mi42Ni4xNjguMTk3OjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnR5cGU9d3MmaG9zdD1ObDItRnVsTC5Qckl2QXRlaVAuTmVUJnBhdGg9L1ZMRVNTJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121荷兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.142.225.149:443#0121新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MzAwMiwic2N5IjoiYXV0byIsInBzIjoiMDEyMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.193.49.88:989#0121爱沙尼亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.237.185.160:989#0121立陶宛 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@185.255.123.92:990#0121尼日利亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.252.251:989#0121秘鲁 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.253.171:989#0121厄瓜多尔 
vless://base64,MDhjNDFlMTctOWQxYy00ZDRhLTllZGMtMjQyZDNkNzFjMWFjQDE4OC4xMTQuOTYuMzo4MDgwP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT0mc25pPW9yZGVyLmZvcnRnaWZ0LmlyJnR5cGU9d3MmaG9zdD1vcmRlci5mb3J0Z2lmdC5pciZwYXRoPS96NWxzSEY1elFyZDFySkRyJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@188.214.36.155:989#0121爱沙尼亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.36.61.59:989#0121立陶宛 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@192.36.61.59:990#0121立陶宛 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@193.29.139.189:8080#0121荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NC44Ny42OS41MCIsInBvcnQiOjE3OTI2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6ImEwOTEzMTA2LTk3NDktNDJjMy05NjRmLTcxZDIxZTZkZDUxNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTk0Ljg3LjY5LjUwIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIxOTQuODcuNjkuNTAiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NC44Ny42OS41MiIsInBvcnQiOjE3OTI2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjY4MGFiOGY1LTJkNTUtNDBiYy1iZjhkLWEzNWJkNjM0MjZhNyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTk0Ljg3LjY5LjUyIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIxOTQuODcuNjkuNTIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS40MiIsInBvcnQiOjE3OTI2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjE4MWVlZTA0LWFhODgtNDlhMS1iNTgzLTlmYzgwYzQ0NDQzMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS41MCIsInBvcnQiOjE3OTI2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6Ijk2MGM5NWE5LTg1MDItNGNiYy1hNTI3LWQ0MGMyZDY4ZDJiMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS44NiIsInBvcnQiOjE3OTI2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjJkYmY0NmU4LTFiMjAtNGM3ZC05Y2Y0LTUzNjBjM2FiNTA5OSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.36.116.141:443#0121韩国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.143.129.230:989#0121芬兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpZakppWXpCag==@45.140.146.223:8388#0121摩尔多瓦 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjguMTU5LjI0MSIsInBvcnQiOjMzMzk1LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjM5OGNlODRlLTQ4NDktNGU1Zi05YjFhLWE1NmZiZTIzM2I4MSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@46.183.217.232:990#0121拉脱维亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMzkuMjU0LjE5NiIsInBvcnQiOjIzOTg1LCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx6Iux5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjM5OGNlODRlLTQ4NDktNGU1Zi05YjFhLWE1NmZiZTIzM2I4MSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://base64,MzY0ODQyNTc5NDc0Mjc4ODA5NkA1LjguMzUuMjA4OjQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWxvdmluZy1ib2EudHJlZWZyb2c3NjEub25lJnR5cGU9dGNwJmhlYWRlcj1ub25lJmhvc3Q9JnBhdGg9JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121印度 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.179.54.70:443#0121新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.187.174.202:443#0121美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.214.180.125:443#0121美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.255.240.168:443#0121新加坡 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@84.17.53.160:989#0121瑞士 
vless://base64,MTJjZWFkZTktMjBmNy00MTVjLTk3NjUtN2I0NGVjMzllN2JjQDg1LjEzMy4yMDEuMjI6MjA1Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1sZHBudXVyejMuaW1hbWhhc3Nhbi5pbmZvJnR5cGU9d3MmaG9zdD1sZHBudXVyejMuaW1hbWhhc3Nhbi5pbmZvJnBhdGg9L3FsSlBXa2RHNWR1WTF4TXk0UnZRamRGaUwmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121瑞典 
vless://base64,Yzk3YjNiMzMtMmE0My00NWIxLWJkNzYtNTE1NjdkMTZjODhiQDkxLjEwNy4xMzEuMTYxOjEwMDIxP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT0mc25pPSZ0eXBlPXRjcCZob3N0PSZwYXRoPSZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121德国 
vless://base64,ZGQxOTE2YjYtZDJmMS00ZTc1LWJjYjEtYWE1YzNiZjU4NDQ2QDkxLjEwNy4xMzEuMTYxOjQwOTk0P2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT0mc25pPSZ0eXBlPXRjcCZob3N0PSZwYXRoPSZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121德国 
trojan://base64,QWltZXJAOTIuMjQzLjc0LjM6ODQ0Mz9mbG93PSZzZWN1cml0eT10bHMmc25pPWFtZXBvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZoZWFkZXI9bm9uZSZob3N0PWFtZXBvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTAmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121波兰 
vmess://eyJ2IjoiMiIsImFkZCI6Ijk0LjE4Mi4xNTAuMjMwIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjHlvrflm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjJiN2NlMWQyLTAzNzItNDEwNC1hYTA2LWY3ZDk5OWYyNmUxZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://base64,ZDM0MmQxMWUtZDQyNC00NTgzLWIzNmUtNTI0YWIxZjBhZmE0QDk0LjI1MC4yNDYuMjAwOjgwODA/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9YS5taWZlbmcudXMua2cmdHlwZT13cyZob3N0PWEubWlmZW5nLnVzLmtnJnBhdGg9LyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121美国 
vless://base64,ZDM0MmQxMWUtZDQyNC00NTgzLWIzNmUtNTI0YWIxZjBhZmE0QDk1LjE2NC41MS4yNDoyNTAxP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWEubWlmZW5nLnVzLmtnJnR5cGU9d3MmaG9zdD1hLm1pZmVuZy51cy5rZyZwYXRoPS8lM0ZlZCUzRDI1NjAmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpabVF3WmpGaw==@at1.opensocks.site:8388#0121奥地利 
vmess://eyJ2IjoiMiIsImFkZCI6ImNtLmF3c2xjbi5pbmZvIiwicG9ydCI6MjUyNDAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMjHoi7Hlm70iLCJuZXQiOiJ3cyIsImlkIjoiMjQzZWFiNTItOWFjMS00MDVjLTg4N2MtZWIxMTJjMDk4NWI4IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjbS5hd3NsY24uaW5mbyIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://base64,NTk1MTNhODctNGM5Ni01NDFiLWFkODctYjA3ODY4MDE1OTJlQGZhY3VsdHkudWNkYXZpcy5lZHU6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWZhY3VsdHkudWNkYXZpcy5lZHUmdHlwZT13cyZob3N0PXNwZWVkdGVzdC5uZXQuZnRwLmRlYmlhbi5vcmcuMS4yLjMuYS5iLmMubmV0c3BlZWR0ZXN0Lm5ldC5wbG4uYXNua2kuaXImcGF0aD0vdmxlc3Mtd3MvJTQwTUFSQU1CQVNISV9NQVJBTUJBU0hJLyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0121波兰 
vless://base64,ODA3YjI3MTctZTFhYy00MjA5LTkzM2ItYjA0MDc2Y2RkZGU5QGx5bm4ubnMuY2xvdWRmbGFyZS5jb206NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWFtZWRvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmdHlwZT13cyZob3N0PWFtZWRvLmFtYmVyY2MuZmlsZWdlYXItc2cubWUmcGF0aD0vJTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121波兰 
ss://YWVzLTI1Ni1nY206VE9VOVBCMkI3NjdURlFWVQ==@qh62onjn.slashdevslashnetslashtun.net:16007#0121新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6InMxLmRiLWxpbmswMS50b3AiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDEyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI0YjM2NjI1Yy1iOWQ5LTNlYTYtYWVkNS04NmQ2MmM3MGUxNmQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IjEwMC05Ny0xMTUtMjM1LnMxLmRiLWxpbmswMS50b3AiLCJwYXRoIjoiL2RhYmFpLmluMTA0LjI0LjMyLjIwNCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IjEwMC05Ny0xMTUtMjM1LnMxLmRiLWxpbmswMS50b3AiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InMxLmRiLWxpbmswMS50b3AiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTI1MC0zMi01My5zMS5kYi1saW5rMDEudG9wIiwicGF0aCI6Ii9kYWJhaS5pbjE3Mi42Ny45NS4zNSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IjEwMC0yNTAtMzItNTMuczEuZGItbGluazAxLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206OEZXNFFVSU05SEg5V1YxSQ==@ti3hyra4.slashdevslashnetslashtun.net:17002#0121美国 
vless://base64,ZGJhOTEwYTItODQ1YS00ZTYzLThhODgtMDk4ZDZmZDc5YTMwQHY3LnZpeHNtLmlyOjU3ODU/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PSZzbmk9JnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121法国 
ss://YWVzLTI1Ni1nY206MVhRREhHN01VNjFOS0RYMg==@w72tapyb.slashdevslashnetslashtun.net:17008#0121美国 
vmess://eyJ2IjoiMiIsImFkZCI6Inl4LnN1bGluay5vbmUiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDEyMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3ZjI0ZDZjOS1mMzdlLTQ1Y2QtODk1MS04YjY2NzhkZWFkMTUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVzNS5zdWxpbmsub25lIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6Inl4LnN1bGluay5vbmUiLCJwb3J0IjoyMDUyLCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5Y+w5rm+IiwibmV0Ijoid3MiLCJpZCI6IjdmMjRkNmM5LWYzN2UtNDVjZC04OTUxLThiNjY3OGRlYWQxNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoidHcwMi54bi0taW8wYTdpdzBhYjY3Yi54eXoiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://base64,M2MxNzEyZDMtNTI2Mi00NmNlLWJmMDMtM2ZjZWM1OWIyYzEyQDUuMTgwLjI1My4yMzM6NTExMjg/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1zd2Rpc3QuYXBwbGUuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1zd2Rpc3QuYXBwbGUuY29tJnBhdGg9L21NVXV4dnZOaDNtMiZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDk3NjJlMjctZjk0MS00ZGVhLWEzYWEtNjhjNWNmNmU4MzI5QDUuMTgwLjI1My4yMzM6NDI1MTQ6d3M6L0hodHk0dHY1REFFRWhOTjRRNTdCMmhoZkVZVTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0121德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0ODYzMiwic2N5IjoiYXV0byIsInBzIjoiMDEyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJiNzZkNzQ4My1jNGEyLTQxOTMtYTA2OC1hYjMwM2JlZTY2NmMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL05ZajFoY3ZCcnBpVmN6WGVHVE9LWGpCUFZBSkciLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozNTUzMywic2N5IjoiYXV0byIsInBzIjoiMDEyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhYmNhODYyNi0yMTZjLTQ3NDktOTJhOS1hZGJmM2NiZGEzYzYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL2hxelh5eXJMTzNlaWRlb3FyS0o1U0EiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjozODY0OCwic2N5IjoiYXV0byIsInBzIjoiMDEyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0ZTViYTA3Ni1kZjcwLTQxZGUtYWY3Ny1lYjdkNTU5NWNmMWYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL0k3IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoic3dkaXN0LmFwcGxlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NjgyNSwic2N5IjoiYXV0byIsInBzIjoiMDEyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJhOGI2ZjBmOC0xZGJhLTQ1YjgtYWNhOC1iNjBmNWQ3NTNkOTUiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL1FGbyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InN3ZGlzdC5hcHBsZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YWJjYTg2MjYtMjE2Yy00NzQ5LTkyYTktYWRiZjNjYmRhM2M2QDUuMTgwLjI1My4yMzM6NjM5MTU6d3M6L1luNE1sdGRraEpPTUMyUW53aDpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0121德国 
hysteria2://base64,QTlXeUxnVzhCY2k1RUN3NXhtVEgzcHlmVDdRdkA1LjE4MC4yNTMuMjMzOjUwMzY2P2luc2VjdXJlPTEmc25pPXN3ZGlzdC5hcHBsZS5jb20mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPWU0MkVvRDNNMDB1aXFZNUdnMmN3YXZTJm9zPQ==#0121德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MmNjNjY5YWYtOGViZi00YzhjLWFmNzItOTI1NWEzNTQ3NzA4QDUuMTgwLjI1My4yMzM6NDMwOTY6d3M6L3BUWTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0121德国 
trojan://base64,ZThkMTg5MDgtZjBiYS00OTZkLTkzZDctYjY5NGIxNjIwMjlhQDUuMTgwLjI1My4yMzM6NjUwNDE/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1zd2Rpc3QuYXBwbGUuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1zd2Rpc3QuYXBwbGUuY29tJnBhdGg9L3hlb1ZQQWh0RzZncTBrV05RclI4cmNIbjBYRyZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YThiNmYwZjgtMWRiYS00NWI4LWFjYTgtYjYwZjVkNzUzZDk1QDUuMTgwLjI1My4yMzM6NDQ5OTc6d3M6L2FJRnMyWHlWTmhKNTpzd2Rpc3QuYXBwbGUuY29tOm5vbmU6dGxzOnN3ZGlzdC5hcHBsZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0121德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZThkMTg5MDgtZjBiYS00OTZkLTkzZDctYjY5NGIxNjIwMjlhQDUuMTgwLjI1My4yMzM6NDYzNjc6d3M6L3QzVFYzMk1vbDg6c3dkaXN0LmFwcGxlLmNvbTpub25lOnRsczpzd2Rpc3QuYXBwbGUuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0121德国 
hysteria2://base64,blp1YktpdFphaVRsdUk0dU9PQ2hqanRANS4xODAuMjUzLjIzMzo1MTM1Nj9pbnNlY3VyZT0xJnNuaT1zd2Rpc3QuYXBwbGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1CbmsxaWJaYnlZMWtPQVN1OXlRJm9zPQ==#0121德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0Ijo0NDMwLCJzY3kiOiJhdXRvIiwicHMiOiIwMTIx5b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjA5NzYyZTI3LWY5NDEtNGRlYS1hM2FhLTY4YzVjZjZlODMyOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic3dkaXN0LmFwcGxlLmNvbSIsInBhdGgiOiIvVHpNR0s3d1RxT0E2UCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InN3ZGlzdC5hcHBsZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://base64,YThiNmYwZjgtMWRiYS00NWI4LWFjYTgtYjYwZjVkNzUzZDk1QDUuMTgwLjI1My4yMzM6MjgwMjQ/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1zd2Rpc3QuYXBwbGUuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1zd2Rpc3QuYXBwbGUuY29tJnBhdGg9L29ObTQwcjN2RmhnQjF6QnVDWTN3JmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121德国 
hysteria2://base64,dFJHc1B4M0tSY2dpV0xXdElzeTVITnVANS4xODAuMjUzLjIzMzoyNzAxNj9pbnNlY3VyZT0xJnNuaT1zd2Rpc3QuYXBwbGUuY29tJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1BUGFoekZCYnZyY21XbkVrRVMwUWpNUEV6dkFwd1lreFEmb3M9#0121德国 
vless://base64,YWJjYTg2MjYtMjE2Yy00NzQ5LTkyYTktYWRiZjNjYmRhM2M2QDUuMTgwLjI1My4yMzM6NTM2NzQ/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9c3dkaXN0LmFwcGxlLmNvbSZ0eXBlPXdzJmhvc3Q9c3dkaXN0LmFwcGxlLmNvbSZwYXRoPS9LRVZQTEFUY29FQ2JkcGN1SjhoNG9jUVo2bFMmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121德国 
vless://base64,MmNjNjY5YWYtOGViZi00YzhjLWFmNzItOTI1NWEzNTQ3NzA4QDUuMTgwLjI1My4yMzM6MzE5NzI/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9c3dkaXN0LmFwcGxlLmNvbSZ0eXBlPXdzJmhvc3Q9c3dkaXN0LmFwcGxlLmNvbSZwYXRoPS8wVDRmajUwRGEmaGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0121德国 
hysteria2://base64,ak9JUWxRZXU2RHIyUzhuTmQzS2JXbk9yOXJYVlBnU054M0A1LjE4MC4yNTMuMjMzOjMxNDU3P2luc2VjdXJlPTEmc25pPXN3ZGlzdC5hcHBsZS5jb20mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPTBUWm9jRkQ2OEFZdDNxRUwzaE1sNktrUWtNMW5OM0FDMFVsJm9zPQ==#0121德国 
hysteria2://base64,RkJCRG5KVGFLT0JWa3BBNE5Md3dKMHhUYVpTOVR2dW96bzMwQDUuMTgwLjI1My4yMzM6MzA5MTI/aW5zZWN1cmU9MSZzbmk9c3dkaXN0LmFwcGxlLmNvbSZhbHBuPSZmcD0mb2Jmcz1zYWxhbWFuZGVyJm9iZnMtcGFzc3dvcmQ9WGRhc3FZdFJPaDRyRGx6a0paTVBkZVB3SUVqcEQmb3M9#0121德国 
trojan://base64,YWJjYTg2MjYtMjE2Yy00NzQ5LTkyYTktYWRiZjNjYmRhM2M2QDUuMTgwLjI1My4yMzM6NDU5MTg/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1zd2Rpc3QuYXBwbGUuY29tJnR5cGU9d3MmaGVhZGVyPW5vbmUmaG9zdD1zd2Rpc3QuYXBwbGUuY29tJnBhdGg9L283NmpHazJZT0ZGZExldVhWVklITiZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0121德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMTgwLjI1My4yMzMiLCJwb3J0IjoyODEzOSwic2N5IjoiYXV0byIsInBzIjoiMDEyMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlOGQxODkwOC1mMGJhLTQ5NmQtOTNkNy1iNjk0YjE2MjAyOWEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InN3ZGlzdC5hcHBsZS5jb20iLCJwYXRoIjoiL0ZudzQwN1pVY3hMQnNTbEdKaTgiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJzd2Rpc3QuYXBwbGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 

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
