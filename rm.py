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

vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.18.43.169:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.21.21.181:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107日本 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.21.51.114:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.21.7.41:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.21.8.135:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4yMS44OS4yMTkiLCJwb3J0IjoyMDg2LCJzY3kiOiJhdXRvIiwicHMiOiIwMTA36Zi/5ouJ5Lyv6YWL6ZW/5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjNmZDdiOTU4LTIxNjEtNDZlMS1iNmZjLWJkNmJiMjE2NTMxMiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoic2hzLnhpYW9xaTY2Ni54eXoiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNocy54aWFvcWk2NjYueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.26.10.197:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@104.27.0.44:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107韩国 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@107.155.57.11:8080#0107美国 
vless://8ea00d88-3089-4fdc-e0d4-566bf11c3c4c@107.172.25.166:443?flow=&encryption=none&security=&sni=&type=ws&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MjI3NDYsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNDdlYjUzYzktY2I5MC00MzM1LWJhODMtZDI5YjQ3ZTExMTU3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvWXRpbyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
hysteria2://mTa7rAg6Ki2NPmSXvZNycFxGtbsg@109.71.253.167:64239?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=OPbfSMillv4OCHejv5bB9ic&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NjQwNjUsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNDRlNTVjM2UtMmI3NC00ZWJmLTk2ZjQtMDQ2YzVhMzkxNTQ2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvUXd1QlJiIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://1c28bac5-e230-4dce-a62b-281e5d87e0a4@109.71.253.167:59055?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/8SaCtCVMWJILQ72mzQG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://aIjWpYyBWAslgMFkTc@109.71.253.167:59234?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=ptXTgUe1rx8OgbSg&os=#0107德国 
trojan://364c8c8f-510c-463f-9791-120d48353270@109.71.253.167:2745?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/EgAhLkrxWdC&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://4a8ef652-db13-4e91-b56a-cc205e94ac6d@109.71.253.167:24253?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NDRlNTVjM2UtMmI3NC00ZWJmLTk2ZjQtMDQ2YzVhMzkxNTQ2QDEwOS43MS4yNTMuMTY3OjM1Nzg2OndzOi9NQnk3bjVCRGx1ZTp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
hysteria2://MMu7BuHFl0KeX8fsNTPA4NvmkOiMK1H@109.71.253.167:24726?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=fG50TdQIkHEvTaooWfDUjATeP21Ah&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmI4MWFmNjQtYzc5Yy00MGRmLWJjM2MtNzRmOTRmZDViZjFhQDEwOS43MS4yNTMuMTY3OjEyODcyOndzOi9VUzlEbkd4MU9hQ3A6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0107德国 
hysteria2://QjBAq60kKU2yQ3GSwn@109.71.253.167:48254?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=UmhhpIHiMSPtzNOFxyq0H2bqCYRLMguI&os=#0107德国 
vless://53243c3a-8666-4a54-a666-2adbf461ce79@109.71.253.167:31392?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/lY2g49KhPkzJdCx0vvZsT4&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://14d36722-2510-408e-9a77-35b03491adf9@109.71.253.167:4563?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/RfZjOP7CDuptePT&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NzU4OSwic2N5IjoiYXV0byIsInBzIjoiMDEwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJlNmFhNzE0NC0zM2EwLTRjNGUtOWRmOC1mNTBlYzY0YTY1ZjgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii8yU3JiVHp5d3lqN3N0UzgiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NTM5MDQsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMTRkMzY3MjItMjUxMC00MDhlLTlhNzctMzViMDM0OTFhZGY5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvd3hwdXJhTjZBNmU0cmk5eWNQN2RNS0F4YjVOIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MGVhYTdhODgtMmFhMi00MWFiLWIxMWUtMjQxMzZiYjcyZDFkQDEwOS43MS4yNTMuMTY3OjM4MDY5OndzOi9acFpGOHJWQlRKYTp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MTRkMzY3MjItMjUxMC00MDhlLTlhNzctMzViMDM0OTFhZGY5QDEwOS43MS4yNTMuMTY3OjE4NTY4OndzOi9hMjRSZ1hPaTp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MzY0YzhjOGYtNTEwYy00NjNmLTk3OTEtMTIwZDQ4MzUzMjcwQDEwOS43MS4yNTMuMTY3OjE3OTI1OndzOi9udWtFSXBZRzJ3VGZZcWc3OnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
hysteria2://tfZHDRjP99OFYHTpjHyc0rVj737u@109.71.253.167:38452?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=wYVvGg8PV5BrREO7R51CgsvSvEHzn0E&os=#0107德国 
vless://47eb53c9-cb90-4335-ba83-d29b47e11157@109.71.253.167:63256?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/RZbZhzlmoN6qWiwuf0ngmMZlnqqfuPtt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://bb81af64-c79c-40df-bc3c-74f94fd5bf1a@109.71.253.167:57825?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/T&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MjIzMjIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNGE4ZWY2NTItZGIxMy00ZTkxLWI1NmEtY2MyMDVlOTRhYzZkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvbG9YVGVzUlphaEM4UjBZSFNnQiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://364c8c8f-510c-463f-9791-120d48353270@109.71.253.167:5524?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/uTuI1frR6pyHdu8S4EulwZi7&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YzBjMDVjZmMtZjZlMy00MDg1LWJjYTgtZWRiYjEyNjdiMmViQDEwOS43MS4yNTMuMTY3OjI0NzU0OndzOi9hQjQ6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0107德国 
hysteria2://aXdM1yojfnLeLOAFIcrz901urpZ@109.71.253.167:26243?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=CP2qm2mun1oc8HUsBt&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MzgxNDksInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZTk3NGQyYTUtOWVhOS00Yzc1LTg1ZWEtNjA1M2MwNmU3MjE0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvVlE5Z0k2OG1HaXhEcWR6ZTM0NVRnbXIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6OGFlMWMwYmQtMmYxNS00OWFlLWJlZDgtYTcxY2Y2YjFhYWQxQDEwOS43MS4yNTMuMTY3Ojg1ODA6d3M6L0RES0hyZDIxMm03czp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MGE4ZTljMTYtMDY3YS00MTY2LTg4ZjktNmUxMjAxZGQxMmI5QDEwOS43MS4yNTMuMTY3OjU1NDY2OndzOi9MZWpuc1lYVUxnOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
vless://44e55c3e-2b74-4ebf-96f4-046c5a391546@109.71.253.167:21371?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/tcM9cfSS3bYHBPd&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://yRaE6Raaut34Gucoxt6C4KjrXu5sX3198a90o@109.71.253.167:12294?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=eFK9ldeIkUOMDfABe1vYJ&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MjA5NDBhMDktNjkyZS00YTYzLThhM2EtZmZhYTk5OWU1ODE1QDEwOS43MS4yNTMuMTY3OjI5NDM3OndzOi9pMDF6UENZQXBSODZ5dXRVVTp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
vless://f604d228-1b03-40d0-9821-96766d66551e@109.71.253.167:15450?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/xwNETW175aVGB7JG90gnmwtUvgiG4&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://069ijm0mRqy17kwzaUtTx8BA28@109.71.253.167:55483?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=tT1u0jDJr5q797UtrEUci8hUhO5cOdvsH5&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NGE4ZWY2NTItZGIxMy00ZTkxLWI1NmEtY2MyMDVlOTRhYzZkQDEwOS43MS4yNTMuMTY3OjIzNDY3OndzOi9xN2ZsRG9SdXRkckY4UmFQc1V6NENPVWdEQzp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MzU3NDcsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiNTMyNDNjM2EtODY2Ni00YTU0LWE2NjYtMmFkYmY0NjFjZTc5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvTTBNdXZjY21IOGxBcm9mU2lScVgwWGhrT05EV2FNbCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://aa99d63f-42b0-46ff-ac82-7427f00940c9@109.71.253.167:46113?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/r8XcghTPIZgze&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjFhNmUwYzQtOTY3NC00M2JjLWFjNzgtMThlMDUxNTAwNDk3QDEwOS43MS4yNTMuMTY3OjUyMjk1OndzOi9FUkJ6c2U6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NDQyNjksInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZjYwNGQyMjgtMWIwMy00MGQwLTk4MjEtOTY3NjZkNjY1NTFlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvSjZFM0I1ODJJcUxqTDdKU000M2kiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://0a8e9c16-067a-4166-88f9-6e1201dd12b9@109.71.253.167:23283?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/tcMj6&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://1c28bac5-e230-4dce-a62b-281e5d87e0a4@109.71.253.167:24329?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/JcW9D&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://l1iBdFfBSsH28ZjpgSXEzJUoc86@109.71.253.167:11351?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=HkBkd0O2gJFlhTzFd3ZzuiLmVH4&os=#0107德国 
trojan://bb81af64-c79c-40df-bc3c-74f94fd5bf1a@109.71.253.167:15495?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/2Ov3kM2xkqq17nq2bfczM98Vc&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://14d36722-2510-408e-9a77-35b03491adf9@109.71.253.167:24095?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/fY4czLFRqFwJ&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://44e55c3e-2b74-4ebf-96f4-046c5a391546@109.71.253.167:59656?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/d9oH&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MTQ3MzYsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMGVhYTdhODgtMmFhMi00MWFiLWIxMWUtMjQxMzZiYjcyZDFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvVFpEQmFPYVpJRXNZIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZTk3NGQyYTUtOWVhOS00Yzc1LTg1ZWEtNjA1M2MwNmU3MjE0QDEwOS43MS4yNTMuMTY3OjMzMjE4OndzOi9IWjkyMVU0d2E6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTo6OltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
hysteria2://ppohD6vroVCPCaPzDb7ltqsiTn@109.71.253.167:27023?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=l7xWwEmNRoiyh8YcIoNcqatbPZSmiVbN&os=#0107德国 
hysteria2://1jsI4BFGKB8arwOpwB2GSnqw05zvh7PM85@109.71.253.167:37099?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=We8MnQYrm6ie8s7cNYmOD&os=#0107德国 
trojan://c0c05cfc-f6e3-4085-bca8-edbb1267b2eb@109.71.253.167:9005?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/T4fG1U7DoIDgmexKNSOZM&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NTY4MTQsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiYzBjMDVjZmMtZjZlMy00MDg1LWJjYTgtZWRiYjEyNjdiMmViIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvOXJyam5FeVFnaHRKSnN3WiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NzgyNiwic2N5IjoiYXV0byIsInBzIjoiMDEwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzNjRjOGM4Zi01MTBjLTQ2M2YtOTc5MS0xMjBkNDgzNTMyNzAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9ET2ljSjlyalJrVmQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NDc0NDQsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiYmI4MWFmNjQtYzc5Yy00MGRmLWJjM2MtNzRmOTRmZDViZjFhIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvSEpla25xRGhNS0wwcDdxcUZRQm9MVEZaUVZzQVlwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NjEyODIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiOGFlMWMwYmQtMmYxNS00OWFlLWJlZDgtYTcxY2Y2YjFhYWQxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvc05TdjJOcVFrcEFQQ0o0MmpjaWpaN2giLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZjYwNGQyMjgtMWIwMy00MGQwLTk4MjEtOTY3NjZkNjY1NTFlQDEwOS43MS4yNTMuMTY3OjUxMDAxOndzOi9MU2pYOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NDdlYjUzYzktY2I5MC00MzM1LWJhODMtZDI5YjQ3ZTExMTU3QDEwOS43MS4yNTMuMTY3OjYwNDI5OndzOi9IbHJUZmpZM0tEdTp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
trojan://4a8ef652-db13-4e91-b56a-cc205e94ac6d@109.71.253.167:41303?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/u0kpoChGZoOPwWlDyQsE&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://f604d228-1b03-40d0-9821-96766d66551e@109.71.253.167:54302?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/Su0gVMXkEGJuoikFf9WSA&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YWY1OTlmMDEtNzU2MC00NzBhLWI5NzUtMWExZDJmZGFhZDA1QDEwOS43MS4yNTMuMTY3OjYxMzg2OndzOi9kVkNrd0hPdzlNZDlLMGRHY3Mza0lpeWY0Y0FLbTQ6dXBkYXRlLm1pY3Jvc29mdC5jb206bm9uZTp0bHM6dXBkYXRlLm1pY3Jvc29mdC5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmY3MzI2ZmItODAyNy00MGRkLTgyNmUtZmM3ZWFhMTc1NWExQDEwOS43MS4yNTMuMTY3Ojg4MzY6d3M6Lzp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MjYyMDksInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMGE4ZTljMTYtMDY3YS00MTY2LTg4ZjktNmUxMjAxZGQxMmI5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIveUpNUVNaYzR6NHFucGZBTDlUT3RQelljVHpOZ0JHIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://20940a09-692e-4a63-8a3a-ffaa999e5815@109.71.253.167:4745?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/jR0kDrM0p8l6OKsLpm9dWGs&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://bf7326fb-8027-40dd-826e-fc7eaa1755a1@109.71.253.167:56689?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/WLDDyyM3lz9ISlbhFFVJznCHo7mykEQU&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://af599f01-7560-470a-b975-1a1d2fdaad05@109.71.253.167:41788?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/hREZfCTcrH2RdSI&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YWE5OWQ2M2YtNDJiMC00NmZmLWFjODItNzQyN2YwMDk0MGM5QDEwOS43MS4yNTMuMTY3OjMwNjg5OndzOi9zWWRxT2IwRU9WaGVsRzp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MTY3MjAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiYWY1OTlmMDEtNzU2MC00NzBhLWI5NzUtMWExZDJmZGFhZDA1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvNDlsUVNEMnY5IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
hysteria2://WjyJwYpmXfIGlBNdHg3Ri0g@109.71.253.167:45607?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=qmB9yBhgxwkra1WRvCshEFfVTB&os=#0107德国 
vless://befaa7c3-c999-49c3-b541-b407d62145ab@109.71.253.167:6475?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/EXgBlngW4GHDpeKdvsiBhOn04l&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6Njc2Miwic2N5IjoiYXV0byIsInBzIjoiMDEwN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJiZWZhYTdjMy1jOTk5LTQ5YzMtYjU0MS1iNDA3ZDYyMTQ1YWIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6InVwZGF0ZS5taWNyb3NvZnQuY29tIiwicGF0aCI6Ii9xMm9sRzNXbDZTVjM4TGx2Sk1lNDMiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://Zh2zvuZCrzaCQAFL5@109.71.253.167:50251?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=jetDNkDaFZbABtxT9ze1gyoItVTU4MH&os=#0107德国 
hysteria2://V60AMDJ2vjGpe667@109.71.253.167:13933?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=XT3Vbn8OdRXIY75lvzWj1sQwR68Yqd7&os=#0107德国 
vless://8ae1c0bd-2f15-49ae-bed8-a71cf6b1aad1@109.71.253.167:18808?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/WBiHv6ET14uJjhZ4XUgCjEp&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://0eaa7a88-2aa2-41ab-b11e-24136bb72d1d@109.71.253.167:42743?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/baXqao7sK3yKQ0bHRXwVk&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://8ae1c0bd-2f15-49ae-bed8-a71cf6b1aad1@109.71.253.167:59699?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/7WGo9qeEBp8HtB&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://47eb53c9-cb90-4335-ba83-d29b47e11157@109.71.253.167:36542?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/pUJs0Sx3&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://befaa7c3-c999-49c3-b541-b407d62145ab@109.71.253.167:36239?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/14nPATRGxpFdI&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://aa99d63f-42b0-46ff-ac82-7427f00940c9@109.71.253.167:13260?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/rQmf5VhCSX05Fq3xhuheNxuy&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://1WRWtm606Qwt5fEE@109.71.253.167:2816?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=TzsOeUPgn8sQMKn46ahCNF0jefqP1YAf&os=#0107德国 
hysteria2://30M6HpR1KQL5bYCVzle@109.71.253.167:2034?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=GotqgS8ZknhExf7hAxOBBr5Ewmp4y5Sb9YuGx9sm&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6NTMyNjQsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMWMyOGJhYzUtZTIzMC00ZGNlLWE2MmItMjgxZTVkODdlMGE0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MTAwOTQsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiYmY3MzI2ZmItODAyNy00MGRkLTgyNmUtZmM3ZWFhMTc1NWExIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvYzFpU2JLV1F1OHpWOTdBbmp3OHhOS3FDTGV1d1N5IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZTZhYTcxNDQtMzNhMC00YzRlLTlkZjgtZjUwZWM2NGE2NWY4QDEwOS43MS4yNTMuMTY3OjMxMDk4OndzOi9vOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
trojan://0eaa7a88-2aa2-41ab-b11e-24136bb72d1d@109.71.253.167:26671?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/aKasyBYvxyyueYGCgbGChZeLLmG&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://e6aa7144-33a0-4c4e-9df8-f50ec64a65f8@109.71.253.167:25677?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/uWFyApp9reVdTztK28SCtVMxi&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6Mzg3MzAsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiYWE5OWQ2M2YtNDJiMC00NmZmLWFjODItNzQyN2YwMDk0MGM5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvZkxoWml5VHF2IiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXBkYXRlLm1pY3Jvc29mdC5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://f1a6e0c4-9674-43bc-ac78-18e051500497@109.71.253.167:24499?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/pJOzpRz0M4kNEsJNfK7T5yDvvpWk&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://WSIYkqFaaEn7LKID3@109.71.253.167:14670?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=QmoBZ4Cj3hsi7iYE3RK18KvGkhqwEo9eE5U53Bnf&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6NTMyNDNjM2EtODY2Ni00YTU0LWE2NjYtMmFkYmY0NjFjZTc5QDEwOS43MS4yNTMuMTY3OjE0Nzc4OndzOi9sR1RhWkVxTnB5dXpMT0RxMWhMMkdIOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
vless://c0c05cfc-f6e3-4085-bca8-edbb1267b2eb@109.71.253.167:15598?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/aQeppVsHzIIajufcCE7ZXMpQvGWN8&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://af599f01-7560-470a-b975-1a1d2fdaad05@109.71.253.167:42709?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/GJe6mBbvspSlOZTQcz&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://53243c3a-8666-4a54-a666-2adbf461ce79@109.71.253.167:26017?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/nCF8Jtuk5tpDmE&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmVmYWE3YzMtYzk5OS00OWMzLWI1NDEtYjQwN2Q2MjE0NWFiQDEwOS43MS4yNTMuMTY3OjQ2NDQxOndzOi85ekVNQWdLOnVwZGF0ZS5taWNyb3NvZnQuY29tOm5vbmU6dGxzOnVwZGF0ZS5taWNyb3NvZnQuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0107德国 
trojan://e6aa7144-33a0-4c4e-9df8-f50ec64a65f8@109.71.253.167:56143?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/Y1ga&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6MjI0NDgsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiZjFhNmUwYzQtOTY3NC00M2JjLWFjNzgtMThlMDUxNTAwNDk3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvcU5vRFJmWHgiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://0a8e9c16-067a-4166-88f9-6e1201dd12b9@109.71.253.167:34128?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/7vHT&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://31hqmfsTxxOjaH9Fd@109.71.253.167:58628?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=V3UivAj323ulufrmRzlQ5omsgqgv3eFf&os=#0107德国 
vless://bf7326fb-8027-40dd-826e-fc7eaa1755a1@109.71.253.167:15383?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/aye8F9iTLTGKA9xLzSpDy&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://zfAMpkQP2rLVRbk9R9aDuabzN@109.71.253.167:51296?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=CslJckAQlfCsLJftRj&os=#0107德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MWMyOGJhYzUtZTIzMC00ZGNlLWE2MmItMjgxZTVkODdlMGE0QDEwOS43MS4yNTMuMTY3OjIwNTkxOndzOi9nckVRQjZlOHpSWWQ1TjFodzp1cGRhdGUubWljcm9zb2Z0LmNvbTpub25lOnRsczp1cGRhdGUubWljcm9zb2Z0LmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0107德国 
hysteria2://WVIg6RmG5fQldQTNj@109.71.253.167:62094?insecure=1&sni=update.microsoft.com&alpn=&fp=&obfs=salamander&obfs-password=XRceYJl7nwQvEXrK3x1as71C7hEua&os=#0107德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwOS43MS4yNTMuMTY3IiwicG9ydCI6Mzk4MTgsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDflvrflm70iLCJuZXQiOiJ3cyIsImlkIjoiMjA5NDBhMDktNjkyZS00YTYzLThhM2EtZmZhYTk5OWU1ODE1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsInBhdGgiOiIvdzNzcW9GTTFhOGtRdDRGMkVhU2o4N1giLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ1cGRhdGUubWljcm9zb2Z0LmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
trojan://20940a09-692e-4a63-8a3a-ffaa999e5815@109.71.253.167:65135?flow=&security=tls&sni=update.microsoft.com&type=ws&header=none&host=update.microsoft.com&path=/JU7XhJf80uHbdf4ZHFL0kY&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://f1a6e0c4-9674-43bc-ac78-18e051500497@109.71.253.167:4214?flow=&encryption=none&security=tls&sni=update.microsoft.com&type=ws&host=update.microsoft.com&path=/WRmk5U41hZ6MSKuCfGoV&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@112.213.102.228:4231#0107香港 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE0IiwicG9ydCI6MzQ0OTMsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfmlrDliqDlnaEiLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA5NzIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6Ijc3MGVlNzMwLTI0NTAtNGUzYy1hNmM2LTM5MzJiZDMyYWZiZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDA1NjUsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzQuMTAyLjIyOSIsInBvcnQiOjUyOTA4LCJzY3kiOiJhdXRvIiwicHMiOiIwMTA3576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiI0MTgwNDhhZi1hMjkzLTRiOTktOWIwYy05OGNhMzU4MGRkMjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjY0LCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.250.115.217:443#0107新加坡 
trojan://telegram-id-privatevpns@13.37.123.220:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107法国 
trojan://telegram-id-privatevpns@13.39.96.175:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107法国 
trojan://telegram-id-privatevpns@13.41.102.111:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107英国 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@135.148.177.196:443?flow=&encryption=none&security=tls&sni=147135001178.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://0ea2f1b5-48c5-40c2-8496-5fdf856caafe@138.124.53.161:443?flow=&encryption=none&security=tls&sni=ad4.transitkala.com&type=ws&host=ad4.transitkala.com&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@140.238.23.148:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107韩国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@144.24.200.164:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107日本 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@146.70.61.18:8080#0107英国 
vless://ea286109-d20f-415e-849e-4af20ab04b65@147.135.1.195:443?flow=&encryption=none&security=tls&sni=147135001195.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107美国 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@147135001178.sec22org.com:443?flow=&encryption=none&security=tls&sni=&type=tcp&host=&path=&headerType=none&alpn=http/1.1%2Ch2&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107美国 
vless://ea286109-d20f-415e-849e-4af20ab04b65@147135001195.sec22org.com:443?flow=&encryption=none&security=tls&sni=&type=tcp&host=&path=&headerType=none&alpn=http/1.1%2Ch2&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107美国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@147135010103.sec19org.com:443?flow=&encryption=none&security=tls&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107美国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@15.204.153.78:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://7fce54eb-23d4-4f1e-a5e3-3749aaee2cfd@151.101.0.155:80?flow=&encryption=none&security=&sni=gytfyifhgvhvvgf.com&type=ws&host=gytfyifhgvhvvgf.com&path=/telegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%2Ctelegram-NUFiLTER%3Fed%3D888&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://3a67aaab-515e-4079-a518-d00cb5e6b20e@151.101.158.204:80?flow=&encryption=none&security=&sni=zmaoz.faculty.ucdavis.edu.&type=ws&host=fatmelo.com&path=/olem/ws%3Fed%3D64&headerType=none&alpn=http/1.1%2Ch2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107芬兰 
vless://8167f943-0513-5c93-bda3-2ec02522cd8a@151.101.193.6:80?flow=&encryption=none&security=&sni=&type=ws&host=PABLO-MOSTAFAA.COM&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://68601963-27c2-4253-c784-914782ce09ef@151.101.194.219:80?flow=&encryption=none&security=&sni=&type=ws&host=foffmelo.com&path=/olem/ws%3Fed%3D1024&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://5eaa121d-4362-444d-8219-29b02c35303a@151.249.104.35:34623?insecure=1&sni=jquery.com&alpn=&fp=&os=#0107捷克 
hysteria2://ff006ffb-ad09-4d79-8c27-91dcd9123d8b@151.249.104.35:34623?insecure=1&sni=digitalocean.com&alpn=&fp=&os=#0107捷克 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@152.67.203.34:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1Mi43MC4yNDkuMTUyIiwicG9ydCI6MjM0NTEsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfpn6nlm70iLCJuZXQiOiJ3cyIsImlkIjoiNDQ4NWMyMTUtZWI1NC00MmY0LWJkMjUtZjVlMWE2MDYyN2IyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@154.197.26.237:8388#0107香港 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@154.90.37.139:989#0107菲律宾 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@159.69.22.135:1001?flow=&encryption=none&security=tls&sni=a.mifeng.us.kg&type=ws&host=a.mifeng.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://94d219c9-1afc-4d42-b090-8b3794764380@160.30.21.105:443?flow=&security=tls&sni=std1.loadingip.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107越南 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@172.64.147.50:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@172.66.40.228:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@172.67.194.21:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%2C%40icv2ray%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42Ny4yMDQuMTkiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiNWY3MjZmZTMtZDgyZS00ZGE1LWE3MTEtOGFmMGNiYjJiNjgyIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIxYTJkNTE0Yi0zN2NmLTQ5OWYtOGQwOC1kMDE3YTkyYWI1YmIuYXNvdWwtYXZhLnRvcCIsInBhdGgiOiIvYXp1bWFzZS5yZW4iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIxYTJkNTE0Yi0zN2NmLTQ5OWYtOGQwOC1kMDE3YTkyYWI1YmIuYXNvdWwtYXZhLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@172.67.70.99:443?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.181.162.137:443#0107日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNDguMTU4IiwicG9ydCI6NTAwNTIsInNjeSI6ImF1dG8iLCJwcyI6IjAxMDfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo0MTAyMCwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo0NjYwMiwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MTcwNCwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MzAwMiwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NDEwNCwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1NjYwMSwic2N5IjoiYXV0byIsInBzIjoiMDEwN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMjMiLCJwb3J0Ijo1MjExMiwic2N5IjoiYXV0byIsInBzIjoiMDEwN+e+juWbvSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.123.101.241:989#0107土耳其 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0107丹麦 
ss://YWVzLTI1Ni1nY206ZG9uZ3RhaXdhbmcuY29t@185.22.155.228:23456#0107俄罗斯 
vless://d342d11e-d424-4583-b36e-524ab1f0afa4@192.210.160.163:1001?flow=&encryption=none&security=tls&sni=a.xn--i-sx6a60i.us.kg&type=ws&host=a.xn--i-sx6a60i.us.kg&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
trojan://Julius@193.106.248.196:443?flow=&security=tls&sni=miami.juliusnet.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@194.5.215.59:8080#0107美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5NS41OC40OS41MCIsInBvcnQiOjEwODgxLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6ImFmMDZlNzVmLTc1MTEtNDQ0NC05MWJiLWVlNjAzMjIxOTNlYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5OS4yMzIuMjE0LjEzMyIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDEwN+azleWbvSIsIm5ldCI6IndzIiwiaWQiOiJlNTg1MjM5My1jYTUyLTRjOTAtYTIzNy1kNjNjYmJiNTdmMjEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6Imxva2kub3JhY2xlIiwicGF0aCI6Ii9mYXJjcnk/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=207.148.22.93&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0107美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0107美国 
hysteria2://9bb452b106ffc217@207.148.22.93:443?insecure=1&sni=vkvd127.mycdn.me&alpn=&fp=&obfs=salamander&obfs-password=cd29099d&os=#0107美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpucTk2S2Z0clpBajNMdUZRRVNxbW40NE1vNW9DdW8yY2lwb0VzYWUyNW1ybUhHMm9KNFZUMzdzY0JmVkJwTjVEV3RVRUxadXRWaGhYczhMZTVCOGZaOWhMbjl5dHd2YmY=@208.67.105.87:42501#0107荷兰 
vless://14ba4514-3846-45c0-aec6-444e5451b95c@212.224.93.93:443?flow=&encryption=none&security=tls&sni=blog.codegethub.org&type=ws&host=blog.codegethub.org&path=/ws%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
ss://YWVzLTI1Ni1jZmI6ZjYzZ2c4RXJ1RG5Vcm16NA==@217.30.10.18:9010#0107波兰 
ss://YWVzLTI1Ni1jZmI6TTN0MlpFUWNNR1JXQmpSYQ==@217.30.10.18:9011#0107波兰 
ss://YWVzLTI1Ni1jZmI6R0E5S3plRWd2ZnhOcmdtTQ==@217.30.10.18:9019#0107波兰 
ss://YWVzLTI1Ni1jZmI6QmVqclF2dHU5c3FVZU51Wg==@217.30.10.18:9024#0107波兰 
ss://YWVzLTI1Ni1jZmI6RVhOM1MzZVFwakU3RUp1OA==@217.30.10.18:9027#0107波兰 
ss://YWVzLTI1Ni1jZmI6QndjQVVaazhoVUZBa0RHTg==@217.30.10.18:9031#0107波兰 
ss://YWVzLTI1Ni1jZmI6cDl6NUJWQURIMllGczNNTg==@217.30.10.18:9040#0107波兰 
ss://YWVzLTI1Ni1jZmI6VTZxbllSaGZ5RG1uOHNnbg==@217.30.10.18:9041#0107波兰 
ss://YWVzLTI1Ni1jZmI6UzdLd1V1N3lCeTU4UzNHYQ==@217.30.10.18:9042#0107波兰 
ss://YWVzLTI1Ni1jZmI6Rkc1ZGRMc01QYlY1Q3V0RQ==@217.30.10.18:9050#0107波兰 
ss://YWVzLTI1Ni1jZmI6dWVMWFZrdmg0aGNraEVyUQ==@217.30.10.18:9060#0107波兰 
ss://YWVzLTI1Ni1jZmI6Y3A4cFJTVUF5TGhUZlZXSA==@217.30.10.18:9064#0107波兰 
ss://YWVzLTI1Ni1jZmI6VFBxWDhlZGdiQVVSY0FNYg==@217.30.10.18:9079#0107波兰 
ss://YWVzLTI1Ni1jZmI6YzNOdEhKNXVqVjJ0R0Rmag==@217.30.10.18:9084#0107波兰 
ss://YWVzLTI1Ni1jZmI6ZjhucEtnTnpka3NzMnl0bg==@217.30.10.18:9088#0107波兰 
ss://YWVzLTI1Ni1jZmI6d2ZMQzJ5N3J6WnlDbXV5dA==@217.30.10.18:9093#0107波兰 
ss://YWVzLTI1Ni1jZmI6cnBnYk5uVTlyRERVNGFXWg==@217.30.10.18:9094#0107波兰 
ss://YWVzLTI1Ni1jZmI6VVRKQTU3eXBrMlhLUXBubQ==@217.30.10.18:9033#0107波兰 
ss://YWVzLTI1Ni1jZmI6WkVUNTlMRjZEdkNDOEtWdA==@217.30.10.18:9005#0107波兰 
ss://YWVzLTI1Ni1jZmI6RkFkVXZNSlVxNXZEZ0tFcQ==@217.30.10.18:9006#0107波兰 
ss://YWVzLTI1Ni1jZmI6S25KR2FkM0ZxVHZqcWJhWA==@217.30.10.18:9014#0107波兰 
ss://YWVzLTI1Ni1jZmI6UVdERHZWRTlucE51clFmQQ==@217.30.10.18:9026#0107波兰 
ss://YWVzLTI1Ni1jZmI6ck5CZk51dUFORkNBazdLQg==@217.30.10.18:9056#0107波兰 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@218.234.149.9:2105#0107韩国 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@221.150.109.90:41748#0107韩国 
trojan://vzhXXZVw@223.113.54.149:14505?flow=&security=tls&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.112.236.3:443#0107日本 
trojan://telegram-id-directvpn@3.23.176.13:22222?flow=&security=tls&sni=trojan.burgerip.co.ukhttp/1.1&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.35.206.24:443#0107韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.38.212.48:443#0107韩国 
trojan://telegram-id-directvpn@3.69.59.22:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
trojan://telegram-id-directvpn@3.97.101.244:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107加拿大 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.141.82.165:8848#0107德国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.142.21.211:8848#0107英国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.18.5.163:8848#0107卡塔尔 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.211.229.86:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.213.242.165:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.216.172.180:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.80.203:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.222.132.123:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.222.136.128:443#0107美国 
trojan://telegram-id-privatevpns@34.248.34.7:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107爱尔兰 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@34.58.159.18:8848#0107美国 
trojan://telegram-id-privatevpns@35.179.83.100:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107英国 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.194.227.32:8848#0107台湾 
ss://YWVzLTI1Ni1jZmI6YXNkZjEyMzQ=@35.220.163.233:8848#0107香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.85.33.177:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.85.36.208:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.88.126.102:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.93.31.33:443#0107美国 
trojan://vzhXXZVw@36.150.215.196:18681?flow=&security=tls&sni=36.150.215.196&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107香港 
vless://7c4efc45-42f7-48d8-a741-6093cd2886a7@36.226.244.225:56870?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=9J1xcf0tI7OQ8Z6ULcruIIjsM5AK3nZTXdOK6GIhwmA&sid=239c3cef&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107台湾 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.143.128.195:989#0107智利 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@40.172.155.166:443#0107阿拉伯酋长国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@40.172.156.169:443#0107阿拉伯酋长国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.122.162:443#0107韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.127.152:443#0107韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.206.231.196:443#0107日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://fcf99985-147b-4c71-c3f2-f448e5a379f1@45.63.117.50:443?flow=&encryption=none&security=tls&sni=cpanel3.sassanidempire.com&type=ws&host=cpanel3.sassanidempire.com&path=/ws&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
hysteria2://1f17cdf0578a2860@45.76.0.86:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=4b817757&os=#0107美国 
hysteria2://1f17cdf0578a2860@45.76.0.86:443?insecure=1&sni=45.76.0.86&alpn=&fp=&obfs=salamander&obfs-password=4b817757&os=#0107美国 
hysteria2://1f17cdf0578a2860@45.76.0.86:443?insecure=1&sni=wrmelmwxlf.gktevlrqznwqqozy.fabpfs66gizmnojhcvqxwl.kytrcfzqla87gvgvs6c7kjnrubuh.cc&alpn=&fp=&obfs=salamander&obfs-password=4b817757&os=#0107美国 
hysteria2://1f17cdf0578a2860@45.76.0.86:443?insecure=1&sni=vkvd127.mycdn.me&alpn=&fp=&obfs=salamander&obfs-password=4b817757&os=#0107美国 
hysteria2://dongtaiwang.com@46.17.41.189:50717?insecure=1&sni=www.bing.com&alpn=&fp=&os=#0107俄罗斯 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@46.183.217.232:990#0107拉脱维亚 
vless://4c5f4cf8-b30a-4658-84bb-f0145dd123d4@47.251.95.178:443?flow=&encryption=none&security=tls&sni=high.work.lzg.me&type=ws&host=high.work.lzg.me&path=/4c5f4cf8-b30a-4658-84bb-f0145dd123d4&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMzkuMjUyLjIwNCIsInBvcnQiOjEwODgxLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35b635Zu9IiwibmV0Ijoid3MiLCJpZCI6IjcxZGIxMDZjLTBkMmYtNDczMy04N2NjLWNiYTY1N2IzODdlOSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjUuMzkuMjU0LjE5NiIsInBvcnQiOjIzMTY5LCJzY3kiOiJhdXRvIiwicHMiOiIwMTA36Iux5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjM5OGNlODRlLTQ4NDktNGU1Zi05YjFhLWE1NmZiZTIzM2I4MSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpNN3gxbUdOT3doUGlSQjlqU3haSk55@51.13.182.236:6870#0107挪威 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.194.212.235:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.196.112.58:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.68.44.53:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.69.160.222:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.79.73.137:443#0107韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.89.164.115:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.178.191.236:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.178.84.59:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.179.186.199:443#0107新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.186.92.34:443#0107美国 
trojan://telegram-id-directvpn@54.197.237.130:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.200.223.152:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.201.172.79:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.202.77.81:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.238.219.226:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.245.207.144:443#0107美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.249.152.9:443#0107日本 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.69.180.74:443#0107美国 
vless://a835df0f-6b89-46e1-a2a0-c08907d5a524@57.129.0.208:80?flow=&encryption=none&security=&sni=&type=ws&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#0107德国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@62.100.205.48:989#0107英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpDalJsODE3Q3hYcFZKMGoybmhKUldh@62.210.88.22:443#0107法国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=66.135.11.68&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0107美国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0107美国 
hysteria2://4e9ee29b39a28277@66.135.11.68:443?insecure=1&sni=wrmelmwxlf.gktevlrqznwqqqozy6hgvqxwfmfsvgvs6c7kjnrubuh.cc&alpn=&fp=&obfs=salamander&obfs-password=13f7ba5f&os=#0107美国 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@68.183.227.45:8080#0107新加坡 
hysteria2://18240b2dfdd76484@70.34.207.153:443?insecure=1&sni=70.34.207.153&alpn=&fp=&obfs=salamander&obfs-password=d2648ec2&os=#0107瑞典 
vless://9e316ce0-8fd3-4058-bc5e-241f9c3a9f56@78.157.59.140:50067?flow=&encryption=none&security=&sni=MgbJP.divarcdn.com%2CLXHRl.snappfood.ir%2C3cubP.yjc.ir%2CXbifM.digikala.com%2CHL56Q.tic.ir&type=ws&host=MgbJP.divarcdn.com%2CLXHRl.snappfood.ir%2C3cubP.yjc.ir%2CXbifM.digikala.com%2CHL56Q.tic.ir&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@8.218.120.79:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vless://14ba4514-3846-45c0-aec6-444e5451b95c@8.219.241.41:443?flow=&encryption=none&security=tls&sni=blog.codegethub.org&type=ws&host=blog.codegethub.org&path=/ws%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel----%40PersiaTM_Channel&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107德国 
vless://3b9bc773-05eb-4d5f-8c1f-57342c0c4f40@8.222.158.140:443?flow=&encryption=none&security=tls&sni=147135010103.sec19org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyMTU4NmFhYi0zYTM3LTRmNTUtYjhiNy01YWU2OTU3MmQ0MDM=@85.133.241.75:1935#0107土耳其 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTowZ29hdGpsR21LZUt0OUVuNnZmc0pG@89.185.85.227:19262#0107荷兰 
ss://YWVzLTI1Ni1nY206SVk4UDJPN1hJUVpWTDlKRQ==@8tv68qhq.slashdevslashnetslashtun.net:17001#0107美国 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@Cmc5.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc5.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107越南 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@aisalayer-a.upperlay.xyz:568#0107新加坡 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@aisalayer-b.upperlay.xyz:571#0107新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@api.namasha.co:443#0107阿拉伯酋长国 
vmess://eyJ2IjoiMiIsImFkZCI6ImNtMS5hd3NsY24uaW5mbyIsInBvcnQiOjI1MjMwLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35L+E572X5pavIiwibmV0Ijoid3MiLCJpZCI6IjI0M2VhYjUyLTlhYzEtNDA1Yy04ODdjLWViMTEyYzA5ODViOCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiY20xLmF3c2xjbi5pbmZvIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJjbTEuYXdzbGNuLmluZm8iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@cmc5.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc5.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107越南 
trojan://34ec6bdf-602c-4bbe-933a-5c0823524201@cmc6.5gsieuvip.vn:443?flow=&security=tls&sni=Cmc6.5gsieuvip.vn&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107越南 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@cminit.exitlag.xyz:566#0107香港 
vmess://eyJ2IjoiMiIsImFkZCI6ImlydmlkZW8uY2ZkIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35rOV5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImU1MzdmMmY1LTJhMGMtNGY1OS05MmM5LTgzMmNhNjQzM2JmMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiaXJ2aWRlby5jZmQiLCJwYXRoIjoiL2xpbmt3cyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImlydmlkZW8uY2ZkIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@neweur.upperlay.xyz:630#0107俄罗斯 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p230.panda004.net:41748#0107韩国 
vless://d7a6f3c2-5c25-46d9-bf7d-2b0e8cf1703d@phx-plus-1ddns.faforex.eu.org:18443?flow=&encryption=none&security=reality&sni=www.tesla.com&type=tcp&host=&path=&headerType=none&alpn=&fp=edge&pbk=8233FxCRw1a_aCJ8d1HwHBMD_fABUNNW7rsrFe3vK0s&sid=e6658462&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107美国 
vmess://eyJ2IjoiMiIsImFkZCI6InByaW1lci5pYmlsaWJpLmxpIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMTA35rOV5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImU1ODUyMzkzLWNhNTItNGM5MC1hMjM3LWQ2M2NiYmI1N2YyMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoibG9raS5vcmFjbGUiLCJwYXRoIjoiL2ZhcmNyeT9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYW1lYmxvLmpwIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1nY206VTVHQVFNTUlGUTJGRDQ0QQ==@qh62onjn.slashdevslashnetslashtun.net:18003#0107日本 
ss://YWVzLTI1Ni1nY206VzZMMlo1Q09XRjRUR0M4Uw==@qh62onjn.slashdevslashnetslashtun.net:16015#0107新加坡 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpCb2cwRUxtTU05RFN4RGRR@series-a2-me.varzesh360.co:443#0107巴林 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp1MTdUM0J2cFlhYWl1VzJj@series-a2-mec.varzesh360.co:443#0107阿拉伯酋长国 
ssr://c3NjYS5pcnVuZG5zLm5ldDo0NDM6YXV0aF9hZXMxMjhfbWQ1OmFlcy0xMjgtY2ZiOmh0dHBfcG9zdDpKQ1JVZFhKaU1GWlFUaVFrLz9vYmZzcGFyYW09JnByb3RvcGFyYW09JnJlbWFya3M9TURFd04rV0tvT2FMditXa3B3PT0mb3M9 
trojan://94d219c9-1afc-4d42-b090-8b3794764380@std1.loadingip.com:443?flow=&security=tls&sni=std1.loadingip.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0107越南 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:574#0107美国 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:573#0107美国 
ss://YWVzLTEyOC1nY206ODg0MzA2MDctZjA4MC00ODE2LWIyZTUtMWE0N2UxOTNhMDU3@usastart-a.upperlay.xyz:571#0107美国 

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
