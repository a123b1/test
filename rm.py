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
vless://base64,M2RjOTAxNWYtMjBjYi00MmQ2LWFkYWItNTVjZTgzMWJhZTYxQHdoYXRpc215aXBhZGRyZXNzLmNvbToyMDg3P2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPWJ2U3l1LmFidUphLW5lV0hFdFppLklOZk8mdHlwZT13cyZob3N0PWJ2U3l1LmFidUphLW5lV0hFdFppLklOZk8mcGF0aD0vbW9yYW5vJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225芬兰 
ss://YWVzLTI1Ni1nY206Mkg5OFVaVDlMVDFURTNYOQ==@w72tapyb.slashdevslashnetslashtun.net:15008#0225中国 
ss://YWVzLTI1Ni1nY206NFM4NUxGMlEzUUs5MjE3MQ==@w72tapyb.slashdevslashnetslashtun.net:18008#0225日本 
ss://YWVzLTI1Ni1nY206MDQwN1dLSUVJWE1UTEdDNg==@qh62onjn.slashdevslashnetslashtun.net:16007#0225新加坡 
ss://YWVzLTI1Ni1nY206VENFTDFIMFhEN1RXQUtJMA==@qh62onjn.slashdevslashnetslashtun.net:15011#0225中国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk02.x.quickcht3.club:52612#0225中国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk01.x.quickcht3.club:52611#0225中国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0YTJyZml4b3BoZGpmZmE4S1ZBNEFh@beesyar.org:8080#0225荷兰 
vless://base64,MWE3YTM5ZTQtOGM5Yi00MDUyLWI4YjItYzA5Mjk1MzZiYmE1QDk1LjE2NC40Ljg4Ojg0NDM/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9cHEtYnJhemlsMS4wOXZwbi5jb20mdHlwZT13cyZob3N0PSZwYXRoPS92bGVzcy8maGVhZGVyVHlwZT1ub25lJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0225巴西 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0225斯洛文尼亚共和国 
ss://YWVzLTI1Ni1nY206UUYzNzdHR1EwMFJBVENNSw==@8tv68qhq.slashdevslashnetslashtun.net:21004#0225台湾 
ss://YWVzLTI1Ni1nY206WU1CM1FMODVMN0YxS0pSNw==@8tv68qhq.slashdevslashnetslashtun.net:18013#0225日本 
ss://YWVzLTI1Ni1nY206TFpRMFI5Qkw2OUdDQzZGUw==@8tv68qhq.slashdevslashnetslashtun.net:15005#0225中国 
ss://YWVzLTI1Ni1nY206SUhXTFlaU1NTWDRHU0tMQQ==@8tv68qhq.slashdevslashnetslashtun.net:16013#0225新加坡 
vless://base64,OGI1NGE2YzctMjU0NC00YTA3LTk1MjAtYjRlNTI1MmJhMmI3QDg5LjE4Ny4yOC4xMjY6ODQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT11bC1qYXBhbjEuMDl2cG4uY29tJnR5cGU9d3MmaG9zdD0mcGF0aD0vdmxlc3MvJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjZiMmEzMC41MGY4LTIyNjgtNDVlMC5jZmQiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeS7peiJsuWIlyIsIm5ldCI6IndzIiwiaWQiOiIwYmE0YTI0MC0xNTg2LTRhNTQtOTI5Yy0yNjM4OWM4YTQxMTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImpwMDFzLjUwZjgtMjI2OC00NWUwLmNmZCIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.204.173:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.184.126.174:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.34.200.48:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.32.166.45:443#0225美国 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDQ2LjE3LjQxLjE4OTo1MTIyND9pbnNlY3VyZT0xJnNuaT13d3cuYmluZy5jb20mYWxwbj0mZnA9Jm9zPQ==#0225俄罗斯 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0YTJyZml4b3BoZGpmZmE4S1ZBNEFh@45.87.175.199:8080#0225荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpjdklJODVUclc2bjBPR3lmcEhWUzF1@45.87.175.166:8080#0225荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0YTJyZml4b3BoZGpmZmE4S1ZBNEFh@45.87.175.164:8080#0225荷兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo0MzIzMCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlNmEyNzg5MS0wMmEzLTRkNzctYTRhMC05YWEyZTgzYTFmNTIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9Tc2lpP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJhcGkubmFtYXNoYS5jbyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ODVjZTdjYTYtZGYwYS00MmIyLWI4YzUtYTNmZDYxMGJlMzE4QDQ1LjgyLjEyMi4yMTE6NTc1MjA6d3M6LzRidjlhS0dEOVZjR0NwJTNGZWQlM0QyNTYwOmFwaS5uYW1hc2hhLmNvOm5vbmU6dGxzOmFwaS5uYW1hc2hhLmNvOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0225德国 
hysteria2://base64,dHg2THZiQlhIelVNbHhQbVdTZkRxQnVSdERVcW9SM0hjakA0NS44Mi4xMjIuMjExOjE1MDU3P2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD13TWpHWGgzZTljelp2SWRoRnJ3cmomb3M9#0225德国 
hysteria2://base64,Ujh0N1NmcXdNQ0xVcmRnaUZPeVRANDUuODIuMTIyLjIxMTozMTIzP2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1sYWgwY1p0aWtuM3NlRWlocTRMaVhaYUl1ekJXclNsR3NQa0c1Q2kmb3M9#0225德国 
trojan://base64,MGFjODdiNjQtZTNlZi00OGYxLTgyNGMtZjBhOWI0ZmU2NDczQDQ1LjgyLjEyMi4yMTE6MjU1OTU/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1hcGkubmFtYXNoYS5jbyZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9YXBpLm5hbWFzaGEuY28mcGF0aD0vU04xZ0hiU3BZZVVWd2dZejgxNTAyM2RnZGVqayUzRmVkJTNEMjU2MCZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225德国 
vless://base64,ZTZhMjc4OTEtMDJhMy00ZDc3LWE0YTAtOWFhMmU4M2ExZjUyQDQ1LjgyLjEyMi4yMTE6MjkwNz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT1hcGkubmFtYXNoYS5jbyZ0eXBlPXdzJmhvc3Q9YXBpLm5hbWFzaGEuY28mcGF0aD0vRTRiRWk2dUZDSyUzRmVkJTNEMjU2MCZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0225德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo1MDQ3LCJzY3kiOiJhdXRvIiwicHMiOiIwMjI15b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjcwNWE1ZGFiLTZlNjMtNDVmYy1iZDAwLTdkYWFhYTVhMzI5MiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiYXBpLm5hbWFzaGEuY28iLCJwYXRoIjoiL2RybEFmNGc2Nj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0IjozMDI4NCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0ZDZkOGNjMy01ZDg5LTQ0NGUtYThkYS05N2ZmZDBkODQyODAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9RNXVLTW1tNjdVNXRYdzk/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImFwaS5uYW1hc2hhLmNvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0Ijo0NTMzNCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4NWNlN2NhNi1kZjBhLTQyYjItYjhjNS1hM2ZkNjEwYmUzMTgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9oTT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NzA1YTVkYWItNmU2My00NWZjLWJkMDAtN2RhYWFhNWEzMjkyQDQ1LjgyLjEyMi4yMTE6NTYyNzU6d3M6L2MwUGlBUW1QcFlMMHBaNDA2bXFGRXp3dTZySzc4SE8lM0ZlZCUzRDI1NjA6YXBpLm5hbWFzaGEuY286bm9uZTp0bHM6YXBpLm5hbWFzaGEuY286W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0225德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMi4yMTEiLCJwb3J0IjoyNzgyNSwic2N5IjoiYXV0byIsInBzIjoiMDIyNeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI0MGJiYzVmMC1kNjFmLTRmYzEtYTJjZC05YjFiMGEwMjcwMmMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImFwaS5uYW1hc2hhLmNvIiwicGF0aCI6Ii9vM2hkUDF5aFNjUzZ6Y2hBTE5xdExpeDFiNj9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYXBpLm5hbWFzaGEuY28iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://base64,YmNhNjJkNjItMmE3MS00NWJiLWE1Y2EtNjhlMDAwMWRmNjA4QDQ1LjgyLjEyMi4yMTE6MTE5Nzc/Zmxvdz0mZW5jcnlwdGlvbj1ub25lJnNlY3VyaXR5PXRscyZzbmk9YXBpLm5hbWFzaGEuY28mdHlwZT13cyZob3N0PWFwaS5uYW1hc2hhLmNvJnBhdGg9L2pBblVDcXc5OHFsVFJUWU5vYnBPZ0lMYlRjWlR5JTNGZWQlM0QyNTYwJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NGQ2ZDhjYzMtNWQ4OS00NDRlLWE4ZGEtOTdmZmQwZDg0MjgwQDQ1LjgyLjEyMi4yMTE6MzA1Nzk6d3M6L1VWeVlzZ2s5VHFoRXR4S0pqMnhodzUlM0ZlZCUzRDI1NjA6YXBpLm5hbWFzaGEuY286bm9uZTp0bHM6YXBpLm5hbWFzaGEuY286W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0225德国 
hysteria2://base64,ekxXMW9sWmZQV1haUTNqOXl6MU96TFowS1JOd2pzSUxUbkdhQDQ1LjgyLjEyMi4yMTE6NjQ5Njg/aW5zZWN1cmU9MSZzbmk9YXBpLm5hbWFzaGEuY28mYWxwbj0mZnA9Jm9iZnM9c2FsYW1hbmRlciZvYmZzLXBhc3N3b3JkPVlKaHB2Y0JrZzZXSjRYYzFHRjBnbFVZVTRqTUVEV3FTJm9zPQ==#0225德国 
hysteria2://base64,aTNBajkxa015S2h3YjdFa0hZZ2toZUA0NS44Mi4xMjIuMjExOjU3NjQ0P2luc2VjdXJlPTEmc25pPWFwaS5uYW1hc2hhLmNvJmFscG49JmZwPSZvYmZzPXNhbGFtYW5kZXImb2Jmcy1wYXNzd29yZD1RT1E5Z3VjRU5TUExIaVhERkF4dTFxamVOWVhaRVpqa2h0VTJGZksmb3M9#0225德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMjI15rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@44.243.45.146:443#0225美国 
vless://base64,NmY5OTUwNTYtNzgwMi00YTFkLWJmZjctNjE2NzhlNjI2YzNmQDQwLjY5LjEwNi4xMDM6NDQzP2Zsb3c9JmVuY3J5cHRpb249bm9uZSZzZWN1cml0eT10bHMmc25pPW1tZ2hneTUuYXp1cmV3ZWJzaXRlcy5uZXQmdHlwZT13cyZob3N0PW1tZ2hneTUuYXp1cmV3ZWJzaXRlcy5uZXQmcGF0aD0vJmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225加拿大 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDIyNeazouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.160.134.223:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.220.211.62:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.220.174.155:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.217.75.205:443#0225美国 
ss://YWVzLTI1Ni1jZmI6YzNOdEhKNXVqVjJ0R0Rmag==@217.30.10.18:9084#0225波兰 
ss://YWVzLTI1Ni1jZmI6TTN0MlpFUWNNR1JXQmpSYQ==@217.30.10.18:9011#0225波兰 
ss://YWVzLTI1Ni1jZmI6ZjhucEtnTnpka3NzMnl0bg==@217.30.10.18:9088#0225波兰 
ss://YWVzLTI1Ni1jZmI6WkVUNTlMRjZEdkNDOEtWdA==@217.30.10.18:9005#0225波兰 
ss://YWVzLTI1Ni1jZmI6Qk5tQVhYeEFIWXBUUmR6dQ==@217.30.10.18:9020#0225波兰 
ss://YWVzLTI1Ni1jZmI6VTZxbllSaGZ5RG1uOHNnbg==@217.30.10.18:9041#0225波兰 
ss://YWVzLTI1Ni1jZmI6OVh3WXlac0s4U056UUR0WQ==@217.30.10.18:9059#0225波兰 
ss://YWVzLTI1Ni1jZmI6Y3A4cFJTVUF5TGhUZlZXSA==@217.30.10.18:9064#0225波兰 
ss://YWVzLTI1Ni1jZmI6QndjQVVaazhoVUZBa0RHTg==@217.30.10.18:9031#0225波兰 
ss://YWVzLTI1Ni1jZmI6cDl6NUJWQURIMllGczNNTg==@217.30.10.18:9040#0225波兰 
hysteria2://base64,ZG9uZ3RhaXdhbmcuY29tQDE5NS4xNTQuMzMuNzA6MTM4NjE/aW5zZWN1cmU9MSZzbmk9d3d3LmJpbmcuY29tJmFscG49JmZwPSZvcz0=#0225法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@188.214.36.155:989#0225爱沙尼亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4OC4xMzAuMTU0LjU2IiwicG9ydCI6MjI5NDYsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXoiqzlhbAiLCJuZXQiOiJ0Y3AiLCJpZCI6IjdlZDFkMTM4LTM3ZjctNDFmNy04NDNkLWQ0ZjJiZGJiYTkxMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.253.171:989#0225厄瓜多尔 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.47.252.251:989#0225秘鲁 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.237.185.160:989#0225立陶宛 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.173:989#0225波兰 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.193.49.88:989#0225爱沙尼亚 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4xNzQuMTM4LjE5NiIsInBvcnQiOjIwODIsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiM2Y2MzhmMzQtOGRiYS00MTg2LWJjNDMtMjcxNmE3ZGRkNGJlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ5ZWxsb3ctcGFwZXItMDI5Yy55dm9ubmEud29ya2Vycy5kZXYiLCJwYXRoIjoiL2F6MDUuYmV5b25keS5jZmQvbGluaz8vVE1AQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjFAQVpBUkJBWUpBQjEvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MzkwMiwic2N5IjoiYXV0byIsInBzIjoiMDIyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo0MjEyMCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1OTEwNCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MTc1NCwic2N5IjoiYXV0byIsInBzIjoiMDIyNeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@181.119.30.20:990#0225哥伦比亚 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@176.103.53.105:989#0225乌克兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4xNzIuMTY4IiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNGJmMDc0ZjQtN2U5Yy00ZTRiLWExMGQtMTU2ZTI2MTk5NzI5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1czAzcy41ZDhlY2Y4Mi5jZmQiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://base64,cUNmdTh0JHN7Mm07c1R4bUAxNzIuNjYuNDQuMTk0OjIwNTM/Zmxvdz0mc2VjdXJpdHk9dGxzJnNuaT1KT2luTWFIZElTZVJ2RXItQzFDLlBhR0VTLmRFViZ0eXBlPXdzJmhlYWRlcj1ub25lJmhvc3Q9am9pbm1haGRpc2VydmVyLWMxYy5wYWdlcy5kZXYmcGF0aD0vdHJqOUZJMm9JR243ZFpjNGczJTNGZWQlM0QyNTYwJmFscG49JmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0225日本 
vless://base64,OWY0NzZiMzEtNWI5Zi00YjAzLTg4NDYtMmI1ZGM5ZWZjZWU3QDE3Mi42Ni4xNjguMjAxOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT10Ui1GdWxsLlBSSXZhdEVJUC5OZXQmdHlwZT13cyZob3N0PXRSLUZ1bGwuUFJJdmF0RUlQLk5ldCZwYXRoPS9WTEVTUyZoZWFkZXJUeXBlPW5vbmUmYWxwbj0mZnA9JnBiaz0mc2lkPSZzcHg9JmFsbG93SW5zZWN1cmU9MSZmcmFnbWVudD0sMTAwLTIwMCwxMC02MCZvcz0=#0225土耳其 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@154.90.37.139:990#0225菲律宾 
vless://base64,M2I5YmM3NzMtMDVlYi00ZDVmLThjMWYtNTczNDJjMGM0ZjQwQDE0Ny4xMzUuMTAuMTAzOjQ0Mz9mbG93PSZlbmNyeXB0aW9uPW5vbmUmc2VjdXJpdHk9dGxzJnNuaT0xNDcxMzUwMTAxMDMuc2VjMTlvcmcuY29tJnR5cGU9dGNwJmhvc3Q9JnBhdGg9JmhlYWRlclR5cGU9bm9uZSZhbHBuPSZmcD0mcGJrPSZzaWQ9JnNweD0mYWxsb3dJbnNlY3VyZT0xJmZyYWdtZW50PSwxMDAtMjAwLDEwLTYwJm9zPQ==#0225美国 
hysteria2://base64,aU1xWTN1R181cGdFajNoQ2Z5SEItMHZCQDE0My4xOTguMjM1LjQ5OjQ0Mz9pbnNlY3VyZT0xJnNuaT0mYWxwbj0mZnA9Jm9zPQ==#0225美国 
ss://Y2hhY2hhMjA6QURabVJRVUdIVHdY@14.18.253.178:8339#0225韩国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0225以色列 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0225孟加拉国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0225日本 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0225新加坡 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0225法国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@134.255.210.49:989#0225塞浦路斯 
trojan://base64,dGVsZWdyYW0taWQtcHJpdmF0ZXZwbnNAMTMuNjEuMjAwLjE0NToyMjIyMj9mbG93PSZzZWN1cml0eT10bHMmc25pPXRyb2phbi5idXJnZXJpcC5jby51ayZ0eXBlPXRjcCZoZWFkZXI9bm9uZSZob3N0PSZwYXRoPSZhbHBuPWh0dHAvMS4xJmZwPSZwYms9JnNpZD0mc3B4PSZhbGxvd0luc2VjdXJlPTEmZnJhZ21lbnQ9LDEwMC0yMDAsMTAtNjAmb3M9#0225瑞典 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMjI1576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6aEdrUTY5MTV0RA==@120.232.81.50:15084#0225日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6MzYwMDIsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjQwIiwicG9ydCI6NTQwODIsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXkuK3lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE2IiwicG9ydCI6NTU0ODIsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAyMjXml6XmnKwiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://base64,ZWJhZTdhMjctNjc0Yi00YTIyLWIxYmUtZmY0NTZjZGEyMjEwQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0225美国 
hysteria2://base64,MDRhNDA3YTUtZjc5My00MTE3LWE0NzktNGY4ZTJkMWVlMzdlQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0225美国 
hysteria2://base64,NDU0N2RlYzctMTM4OS00NTM2LWE0NzUtYWE4Mjk1Zjk4ZDJmQDEwNy4xNzIuMjM1Ljc1OjQzNjE1P2luc2VjdXJlPTEmc25pPWR4b2JnNGF6bWsuZ2Fmbm9kZS5zYnMmYWxwbj0mZnA9Jm9zPQ==#0225美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@103.106.229.219:989#0225新加坡 


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
