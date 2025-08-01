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

vmess://eyJ2IjoiMiIsImFkZCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzMywic2N5IjoiYXV0byIsInBzIjoiMDczMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6InYzMy5oZWR1aWFuLmxpbmsiLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjpmYWxzZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InY1LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA1LCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx5oSP5aSn5YipIiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoidjUuaGVkdWlhbi5saW5rIiwicGF0aCI6Ii9vb29vIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731斯洛文尼亚共和国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731波兰 
vless://401374e6-df77-41fb-f638-dad8184f175b@94.247.142.103:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@141.11.203.139:443?flow=&encryption=none&security=tls&sni=pqh23v5.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vless://401374e6-df77-41fb-f638-dad8184f175b@103.133.1.227:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xMTYuNy4yNDEiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjI0OGJlNTJiLTM1ZDktMzRjYi05YjczLWUxMmI3OGJjMTMwMSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InY0LmhlZHVpYW4ubGluayIsInBvcnQiOjMwODA0LCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNiYjNmODc3LWQxZmItMzQ0Yy04N2E5LWQxNTNiZmZkNTQ4NCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0Ijoib2NiYy5jb20iLCJwYXRoIjoiL29vb28iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1nY206aVVCMDkyM1JCQQ==@154.3.8.151:30067?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731香港 
vmess://eyJ2IjoiMiIsImFkZCI6ImNzZ28uY29tIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiOTVjMjdjYzQtODJiNS00NWRhLTk2MmUtYmE2NzU2NDJmYzNkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJjZG4tbm9kZS1vc3MtOTkucGFvZnUuZGUiLCJwYXRoIjoiL3Byb2ZpbGUvdGVsZWdyYW1Ac3Nyc3ViIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiY2RuLW5vZGUtb3NzLTk5LnBhb2Z1LmRlIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yNDAuMTc5LjkxIiwicG9ydCI6NDg4MzMsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHpppnmuK8iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6NjQsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://401374e6-df77-41fb-f638-dad8184f175b@156.238.19.95:443?flow=&encryption=none&security=tls&sni=pqh24v3.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4yMjEuMTYwLjM3IiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDczMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiIxNzEwMmIxOS1kZWRjLTNkNWUtODIzOC00MDU4MTRhZDI4N2IiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnM0LmNuLWRiLnRvcCIsInBhdGgiOiIvZGFiYWkmVGVsZWdyYW3wn4eo8J+Hs0BXYW5nQ2FpMi8/ZWQ9MjU2MCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IlRHLldhbmdDYWkyLnM0LmNuLWRiLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://06e4425e-a8cb-4b63-929f-2105604ab0a9@time.is:443?flow=&encryption=none&security=tls&sni=ax.ylka.dpdns.org&type=ws&host=ax.ylka.dpdns.org&path=/%3Fed%3D2560%26PROT_TYPE%3Dvless&headerType=none&alpn=&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vmess://eyJ2IjoiMiIsImFkZCI6Ind3d2UzLjExODkwNjA0Lnh5eiIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjUxMmQ5Njc0LWRiMTItNDRjYS1hMWI1LTY1NDI0NDU0OWI2NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0Ijoid3d3ZTMuMTE4OTA2MDQueHl6IiwicGF0aCI6Ii91aUF4dkg2T2tWazBWQ2ZhN2RYM0pJcllrN3ptIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoid3d3ZTMuMTE4OTA2MDQueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6Ik9Pb09PT29vT3AuMjIyNzY5LlhZWiIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImNlOTIxMzg1LTJiMzEtNDVmZS04NGM1LTE4NDNlOGFlODQ1YiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiT09vT09Pb29PcC4yMjI3NjkuWFlaIiwicGF0aCI6Ii9WYWFTRWZOTEhkVzNJOThkeExrZXoiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJPT29PT09vb09wLjIyMjc2OS5YWVoiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IkVlRURDRlZnLjk5OTgyNC54WVoiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMDczMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjZGVjOWQ1Ny02NjFkLTQ1NmEtYmJmMi1iNGMzOGU5YzY3MTEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImVlZWRjZnZnLjk5OTgyNC54eXoiLCJwYXRoIjoiLzlkWmxKTGpISHJMMFZ3U29sYnFGcGciLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJlZWVkY2Z2Zy45OTk4MjQueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IlNTU3hYY3ZGdFkuNDQ0NzUyLlh5eiIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjUxMmQ5Njc0LWRiMTItNDRjYS1hMWI1LTY1NDI0NDU0OWI2NSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiU1NTeFhjdkZ0WS40NDQ3NTIuWHl6IiwicGF0aCI6Ii91aUF4dkg2T2tWazBWQ2ZhN2RYM0pJcllrN3ptIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNDE3NGI5NWQtMTE1ZS00ZDM5LWFkZDYtMWY4ZGI5NWJiODYwIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJzc3Nzc3NzeHh4eC4yMDMyLnBwLnVhIiwicGF0aCI6Ii82V2UzVTlEZjFXR3hnRm5vRlB3MSIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6InNzc3Nzc3N4eHh4LjIwMzIucHAudWEiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InJycnJycnJycnQuMTE4OTA2MDQueHl6IiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImY4OThmZmNiLTY0MTctNDM3My05NjQwLTBiNjYwOTFlODIwNiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoicnJycnJycnJydC4xMTg5MDYwNC54eXoiLCJwYXRoIjoiL0duSjNiQnhWOTF1RmtZdHV6WHlKNVhOZUgxUjEiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJycnJycnJycnJ0LjExODkwNjA0Lnh5eiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://401374e6-df77-41fb-f638-dad8184f175b@all.tellmethetrue.shop:443?flow=&encryption=none&security=tls&sni=pqh29v1.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vless://ffcf7ec1-3e09-4821-b3d9-b426a107b73b@172.67.157.220:443?flow=&encryption=none&security=tls&sni=XXCsDERT6.777159.XyZ&type=ws&host=xxcsdert6.777159.xyz&path=/O9jlBCbIm3xr1D40NK&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vless://357b1bba-6400-4944-baff-1b933311ff28@162.159.129.11:443?flow=&encryption=none&security=tls&sni=SsSSSSSsSSSD.890606.Xyz&type=ws&host=SsSSSSSsSSSD.890606.Xyz&path=/kSIHD28dr9nkaMBYIsgt&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vless://6f6e8f09-c1b3-48fd-ab00-18f921d875ef@104.21.36.57:443?flow=&encryption=none&security=tls&sni=profit.fullmargintraders.com&type=ws&host=profit.fullmargintraders.com&path=/wsv/6f6e8f09-c1b3-48fd-ab00-18f921d875ef&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://db400287-fb42-441d-8a76-5624a8a96f49@172.67.66.177:443?flow=&encryption=none&security=tls&sni=rayan-roof.atena.dpdns.org&type=ws&host=rayan-roof.atena.dpdns.org&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731亚美尼亚 
vless://288124da-0d68-42f4-9f48-70dc4dcc55a6@172.67.175.139:443?flow=&encryption=none&security=tls&sni=999O0.859886.xyz&type=ws&host=999o0.859886.xyz&path=/e49RZLgIb0TdfgF5HdHEIupMZeK&headerType=none&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731加拿大 
trojan://f108e0e2-5f12-42b6-9e67-1b2f073ffb2b@172.67.219.196:443?flow=&security=tls&sni=CCcvfgt6.852224.dpdns.org&type=ws&header=none&host=CCcvfgt6.852224.dpdns.org&path=/CA5bMmr2JMum8sDKRwvFCJq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
trojan://288124da-0d68-42f4-9f48-70dc4dcc55a6@172.67.200.11:443?flow=&security=tls&sni=rRfGty6.890606.XYz&type=ws&header=none&host=rRfGty6.890606.XYz&path=/raChT39pjLFYRA5HdHEIupMZeK&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731加拿大 
vmess://eyJ2IjoiMiIsImFkZCI6Ind3dy52aXNhLmNvbS5zZyIsInBvcnQiOjg0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiNjJhMDBlZGMtOTg2Ny00YzY2LTgyZWUtZDU3YzE5ZmFjYWQzIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJudXJzZS1ib3N0b24tcXVlZW4tcm9tYW50aWMudHJ5Y2xvdWRmbGFyZS5jb20iLCJwYXRoIjoiLyIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6Im51cnNlLWJvc3Rvbi1xdWVlbi1yb21hbnRpYy50cnljbG91ZGZsYXJlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjkyLjUzLjE5MS4yNyIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNTVmODdkZmYtYTUzMy0zODU2LWI2ZjAtN2QwNTc0NzRhZmE5IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJURy5XYW5nQ2FpMi5zNC5jbi1kYi50b3AiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjE5OS4zNC4yMzAuNyIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMmQ4NmJmMDktMDgxMC0zYzI5LWE3NGMtYmE3MTUwODQ4Y2ZmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zNC5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJURy5XYW5nQ2FpMi5zNC5jbi1kYi50b3AiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImNjMmRhc2guODkwNjAwMDQueHl6IiwicG9ydCI6MjA5Niwic2N5IjoiYXV0byIsInBzIjoiMDczMeWKoOaLv+WkpyIsIm5ldCI6IndzIiwiaWQiOiIyZmMzNzcxMy0zMDE3LTQ5N2UtZmYyZC05NjVmODI2YTE5YTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNjMmQxLjg5MDYwMDA0Lnh5eiIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IkpKSmpqampqbU1NbU0uNDQ0NDkyNi5YWVoiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiZGM1MGViMWQtMjQ0ZC00NzExLWIxNjgtYTEwMWE1ZTZmYjFiIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJKSkpqampqam1NTW1NLjQ0NDQ5MjYuWFlaIiwicGF0aCI6Ii9hd21xcTc5QjE3cmZucFhpTmFXYiIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@192.71.166.100:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731希腊 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.213.23.226:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731挪威 
vmess://eyJ2IjoiMiIsImFkZCI6IjIxMC44Ny4xMTEuMjQxIiwicG9ydCI6MjA1MjEsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHmlrDliqDlnaEiLCJuZXQiOiJ3cyIsImlkIjoiOTBjMjQzNjUtOGY2ZC00OWQ3LTlmMWEtNmYxZDM2MWM4MzE1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIyMTAuODcuMTExLjI0MSIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6InYzNS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzNSwic2N5IjoiYXV0byIsInBzIjoiMDczMea+s+Wkp+WIqeS6miIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6ImgzcWE1LWcwNi5qcDA0LTM3NzEtdm0wLmVudHJ5LmZyMDMwN2EuYXJ0IiwicG9ydCI6NDQ5LCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx5pel5pysIiwibmV0IjoidGNwIiwiaWQiOiIyMjc4MTQ2Yy04ZmIwLTM2ODMtODMwMC0zNDIyMzhmOGE5ZDAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjEsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImhrdC5nb3RvY2hpbmF0b3duLm5ldCIsInBvcnQiOjgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx6aaZ5rivIiwibmV0Ijoid3MiLCJpZCI6IjliNjA0MTk0LTE3YjctMTFlZi04MGIwLWYyM2M5MTNjOGQyYiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MiwidHlwZSI6Im5vbmUiLCJob3N0IjoiYnJvYWRjYXN0bHYuY2hhdC5iaWxpYmlsaS5jb20iLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOmZhbHNlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYyNC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgyNCwic2N5IjoiYXV0byIsInBzIjoiMDczMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p222.panda001.net:15098?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731韩国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjIwMi4zMC4yNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiM2UxZTNlN2YtMjY4My0zZjM2LTgzYjEtMTg1MDc5MDI5NWRmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ2LjI1NC45Mi4yNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiM2UxZTNlN2YtMjY4My0zZjM2LTgzYjEtMTg1MDc5MDI5NWRmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImFiYy50aGV5eXN6bW4uc2JzIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0IjoidGNwIiwiaWQiOiIzZDg0YTY2OC0wNTg4LTQ0N2ItZmJlMS0wNThkZWI1YmFmOTMiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://401374e6-df77-41fb-f638-dad8184f175b@92.53.188.36:443?flow=&encryption=none&security=tls&sni=pqh23v4.hiddendom.shop&type=grpc&host=&serviceName=&mode=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731美国 
vmess://eyJ2IjoiMiIsImFkZCI6InYzOS5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgzOSwic2N5IjoiYXV0byIsInBzIjoiMDczMeaWsOWKoOWdoSIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xNjkuMTQyLjI0MSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMjQ4YmU1MmItMzVkOS0zNGNiLTliNzMtZTEyYjc4YmMxMzAxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwMy4xNjAuMjA0LjI0MSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMjQ4YmU1MmItMzVkOS0zNGNiLTliNzMtZTEyYjc4YmMxMzAxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0OS4xMi4yNSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiM2UxZTNlN2YtMjY4My0zZjM2LTgzYjEtMTg1MDc5MDI5NWRmIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5jbi1kYi50b3AiLCJwYXRoIjoiL2RhYmFpJlRlbGVncmFt8J+HqPCfh7NAV2FuZ0NhaTIvP2VkPTI1NjAiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMC5oZWR1aWFuLmxpbmsiLCJwb3J0IjozMDgwNywic2N5IjoiYXV0byIsInBzIjoiMDczMemmmea4ryIsIm5ldCI6IndzIiwiaWQiOiJjYmIzZjg3Ny1kMWZiLTM0NGMtODdhOS1kMTUzYmZmZDU0ODQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjIsInR5cGUiOiJub25lIiwiaG9zdCI6ImJhaWR1LmNvbSIsInBhdGgiOiIvb29vbyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjIwNS4yMzMuMTgxLjI0MSIsInBvcnQiOjg4ODAsInNjeSI6ImF1dG8iLCJwcyI6IjA3MzHnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMjQ4YmU1MmItMzVkOS0zNGNiLTliNzMtZTEyYjc4YmMxMzAxIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJURy5XYW5nQ2FpMi5zMi5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo3OTA1YTMyYi0wMTJjLTQ3MTEtODllMi03M2I2NzEzZWNhNzU=@pr.fastsoonlink.com:40030?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731波兰 
vless://170ba974-6ae5-44ae-dfdc-4675b5643f34@79.137.33.139:16390?flow=&encryption=none&security=&sni=&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731法国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE0LjEwMi4yMjguMTcyIiwicG9ydCI6ODg4MCwic2N5IjoiYXV0byIsInBzIjoiMDczMee+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI3MGRmN2MxZS0xMmM4LTMyNWYtYTEyYS0zNGFhNDY5NDllNjAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IlRHLldhbmdDYWkyLnM0LmNuLWRiLnRvcCIsInBhdGgiOiIvZGFiYWkmVGVsZWdyYW3wn4eo8J+Hs0BXYW5nQ2FpMi8/ZWQ9MjU2MCIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6cXdlclJFV1FAQA==@p141.panda001.net:4652?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731韩国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#0731摩尔多瓦 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE1OS4yMTcuMjUiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjNlMWUzZTdmLTI2ODMtM2YzNi04M2IxLTE4NTA3OTAyOTVkZiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuY24tZGIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE1OS4yMTYuMjUiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjNlMWUzZTdmLTI2ODMtM2YzNi04M2IxLTE4NTA3OTAyOTVkZiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuY24tZGIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjYzLjE0MS4xMjguMjUiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwNzMx576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjNlMWUzZTdmLTI2ODMtM2YzNi04M2IxLTE4NTA3OTAyOTVkZiIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiVEcuV2FuZ0NhaTIuczIuY24tZGIudG9wIiwicGF0aCI6Ii9kYWJhaSZUZWxlZ3JhbfCfh6jwn4ezQFdhbmdDYWkyLz9lZD0yNTYwIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.19.179.173:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
hysteria2://t1w5935QJh5zMSne0BoOgypqmY@45.82.121.146:14405?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=EfmpbzBeh0bqdy7FezTAj1cTHLFk7ouVRaE&mport=&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@190.93.246.230:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@162.159.245.40:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.49.54:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
anytls://AhA4pDy0Dol7zicCO7fvoCYY6alu2FM00@45.82.121.146:59303?insecure=1&sni=cm1.awslcn.info&alpn=h2&fp=&os=#0731德国 
trojan://3cc172e6-ceb9-4781-9fad-ded68e73cf2d@45.82.121.146:38917?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/RVEHqpJvODwDqv4feOmDMsYcRyb9%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
trojan://a1f79978-6d02-450a-9070-3de3212855ed@45.82.121.146:40101?flow=&security=tls&sni=cm1.awslcn.info&type=ws&header=none&host=cm1.awslcn.info&path=/0tvIcahl%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
hysteria2://L8HTvkRlq8rVbn293Z5y8uQ@45.82.121.146:50233?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=iUd5LVGlSPU3rfJrLE6wdoP7jGh5siwHM&mport=&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@188.114.99.92:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.58.3:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@190.93.246.121:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@108.162.196.116:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@103.21.244.115:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://dbe41a05-ce75-4d00-baa5-344226b3ed36@45.82.121.146:53386?flow=&encryption=none&security=tls&sni=cm1.awslcn.info&type=ws&host=cm1.awslcn.info&path=/E1MiYyyhXQg%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
hysteria2://GGuTaEMyLNVdbp93nOh8EpMPRxZOJurCoQ24a@45.82.121.146:61727?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=D5BAyaCDNMJlw0eqdZKKkEFgfI6juyxrpU&mport=&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@108.162.192.139:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.18.154.3:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
hysteria2://D6NKoWnCjOJZ4lgsX@45.82.121.146:42600?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=WVegMtgTXcKfKwnIqj&mport=&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.58.4:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.25.154.175:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
hysteria2://HzYG2VEjIcj4qgQYrnFWyQQ@45.82.121.146:30220?insecure=1&sni=cm1.awslcn.info&alpn=&fp=&obfs=salamander&obfs-password=FeYP1mdG2u1qfzPQwRLGBuI&mport=&os=#0731德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xNDYiLCJwb3J0Ijo1MTM1OSwic2N5IjoiYXV0byIsInBzIjoiMDczMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJjMzE5NGViYi1hYjg4LTQ5NzMtOGVkMS03YjZjMTRhNDI2ZTAiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImNtMS5hd3NsY24uaW5mbyIsInBhdGgiOiIvUz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiY20xLmF3c2xjbi5pbmZvIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@172.67.6.178:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.23.126.38:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.58.130:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.19.254.193:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@173.245.59.32:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@103.21.244.223:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@172.66.216.95:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@104.18.230.96:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 
vless://9f71ab9b-6d2a-454f-b33b-00616222cbc1@141.101.120.45:443?flow=&encryption=none&security=tls&sni=cuqa.34892.qzz.io&type=xhttp&host=cuqa.34892.qzz.io&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0731德国 


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
