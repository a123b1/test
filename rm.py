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
vmess://eyJ2IjoiMiIsImFkZCI6IjEwNC4xOS4yMjQuMjgiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTblt7Topb8iLCJuZXQiOiJ3cyIsImlkIjoiODM2ZTBlNWEtMTBiOC00NTEzLWIzMzUtZTBlNmFkNmVjZWZlIiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJici50cmV2ZWx5LnVzLmtnIiwicGF0aCI6Ii9ici50cmV2ZWx5LnVzLmtnIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiYnIudHJldmVseS51cy5rZyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
hysteria2://55faebd1-758b-44a8-ad24-a5b273c486c8@107.172.235.75:47443?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#1216美国 
hysteria2://fc88afdf-ee72-4b7b-af2f-d28b8b00335e@128.204.223.99:59350?insecure=1&sni=www.bing.com&alpn=&fp=&os=#1216波兰 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@13.125.90.251:443#1216韩国 
vless://e20ebe01-1815-4c09-8e77-fb2f168263ce@135.148.177.196:443?flow=&encryption=none&security=tls&sni=147135001178.sec22org.com&type=tcp&host=&path=&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
trojan://061a01f1-704b-4712-8e12-6d3fc95a127d@146.56.158.235:21115?flow=&security=tls&sni=gevent.gmarket.co.kr&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
vless://d85346a9-ba7b-5c83-8c84-c3d54e42e9d1@151.101.1.6:80?flow=&encryption=none&security=&sni=&type=ws&host=PABLOO-MOSTAFA.COM&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216比利时 
vless://c55ceb81-ded6-5f51-b960-08223fecb4dd@151.101.129.6:80?flow=&encryption=none&security=&sni=TEHRANARGO.COM&type=ws&host=TEHRANARGO.COM&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216奥地利 
vless://c55ceb81-ded6-5f51-b960-08223fecb4dd@151.101.193.6:80?flow=&encryption=none&security=&sni=&type=ws&host=TEHRANARGO.COM&path=/%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO-%7C-%40TEHRANARGO%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216奥地利 
vmess://eyJ2IjoiMiIsImFkZCI6IjE1MS4xMDEuMi4xMzMiLCJwb3J0Ijo4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxNuazleWbvSIsIm5ldCI6IndzIiwiaWQiOiJhOTgzYzY5OC1jYWU0LTQyNTQtZDA0Ny01MTg5OGNjZDhlZTciLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImtpbS5nb3Yua3AiLCJwYXRoIjoiL2FyaWVzP2VkPTIwNDgiLCJ0bHMiOiIiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiIiLCJmcmFnbWVudCI6IiwxMDAtMjAwLDEwLTYwIiwib3MiOiIifQ== 
vless://d85346a9-ba7b-5c83-8c84-c3d54e42e9d1@151.101.65.6:80?flow=&encryption=none&security=&sni=&type=ws&host=PABLOO-MOSTAFA.COM&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216比利时 
vless://e9f6766e-b137-5a7d-97d7-373ef67e46b2@151.101.66.219:80?flow=&encryption=none&security=&sni=ELI-V2-RAY.COM&type=ws&host=ELI-V2-RAY.COM&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216荷兰 
hysteria2://55faebd1-758b-44a8-ad24-a5b273c486c8@151.249.104.35:34623?insecure=1&sni=dxobg4azmk.gafnode.sbs&alpn=&fp=&os=#1216捷克 
vmess://eyJ2IjoiMiIsImFkZCI6IjE3Mi42NC4xNTYuNzkiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTbnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNzlhNzJmYTktMDgyMC00N2FkLWE5ZDAtMTY4NmYyNzZiZmI2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cy50cmV2ZWx5LnVzLmtnIiwicGF0aCI6Ii91cy50cmV2ZWx5LnVzLmtnIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXMudHJldmVseS51cy5rZyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://b5cdabf0-e048-4fa2-90da-9379b1a4926e@172.67.27.46:80?flow=&encryption=none&security=&sni=cc.ailicf.us.kg&type=ws&host=cc.ailicf.us.kg&path=/b5cdabf0-e04&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.187.153:443#1216新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@18.141.231.184:443#1216新加坡 
hysteria2://f54584e2-640f-4c18-ae11-35c0a87fd730@188.68.240.161:59350?insecure=1&sni=www.bing.com&alpn=&fp=&os=#1216波兰 
vless://196e676a-d38e-57d1-82ac-3eac95a34fdb@199.232.125.50:443?flow=&encryption=none&security=tls&sni=JOiN--E-L-I-V-2-R-A-Y.net&type=ws&host=JOiN--E-L-i-V-2-R-A-Y.net&path=/&headerType=none&alpn=&fp=firefox&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216土耳其 
vless://913cdacd-2501-531a-8390-d2fcda924944@199.232.192.204:80?flow=&encryption=none&security=&sni=&type=ws&host=JOiN--E-L-i-V-2-R-A-Y.net&path=/Telegram%2C%40ELiV2RAY-Telegram%2C%40ELiV2RAY-Telegram%2C%40ELiV2RAY-%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216土耳其 
vless://76422c7c-4a72-5024-8275-e57848f17bb0@199.232.196.204:80?flow=&encryption=none&security=&sni=JOiN--E-L-i-V-2-R-A-Y.net&type=ws&host=JOiN--E-L-i-V-2-R-A-Y.net&path=/ProxyIP%3DProxyIP.US.fxxk.dedyn.io&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216土耳其 
vless://6b469585-4a07-4387-89cc-b28da026a9a7@212.192.13.179:9187?flow=&encryption=none&security=&sni=&type=ws&host=&path=/&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216中国 
ss://YWVzLTI1Ni1jZmI6cDl6NUJWQURIMllGczNNTg==@217.30.10.18:9040#1216波兰 
ss://YWVzLTI1Ni1jZmI6WkVUNTlMRjZEdkNDOEtWdA==@217.30.10.18:9005#1216波兰 
ss://YWVzLTI1Ni1jZmI6WFB0ekE5c0N1ZzNTUFI0Yw==@217.30.10.18:9025#1216波兰 
ss://YWVzLTI1Ni1jZmI6Z1lDWVhma1VRRXMyVGFKUQ==@217.30.10.18:9038#1216波兰 
ss://YWVzLTI1Ni1jZmI6ck5CZk51dUFORkNBazdLQg==@217.30.10.18:9056#1216波兰 
ss://YWVzLTI1Ni1jZmI6Qk5tQVhYeEFIWXBUUmR6dQ==@217.30.10.18:9020#1216波兰 
ss://YWVzLTI1Ni1jZmI6VE4yWXFnaHhlRkRLWmZMVQ==@217.30.10.18:9037#1216波兰 
ss://YWVzLTI1Ni1jZmI6SmRtUks5Z01FcUZnczhuUA==@217.30.10.18:9003#1216波兰 
ss://YWVzLTI1Ni1jZmI6VTZxbllSaGZ5RG1uOHNnbg==@217.30.10.18:9041#1216波兰 
ss://YWVzLTI1Ni1jZmI6d2ZMQzJ5N3J6WnlDbXV5dA==@217.30.10.18:9093#1216波兰 
ss://YWVzLTI1Ni1jZmI6THAyN3JxeUpxNzJiWnNxWA==@217.30.10.18:9045#1216波兰 
ss://YWVzLTI1Ni1jZmI6Rkc1ZGRMc01QYlY1Q3V0RQ==@217.30.10.18:9050#1216波兰 
ss://YWVzLTI1Ni1jZmI6cnBnYk5uVTlyRERVNGFXWg==@217.30.10.18:9094#1216波兰 
ss://YWVzLTI1Ni1jZmI6RVhOM1MzZVFwakU3RUp1OA==@217.30.10.18:9027#1216波兰 
trojan://aa6ddd2f-d1cf-4a52-ba1b-2640c41a7856@218.190.230.207:41288?flow=&security=tls&sni=hk12.bilibili.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216香港 
trojan://aa6ddd2f-d1cf-4a52-ba1b-2640c41a7856@218.190.230.207:42534?flow=&security=tls&sni=hk12.bilibili.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.1.79.116:443#1216新加坡 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.34.255.220:443#1216韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.38.182.255:443#1216韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@3.38.212.48:443#1216韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@34.222.132.123:443#1216美国 
trojan://QwwHvrnN@36.151.192.198:38698?flow=&security=tls&sni=36.151.192.198&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216日本 
trojan://QwwHvrnN@36.151.192.203:25241?flow=&security=tls&sni=36.151.192.203&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216香港 
trojan://DNUMdmnJ@36.151.192.239:42395?flow=&security=tls&sni=36.151.192.239&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216香港 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.122.162:443#1216韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@43.203.141.93:443#1216韩国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTo0YTJyZml4b3BoZGpmZmE4S1ZBNEFh@45.87.175.164:8080#1216荷兰 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@46.183.217.232:990#1216拉脱维亚 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTp4anpzaU1mVEJ5S2pBOVVSYmRYV05w@51.120.1.158:32091#1216挪威 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@51.15.15.82:989#1216罗马尼亚 
vless://0a44145f-59dc-4e5b-a233-677b97f5114c@51.81.36.78:443?flow=&encryption=none&security=tls&sni=147135011033.sec21org.com&type=tcp&host=&path=&headerType=none&alpn=h2%2Chttp/1.1&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.79.248.193:443#1216韩国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@52.89.164.115:443#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.200.220.184:443#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.201.174.149:443#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@54.244.200.142:443#1216美国 
ss://YWVzLTI1Ni1jZmI6YW1hem9uc2tyMDU=@57.181.42.233:443#1216日本 
ss://cmM0LW1kNToxNGZGUHJiZXpFM0hEWnpzTU9yNg==@79.110.53.169:8080#1216美国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToyRXRQcW42SFlqVU5jSG9oTGZVcEZRd25makNDUTVtaDFtSmRFTUNCdWN1V1o5UDF1ZGtSS0huVnh1bzU1azFLWHoyRm82anJndDE4VzY2b3B0eTFlNGJtMWp6ZkNmQmI=@84.19.31.63:50841#1216德国 
vless://6ff213b8-ccc7-4b5a-b4aa-37f7b792a1f1@89.187.169.71:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.cloudflare.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=B5i03yc1WUTOQD8v_N0UrCUaR4AgMJ40rEl8tXUJY0g&sid=01b200e90e250221&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjkxLjE5OS44NC4xMTIiLCJwb3J0Ijo0MDM4MCwic2N5IjoiYXV0byIsInBzIjoiMTIxNuWPsOa5viIsIm5ldCI6InRjcCIsImlkIjoiMTMzNjQ3ODktYThiMi00YmNkLThkZjctYTc5NGZiNmY4N2U1IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ6ZmEwNC4zMzMyMTAueHl6IiwicGF0aCI6Ii8iLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJ6ZmEwNC4zMzMyMTAueHl6IiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpmOGY3YUN6Y1BLYnNGOHAz@92.118.205.228:990#1216波兰 
vless://d74acf2c-2148-4343-891c-627c4b5d690b@ISVvpn.fastly80-2.hosting-ip.com:80?flow=&encryption=none&security=&sni=5774.ir&type=ws&host=5774.ir&path=/VLESS%3Fed%3D80&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1216德国 
trojan://aa6ddd2f-d1cf-4a52-ba1b-2640c41a7856@abf4a13f063dfe2373df11fe8b9ba0b4.v1.cac.node-is.green:45181?flow=&security=tls&sni=de1.bilibili.com&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216卢森堡 
vmess://eyJ2IjoiMiIsImFkZCI6ImNmLjA5MDIyNy54eXoiLCJwb3J0Ijo0NDMsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTbnvo7lm70iLCJuZXQiOiJ3cyIsImlkIjoiNzlhNzJmYTktMDgyMC00N2FkLWE5ZDAtMTY4NmYyNzZiZmI2IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJ1cy50cmV2ZWx5LnVzLmtnIiwicGF0aCI6Ii91cy50cmV2ZWx5LnVzLmtnIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoidXMudHJldmVseS51cy5rZyIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6ImlydmlkZW8uY2ZkIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIxMjE25rOV5Zu9IiwibmV0Ijoid3MiLCJpZCI6ImU1MzdmMmY1LTJhMGMtNGY1OS05MmM5LTgzMmNhNjQzM2JmMyIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6Ii9saW5rd3MiLCJ0bHMiOiJ0bHMiLCJhbGxvd0luc2VjdXJlIjp0cnVlLCJzbmkiOiJpcnZpZGVvLmNmZCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vmess://eyJ2IjoiMiIsImFkZCI6Im1sMDEuMzMzMjEwLnh5eiIsInBvcnQiOjQwMDAwLCJzY3kiOiJhdXRvIiwicHMiOiIxMjE25paw5Yqg5Z2hIiwibmV0Ijoid3MiLCJpZCI6IjEzMzY0Nzg5LWE4YjItNGJjZC04ZGY3LWE3OTRmYjZmODdlNSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoiZG93bi5kaW5ndGFsay5jb20iLCJwYXRoIjoiL2JieSIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://f8bb4ae1-2358-4a76-ab75-2a6bc94272d6@pscresearch.faculty.ucdavis.edu:443?flow=&encryption=none&security=tls&sni=pscresearch.faculty.ucdavis.edu&type=ws&host=hgc6rct87gy.com&path=/ws/%3Fed%3D2048&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216德国 
vmess://eyJ2IjoiMiIsImFkZCI6InJvb3QubWlkLmFsIiwicG9ydCI6ODAsInNjeSI6ImF1dG8iLCJwcyI6IjEyMTbms5Xlm70iLCJuZXQiOiJ3cyIsImlkIjoiYTk4M2M2OTgtY2FlNC00MjU0LWQwNDctNTE4OThjY2Q4ZWU3IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiJraW0uZ292LmtwIiwicGF0aCI6Ii9hcmllcz9lZD0yMDQ4IiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoiIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpXNzRYRkFMTEx1dzZtNUlB@series-a1.samanehha.co:443#1216英国 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNTpXNzRYRkFMTEx1dzZtNUlB@series-a2.samanehha.co:443#1216英国 
trojan://9d0a75d2-f747-4afa-b43f-d208af9e8f9a@us04.ssr.ee:443?flow=&security=tls&sni=us04.ssr.ee&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
trojan://9d0a75d2-f747-4afa-b43f-d208af9e8f9a@us06.ssr.ee:443?flow=&security=tls&sni=us06.ssr.ee&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1216美国 
vmess://eyJ2IjoiMiIsImFkZCI6InZpc2EuY29tIiwicG9ydCI6NDQzLCJzY3kiOiJhdXRvIiwicHMiOiIxMjE25paw5Yqg5Z2hIiwibmV0Ijoid3MiLCJpZCI6IjJmNmZhMzRhLWJhYmUtNDhhMy05NDkyLWE2MzQ3YTQ0Y2U5ZSIsImFscG4iOiIiLCJmcCI6IiIsImFpZCI6MCwidHlwZSI6Im5vbmUiLCJob3N0IjoieGpwLmRhbHVxdWFuLnRvcCIsInBhdGgiOiIvIiwidGxzIjoidGxzIiwiYWxsb3dJbnNlY3VyZSI6dHJ1ZSwic25pIjoieGpwLmRhbHVxdWFuLnRvcCIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
    
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
