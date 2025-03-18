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
trojan://Fl4B9jyFAwE4XgFxuICw8pD0NCYIneA22OyYO30enl8Kxe3a3xcpDEyqa79CTNSpRA5D8@young.golfland.club:443?flow=&security=tls&sni=young.golfland.club&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317英国 
ss://YWVzLTI1Ni1nY206RjdYR0dOOU1QMERHUExJSQ==@w72tapyb.slashdevslashnetslashtun.net:21007#0317台湾 
trojan://a38c9e28-9960-4e31-9f18-ed2495a756aa@vt-bana2-cn-11.ghpgwqswodgzv.com:40021?flow=&security=tls&sni=vt-bana2-cn-11.ghpgwqswodgzv.com&type=ws&header=none&host=vt-bana2-cn-11.ghpgwqswodgzv.com&path=/dl_media&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317香港 
vmess://eyJ2IjoiMiIsImFkZCI6InZjLmZseS5kZXYiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfpppnmuK8iLCJuZXQiOiJ3cyIsImlkIjoiMzUzNzkyMTktNjUzNS00ZjJlLWE0ZmUtM2U0NGY2MWUwZWVlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjozMiwidHlwZSI6Im5vbmUiLCJob3N0IjoidmMuZmx5LmRldiIsInBhdGgiOiIvdmMiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://F7aCRp5cSNRqynagAa8IaX09TFRycpxllaXZeYzzpDeOa3CpXwwCS9awB7BNNeaqYY8aY9ASz8pZAZS@tubular.wireshop.net:443?flow=&security=tls&sni=tubular.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
ss://YWVzLTI1Ni1nY206UkFLTDVaRzRRTkZBNzJWWA==@ti3hyra4.slashdevslashnetslashtun.net:18007#0317日本 
ss://YWVzLTI1Ni1nY206ODRITVJBV0lMS0I0OVFVWg==@ti3hyra4.slashdevslashnetslashtun.net:18002#0317日本 
ss://YWVzLTI1Ni1nY206S0cxOENWNkhXUjdDWFdQNg==@ti3hyra4.slashdevslashnetslashtun.net:18001#0317日本 
ss://YWVzLTI1Ni1nY206QkZZQ09LSFRDOEhJV1dSQg==@ti3hyra4.slashdevslashnetslashtun.net:16006#0317新加坡 
ss://YWVzLTI1Ni1nY206UkJOMVVOR1ZQRjFCUVhQSw==@ti3hyra4.slashdevslashnetslashtun.net:15006#0317香港 
trojan://CAlpl3ZOpDFaS9E6Se0plFxu2x3I4eACOcqZSaY3ReS6CjZSCTNKDgEF73TDZ2aB9D3nD@soldier.homeofbrave.net:443?flow=&security=tls&sni=soldier.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://7pE3OSjFe9xFey8YyCgaIaz3Zu2CORpananc34DRlgSyO83XTyNjC4xAIue30YKFCCDlx@sohtsa.taiwanesefood.link:443?flow=&security=tls&sni=sohtsa.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317台湾 
ss://YWVzLTI1Ni1nY206SllRNTBHWExLVjJGNlpYVA==@qh62onjn.slashdevslashnetslashtun.net:15015#0317香港 
trojan://Yyjyl3Fwy6pSjTYSaCxg7Z0COIwBYxN38FwC3YBz44678OAypA87p2CEe53SaKel3pCDSZCZaeSaaZS@printer.wireshop.net:28335?flow=&security=tls&sni=printer.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://6qREZzexS5BDqFaSyzlwlBYXT8CDYOpcDIaeYaAC3X940A73OceAaRR32C3Sx6w9xgyCS@phooey.taiwanesefood.link:443?flow=&security=tls&sni=phooey.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://AYA7NTRlglF7qI9qF83a33aZugxSl34OSDcCZDSepF5eOK8OSlACCnxX9ZxBpzBD8T26w@pevoy.protocolbuffer.com:28337?flow=&security=tls&sni=pevoy.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317新加坡 
ss://YWVzLTI1Ni1nY206OWFjZmM1NzQtYWNjMy00YzJiLWFiM2ItNDkxZDQzYTZlYjgz@okanc.node-is.green:21115#0317新加坡 
trojan://OCxO7za3SXnwpEacKD7AZxujyISD840CZgSCSFFp6Z3eXFeOZDyzlTy3lA8AgBea3SDEC@luber.protocolbuffer.com:443?flow=&security=tls&sni=luber.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317新加坡 
trojan://jnaO0CFYpYExOygqlESRplzewIaKSFpBaqXy3YX4xBC8KK9ja94Y4S8aS7zjq96XSxO7CDu5BCYFCZg@lnitak.starspace.link:443?flow=&security=tls&sni=lnitak.starspace.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
vmess://eyJ2IjoiMiIsImFkZCI6ImxhMDIuODE4MTg1Llh5WiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6ImxBMDEuODE4MTg1Lnh5WiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://p0axgx3pXT6yjp4SwSRaaYeCDxCFOFaAlRYDNaRjF8OycXn3ZE3ABaYgnDIx3Eeq9C0ce@huzzah.meijireform.com:443?flow=&security=tls&sni=huzzah.meijireform.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317日本 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk02.x.quickcht3.club:52612#0317香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyYmUwYzk1NC00MjkxLTQ1ZWEtYjQ3ZC1jYTcxMzE4MDU1MGI=@hk01.x.quickcht3.club:52611#0317香港 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@gafntaipei.duckdns.org:36019?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0317台湾 
vmess://eyJ2IjoiMiIsImFkZCI6ImR4djQucGFpNTAyODgudWsiLCJwb3J0IjoxNDEwMCwic2N5IjoiYXV0byIsInBzIjoiMDMxN+iLseWbvSIsIm5ldCI6InRjcCIsImlkIjoiZjY4NjZiMGItZjk0Ni00YTAzLThkZjAtYzdlMDAxNmI1NWFkIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
trojan://SZAaY0CIRDey6OCSpS3Dl3F2nnDTYFqRS8aClceOwAyTwy39XxDz4FYXZO3AxRaEz2SlN@dessert.taiwanesefood.link:443?flow=&security=tls&sni=dessert.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://9FC33glcaEeYYTnOqOS9DOZgBZ5CDazy33SCS2j4Cz36A7AIN88uaKRx5xDyR8pxu3x4D@closet.homeofbrave.net:28332?flow=&security=tls&sni=closet.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://RXO4SlDD8qRKaxz3cBgSa3AXZuFnpu3Ce3KZFAN3YCxC7EEj2lTRN4Y6FyOcBp50IzD3D@bottling.coffeekit.net:443?flow=&security=tls&sni=bottling.coffeekit.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317法国 
trojan://2OnySp6YC3SZcF32XACEjlD5aDOqx9SeR6yRFDwEXAu3Fc8w3Z3Y4AqZ0OSzlN8NCeYIA@bathtub.homeofbrave.net:28333?flow=&security=tls&sni=bathtub.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://ZI3OeTA9Clx3AFS78DejwENjaZAa3FSwSluxY3EOClyycDqyzpYD0a6DI2eS28q7X3NpC@aluminum.wireshop.net:28334?flow=&security=tls&sni=aluminum.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
vmess://eyJ2IjoiMiIsImFkZCI6IkxhMDEuODE4MTg1LlhZWiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vmess://eyJ2IjoiMiIsImFkZCI6IkxBMDQuODkwNjAzLlhZeiIsInBvcnQiOjQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxN+e+juWbvSIsIm5ldCI6IndzIiwiaWQiOiI2MGNkZDg5ZS1hOWNmLTQ4NTAtODU3Ny1lM2M2YWJmNTUxNWQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImxhMDQuODkwNjAzLnh5eiIsInBhdGgiOiIvZ3lDVk9SZmpvWFl5SEhjSkJ1TGQiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1nY206WjJHQjRPMVI0UklWRFZGMg==@91.148.135.48:20039#0317塞浦路斯 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@91.132.94.200:989#0317斯洛文尼亚共和国 
ss://YWVzLTI1Ni1nY206UUYzNzdHR1EwMFJBVENNSw==@8tv68qhq.slashdevslashnetslashtun.net:21004#0317台湾 
ss://YWVzLTI1Ni1nY206WU1CM1FMODVMN0YxS0pSNw==@8tv68qhq.slashdevslashnetslashtun.net:18013#0317日本 
ss://YWVzLTI1Ni1nY206SUhXTFlaU1NTWDRHU0tMQQ==@8tv68qhq.slashdevslashnetslashtun.net:16013#0317新加坡 
ss://YWVzLTI1Ni1nY206TFpRMFI5Qkw2OUdDQzZGUw==@8tv68qhq.slashdevslashnetslashtun.net:15005#0317香港 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp3MkhkWm5HYjVpYmg=@89.221.225.88:443#0317摩尔多瓦 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@84.17.53.160:989#0317瑞士 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTptQ2Vvc1JhY3NnRlJ0bkpQcTN6Y3Rx@77.83.246.74:443#0317波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjY1LjEwOS4xNzkuMTEzIiwicG9ydCI6MjA4OCwic2N5IjoiYXV0byIsInBzIjoiMDMxN+iKrOWFsCIsIm5ldCI6InRjcCIsImlkIjoiMTk0YzBkMmYtOTMwNy00YTNmLWIyMjctNTE2MzlkZDEzYWRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoiaHR0cCIsImhvc3QiOiJ6dWxhLmlyIiwicGF0aCI6Ii8iLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.218.61.43:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.202.63.169:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.184.74.88:443#0317美国 
trojan://N5T0K3aYpYFSO4O3gnD73OcFwp6BCqCyCa3jlIxDXyZRDE282ljCASADaTN4CzZZYllFI@54.179.175.19:18333?flow=&security=tls&sni=pricing.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.151.230.240:443#0317新加坡 
vless://0a44145f-59dc-4e5b-a233-677b97f5114c@51.81.18.62:443?flow=&encryption=none&security=tls&sni=147135011033.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
ss://YWVzLTI1Ni1nY206VkNSNkhOOFVMVTRTNE4yNw==@45.154.207.246:20030#0317加拿大 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjE0NC40OC4xMjgiLCJwb3J0Ijo4NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE35rOi5YWwIiwibmV0Ijoid3MiLCJpZCI6ImE0ODUwNDgxLTliOTUtNDMwZi05YjJkLTE5MmQyNDEwYjRmNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii92bWVzcy8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
trojan://p0axgx3pXT6yjp4SwSRaaYeCDxCFOFaAlRYDNaRjF8OycXn3ZE3ABaYgnDIx3Eeq9C0ce@43.206.220.255:443?flow=&security=tls&sni=huzzah.meijireform.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317日本 
vmess://eyJ2IjoiMiIsImFkZCI6IjNoLXBvbGFuZDEuMDl2cG4uY29tIiwicG9ydCI6ODQ0Mywic2N5IjoiYXV0byIsInBzIjoiMDMxN+azouWFsCIsIm5ldCI6IndzIiwiaWQiOiJhNDg1MDQ4MS05Yjk1LTQzMGYtOWIyZC0xOTJkMjQxMGI0ZjQiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvdm1lc3MvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@37.235.49.152:989#0317以色列 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.91.216.191:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@35.86.111.233:443#0317美国 
trojan://telegram-id-privatevpns@35.176.148.28:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317英国 
trojan://telegram-id-directvpn@35.158.198.221:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.221.169.63:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.219.71.252:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.211.230.161:443#0317美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.210.253.95:443#0317美国 
vless://e657e5fb-c417-4d3f-d84e-a3a8f010f9fa@31.59.111.49:33718?flow=xtls-rprx-vision&encryption=none&security=reality&sni=icloud.cdn-apple.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=g1f1wLjim5gOVGnI5LGUV0dL4iFXPoiepOPZfSxJe14&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo2MjBjNWI1MTA4MTIwYTcy@23.162.56.206:11201#0317加拿大 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@23.132.228.217:20118?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0317美国 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@212.115.124.224:57194?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0317德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjIwNy45MC4yMzguMTM2IiwicG9ydCI6MjAwMTAsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiMzRhN2QwY2QtYjBiYS00NDBkLWFiNzgtODA0Nzc1MzAzYTExIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206NTVOMDlOQ1hXRUg3R1FNRg==@206.245.211.25:19015#0317英国 
ss://YWVzLTI1Ni1nY206RThDTTNSM0JXWFFRTllNTQ==@206.245.211.22:19012#0317英国 
ss://YWVzLTI1Ni1nY206MU1EN1kxSEU4RkZIQUIwTg==@206.245.211.18:19008#0317英国 
ss://YWVzLTI1Ni1nY206UkhQU0pTRUZMSEdPV0NCNg==@206.245.211.14:19004#0317英国 
ss://YWVzLTI1Ni1nY206RlMzN0Y2MUdCQUlYSkY2RQ==@206.245.211.13:19003#0317英国 
ss://Y2hhY2hhMjAtaWV0Zjphc2QxMjM0NTY=@202.162.109.169:8388#0317新加坡 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@192.9.236.144:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://576c81b6-4976-4fe3-b1a9-05a9c302e98e@192.3.130.103:443?flow=&security=tls&sni=us10-01.iran2030.ggff.net&type=grpc&mode=none&host=&serviceName=i8oL7PsxV002zYFTmiIeg&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.231.233.112:989#0317波兰 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4NS4yMi4xNTIuMjM2IiwicG9ydCI6MjMwMTcsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfkv4TnvZfmlq8iLCJuZXQiOiJ3cyIsImlkIjoiNmM5ODdhZjUtNmNmZS00YzJjLTk1OGUtYWFhYjIxYjRmMTRlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiLyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206OUQ1STI2VEU4NVNQOTI4Vw==@185.213.22.93:20026#0317加拿大 
ss://YWVzLTI1Ni1nY206OUYyRzJFUDhFVDFQTDZRNQ==@185.213.20.36:20029#0317加拿大 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.186.79.53:989#0317丹麦 
ss://YWVzLTI1Ni1nY206UFJDVUo4SU5QTjlLWlc3Mg==@185.186.78.220:20035#0317加拿大 
ss://YWVzLTEyOC1jZmI6c2hhZG93c29ja3M=@184.170.241.194:443#0317美国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzgiLCJwb3J0Ijo1MzkwMiwic2N5IjoiYXV0byIsInBzIjoiMDMxN+aWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.236.137.219:443#0317美国 
trojan://8jqRgpyc5lEe34TzC9A8DuFD23aS3ZyCleIFuCxp3xOYnZRCeA3Oc3yCga8C2DKYBDaRp@18.142.45.201:443?flow=&security=tls&sni=mention.protocolbuffer.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.138.125:443#0317新加坡 
trojan://telegram-id-directvpn@18.130.57.147:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317英国 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Ni4zMi4zNS4xNDgiLCJwb3J0IjoyMTAxMywic2N5IjoiYXV0byIsInBzIjoiMDMxN+S/hOe9l+aWryIsIm5ldCI6IndzIiwiaWQiOiI0NTVjZTczYS0yNDJjLTQ1MDItYjdjNi0xOTA3NDQ5YzE5NWEiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6IiIsInBhdGgiOiIvIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo4NzdjM2IwNjljMzM1ZmZj@163.171.181.49:12317#0317科威特 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@156.146.40.194:989#0317斯洛伐克 
trojan://2OnySp6YC3SZcF32XACEjlD5aDOqx9SeR6yRFDwEXAu3Fc8w3Z3Y4AqZ0OSzlN8NCeYIA@154.17.9.26:28333?flow=&security=tls&sni=bathtub.homeofbrave.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://lBSSFOalI3yXZDOAwADg9a8zTCexE6pjxeX4D3a0FgSSYRqlCyCOYcz83w3aYR3cTZDF8@154.17.20.103:443?flow=&security=tls&sni=length.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://jnaO0CFYpYExOygqlESRplzewIaKSFpBaqXy3YX4xBC8KK9ja94Y4S8aS7zjq96XSxO7CDu5BCYFCZg@154.17.13.71:443?flow=&security=tls&sni=lnitak.starspace.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://Yyjyl3Fwy6pSjTYSaCxg7Z0COIwBYxN38FwC3YBz44678OAypA87p2CEe53SaKel3pCDSZCZaeSaaZS@154.17.1.105:28335?flow=&security=tls&sni=printer.wireshop.net&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
vless://c4fa89d4-fcb9-48ba-adbc-665181cc817f@15.204.151.74:443?flow=&encryption=none&security=tls&sni=147135010072.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://SZAaY0CIRDey6OCSpS3Dl3F2nnDTYFqRS8aClceOwAyTwy39XxDz4FYXZO3AxRaEz2SlN@144.229.29.158:443?flow=&security=tls&sni=dessert.taiwanesefood.link&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTozYmY4YzVkYTEwZTAwMjRh@144.126.142.92:21448#0317美国 
ss://Y2hhY2hhMjA6djVhVVV0bWUzanhz@14.18.253.178:9003#0317孟加拉国 
ss://Y2hhY2hhMjA6TjlrNGYyUE9SbDE0@14.18.253.178:8348#0317以色列 
ss://Y2hhY2hhMjA6cTJrU0dwNGF5RktC@14.18.253.178:8347#0317法国 
ss://Y2hhY2hhMjA6YXZwQnFGRm1zWUJO@14.18.253.178:8335#0317日本 
ss://Y2hhY2hhMjA6RHZQZkthOHZzVjlL@14.18.253.178:8334#0317新加坡 
vless://54694a33-a8dc-47dd-bc38-acd3971e0055@135.148.206.182:443?flow=&encryption=none&security=tls&sni=147135004002.sec20org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
trojan://Fl4B9jyFAwE4XgFxuICw8pD0NCYIneA22OyYO30enl8Kxe3a3xcpDEyqa79CTNSpRA5D8@13.40.166.49:443?flow=&security=tls&sni=young.golfland.club&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317英国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.229.233.60:443#0317新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.215.250.172:443#0317新加坡 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4yMzIuMTUzLjYzIiwicG9ydCI6NDAxMDIsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6Ijc3MGVlNzMwLTI0NTAtNGUzYy1hNmM2LTM5MzJiZDMyYWZiZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6IjEyMC4xOTguNzEuMjE5IiwicG9ydCI6NDIwNTUsInNjeSI6ImF1dG8iLCJwcyI6IjAzMTfnvo7lm70iLCJuZXQiOiJ0Y3AiLCJpZCI6IjQxODA0OGFmLWEyOTMtNGI5OS05YjBjLTk4Y2EzNTgwZGQyNCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://YWVzLTI1Ni1nY206WDZXTVE5N1I5QUs3UFgwSQ==@109.104.154.131:20000#0317荷兰 
trojan://telegram-id-privatevpns@108.128.8.151:22222?flow=&security=tls&sni=trojan.burgerip.co.uk&type=tcp&header=none&host=&path=&alpn=http/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317爱尔兰 
hysteria2://074b7c98-21f1-4421-be61-41413db2fd44@107.172.235.75:29370?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#0317美国 
trojan://85950277-f447-48f0-9ead-aaf6d5ff3cad@104.21.34.159:443?flow=&security=tls&sni=df6xxxx.2031.pp.ua&type=ws&header=none&host=df6xxxx.2031.pp.ua&path=/I4L1BP2DQVYmx5NYQ76MGGq&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317美国 
vless://753fa8e8-a3e8-442e-abf7-875ed776eacb@104.17.221.248:443?flow=&encryption=none&security=tls&sni=is.oldcloud.online&type=ws&host=is.oldcloud.online&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317以色列 
vless://24a4aa9b-b341-4717-9d4a-00d74c2b84e0@104.17.147.22:2096?flow=&encryption=none&security=tls&sni=7G6gLgL6fJ.mYsPdMmEtI.cOm&type=ws&host=7G6gLgL6fJ.mYsPdMmEtI.cOm&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317塞浦路斯 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xNi4xNTUuMTAiLCJwb3J0Ijo4ODgwLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE3576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTEwMy01OC0zOS5zMS5kYi1saW5rMDIudG9wIiwicGF0aCI6Ii9kYWJhaS5pbjEwNC4yNS4yNDkuMjE1IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xNi4xNTUuMTAiLCJwb3J0IjoyMDUyLCJzY3kiOiJhdXRvIiwicHMiOiIwMzE3576O5Zu9IiwibmV0Ijoid3MiLCJpZCI6IjRiMzY2MjVjLWI5ZDktM2VhNi1hZWQ1LTg2ZDYyYzcwZTE2ZCIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiMTAwLTEwMi0yNDctOTIuczEuZGItbGluazAyLnRvcCIsInBhdGgiOiIvZGFiYWkuaW4xMDQuMjUuMTc1LjEzNyIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6YmJjMzVhOTItODdlYS00YmRhLTg0ZTQtOTJlYmRiMTU1MjM0QDQ1LjgyLjEyMC4yMTM6NDE0MzQ6d3M6L3VwcElpcVdCcXl1RWRqNTV3SlVlclglM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0317德国 
hysteria2://gINIT5FbIGPciJ4gW9ziFQAQcYECqX6@45.82.120.213:44118?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=UVb6xjf1685JdZopGPgsGZ6annfGRBW9jULa&os=#0317德国 
hysteria2://bVDGZOaRRDJTlzTowS0l1knXdyefP7YvVoNy3gk@45.82.120.213:20118?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=zE46bkyxuTVoAZJEHvv&os=#0317德国 
ss://Y2hhY2hhMjAtcG9seTEzMDU6Yjg4Mzk3Y2MtZjI0NC00YzUxLWFhYzgtZTRmOWNiZTA3MjI2QDQ1LjgyLjEyMC4yMTM6MTgzNTE6d3M6L2V0TFBjTGZhSXdXdE5aWUJubE40cEQ0cHNIJTNGZWQlM0QyNTYwOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOm5vbmU6dGxzOmRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tOltdOjp0cnVlOiwxMDAtMjAwLDEwLTYwOg==#0317德国 
hysteria2://pK4C8WfmMOnKNBjHAwROTVL757dKhuzp44fZEP@45.82.120.213:8225?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=eN7VVR0DXY9E66j1ztqmqhia&os=#0317德国 
hysteria2://Uich6OFjOgs9lfz0OrxuTX4lh@45.82.120.213:63352?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=to3kHHGYIspVSF70e34UB9GfZp62&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@162.159.7.2:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vless://bbc35a92-87ea-4bda-84e4-92ebdb155234@45.82.120.213:60456?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/WoPSjTaQoSTdf9vqh%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
hysteria2://VzZnrla6nT4vqgGeczY5VGZv8i@45.82.120.213:38418?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=8IkmF1ay9BO80r5Xaojdoych5TUMwdFgO&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@198.41.202.129:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.21.205.14:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0OTE5Niwic2N5IjoiYXV0byIsInBzIjoiMDMxN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIzNGQ2MzU2OC1lNDgyLTQxMDMtYTg0Yi1lMGQyZTZjYjI5NTYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9NT2hkb1lYMWZ0OEJMN2pvP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6MDllYzhjYzItZDdlYS00ODA3LTkwOTgtNTdhYjlmMDFlYjllQDQ1LjgyLjEyMC4yMTM6NTg1NDE6d3M6L3h3bWJKOGEzV2s4UkJGbmplcyUzRmVkJTNEMjU2MDpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpub25lOnRsczpkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbTpbXTo6dHJ1ZTosMTAwLTIwMCwxMC02MDo=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.31.125:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@188.114.98.210:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
hysteria2://LT4jmgqbbBFxNhVpf0y@45.82.120.213:46557?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=szigIuqcobUucjuriYyWRcaq&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@173.245.58.119:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.19.192.183:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vless://1c935ff6-94df-4517-b4fc-72f196d08ce7@45.82.120.213:19388?flow=&encryption=none&security=tls&sni=download.windowsupdate.com&type=ws&host=download.windowsupdate.com&path=/EZDyNk64ay%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0MzA0MSwic2N5IjoiYXV0byIsInBzIjoiMDMxN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiIxYzkzNWZmNi05NGRmLTQ1MTctYjRmYy03MmYxOTZkMDhjZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9aRVRqMllMaDI0bWlnNz9lZD0yNTYwIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb20iLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@172.66.150.203:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
trojan://09ec8cc2-d7ea-4807-9098-57ab9f01eb9e@45.82.120.213:58516?flow=&security=tls&sni=download.windowsupdate.com&type=ws&header=none&host=download.windowsupdate.com&path=/rhGEw0v8%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo0NzQxOSwic2N5IjoiYXV0byIsInBzIjoiMDMxN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI2MzQ3YzA4Yi0wODU4LTRkMTUtODkyNi03ZjFhMTBjODkzMmIiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9GeGhTMkgwbW1XSGZDODlRRzRnZno4V1U/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMC4yMTMiLCJwb3J0Ijo2MjQ1OSwic2N5IjoiYXV0byIsInBzIjoiMDMxN+W+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiJmZjRhMDExYy1lZGZlLTQ2OTEtYmIwMi0wNjkxZjdmNjhkODYiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImRvd25sb2FkLndpbmRvd3N1cGRhdGUuY29tIiwicGF0aCI6Ii9kP2VkPTI1NjAiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJkb3dubG9hZC53aW5kb3dzdXBkYXRlLmNvbSIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtcG9seTEzMDU6ZmY0YTAxMWMtZWRmZS00NjkxLWJiMDItMDY5MWY3ZjY4ZDg2QDQ1LjgyLjEyMC4yMTM6NzI5Mjp3czovRXNYZmpYWFlBc2NVS2hEMmclM0ZlZCUzRDI1NjA6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206bm9uZTp0bHM6ZG93bmxvYWQud2luZG93c3VwZGF0ZS5jb206W106OnRydWU6LDEwMC0yMDAsMTAtNjA6#0317德国 
vless://3df883f7-eb8a-489a-af70-6745602ecc1c@104.18.33.143:443?flow=&encryption=none&security=tls&sni=seck.secge.us.kg&type=xhttp&host=seck.secge.us.kg&path=/ZETj2YLh24mig7&mode=packet-up&alpn=h2&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#0317德国 
hysteria2://vbmNANpOabqnEUDz3qlg92fZg9X82fPu@45.82.120.213:36549?insecure=1&sni=download.windowsupdate.com&alpn=&fp=&obfs=salamander&obfs-password=xCncNDjXpqom367KZtCx&os=#0317德国 

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
