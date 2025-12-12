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
vmess://eyJ2IjoiMiIsImFkZCI6IjE4My4yMzYuNTEuMzYiLCJwb3J0Ijo1OTAwMywic2N5IjoiYXV0byIsInBzIjoiMTIxMeS4reWbvSIsIm5ldCI6InRjcCIsImlkIjoiNDE4MDQ4YWYtYTI5My00Yjk5LTliMGMtOThjYTM1ODBkZDI0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjo2NCwidHlwZSI6Im5vbmUiLCJob3N0IjoiIiwicGF0aCI6IiIsInRscyI6IiIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
vless://a00d89f6-ab7e-4e30-a5e5-54c701d62c93@178.236.16.98:35728?flow=&encryption=none&security=reality&sni=yahoo.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=vhUFNoFcvtZAVMo8y5K5eU2V43m5q6yjmWIhp5RkFng&sid=69a2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211哈萨克 
ss://YWVzLTI1Ni1jZmI6ZjhmN2FDemNQS2JzRjhwMw==@185.153.197.5:989?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1211摩尔多瓦 
vmess://eyJ2IjoiMiIsImFkZCI6InYxMi5oZGFjZC5jb20iLCJwb3J0IjozMDgxMiwic2N5IjoiYXV0byIsInBzIjoiMTIxMeaWsOWKoOWdoSIsIm5ldCI6InRjcCIsImlkIjoiY2JiM2Y4NzctZDFmYi0zNDRjLTg3YTktZDE1M2JmZmQ1NDg0IiwiYWxwbiI6IiIsImZwIjoiIiwiYWlkIjowLCJ0eXBlIjoibm9uZSIsImhvc3QiOiIiLCJwYXRoIjoiIiwidGxzIjoiIiwiYWxsb3dJbnNlY3VyZSI6ZmFsc2UsInNuaSI6IiIsImZyYWdtZW50IjoiLDEwMC0yMDAsMTAtNjAiLCJvcyI6IiJ9 
ss://Y2hhY2hhMjAtaWV0Zi1wb2x5MTMwNToxN1pET1JXSWxpUUh1TzZXUkdIQ2hYWU16ZFJ0QVlWUA==@45.14.245.2:443?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1211荷兰 
ss://YWVzLTI1Ni1jZmI6WG44aktkbURNMDBJZU8lIyQjZkpBTXRzRUFFVU9wSC9ZV1l0WXFERm5UMFNW@103.186.155.85:38388?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1211越南 
vless://jrghxqxyoy@jrghxqxyoy-518237151-direct.bahame.co:443?flow=xtls-rprx-vision&encryption=none&security=tls&sni=jrghxqxyoy-518237151-direct.bahame.co&type=tcp&host=&path=&headerType=none&alpn=http/1.1%2Ch2&fp=chrome&pbk=&sid=&spx=&allowInsecure=0&fragment=,100-200,10-60&os=#1211罗马尼亚 
vless://97b2cd5b-b98d-494f-8f97-3a06e8c1bbd2@151.101.195.6:443?flow=&encryption=none&security=tls&sni=hls-amt.itunes.apple.com&type=xhttp&host=adsmiatm1764454498.global.ssl.fastly.net&path=&mode=auto&alpn=h3&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://d2d0f796-edb0-427a-af32-ae360679f9e7@1password.com:443?flow=&encryption=none&security=tls&sni=rAyAn-007.fOtOn.dPdNs.oRg&type=ws&host=rayan-007.foton.dpdns.org&path=/%3Fed%3D2560&headerType=none&alpn=&fp=chrome&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
ss://YWVzLTI1Ni1nY206MTIz@14.18.106.88:6100?security=&sni=&type=tcp&header=none&host=&path=&alpn=&fp=&allowInsecure=1&fragment=,100-200,10-60&os=#1211中国 
trojan://LxJCPOP40a@206.206.77.237:51469?flow=&security=reality&sni=cloudflare.com&type=grpc&mode=gun&host=&serviceName=&alpn=&fp=chrome&pbk=nlxKGGnvTUULdJlG1vfRbiG9IFrbFYC9VMnMWNH_A3s&sid=793dfc59cf7edf&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211新加坡 
vless://0e8a6896-ad90-4a3b-89a3-77d64aa409e2@ilta-wzxrxkdhbjpnprhkkpplsjwawhssvollvxzdhqshiqckwdgrdm.orbnet.xyz:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=i2pd.website&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=YVDo7U4O-AT2fa5H9E7hyYHKgfZd1vB6UdbAf2ggWQE&sid=55e6af1a35e64a98&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211以色列 
trojan://BxceQaOe@219.78.209.224:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211香港 
trojan://BxceQaOe@58.152.25.20:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211香港 
trojan://BxceQaOe@58.152.25.242:443?flow=&security=tls&sni=t.me/ripaojiedian&type=tcp&header=none&host=&path=&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211香港 
vless://20cf5921-f7fa-47c5-81ae-947fbef83a4d@51.250.20.121:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=ads.x5.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=bYPDMM7Z7s3brAUozWIqspE24dQwgHyI60lDRZvscVo&sid=a20d3ed244c76426&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211俄罗斯 
vless://4a6de183-2ad3-456c-b420-feeac81f6257@51.250.109.47:1488?flow=xtls-rprx-vision&encryption=none&security=reality&sni=ads.x5.ru&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=SbVKOEMjK0sIlbwg4akyBg5mL5KZwwB-ed4eEE7YnRc&sid=6ba85179e30d4fc2&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211塞舌尔 
vless://d5f7970e-121f-4e6f-9acf-250effc0715b@89.23.101.203:443?flow=xtls-rprx-vision&encryption=none&security=reality&sni=www.vk.com&type=tcp&host=&path=&headerType=none&alpn=&fp=chrome&pbk=lJscl0GgEiVZtTVrMVI6O0-zSJTgmug9Cs-KJqpxWw0&sid=f6fb0261a102c0c8&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211荷兰 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.78:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
trojan://80e2bf00-7ad2-478d-b9c5-6abd14cd8ac8@45.82.121.113:56049?flow=&security=tls&sni=burgerip.co.uk&type=ws&header=none&host=burgerip.co.uk&path=/E7YhsVXxv729X7PA0WIgZWS%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.20.192.155:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
anytls://4gNkAZIhPN7zyRZaFClCgfkxjVXAxhDkwENpZQ7@45.82.121.113:57991?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.215.192:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
hysteria2://iZaEW3aL0iGTtGKeKen1ZOH6kK8832lF0fTrU8kj@45.82.121.113:61168?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=W5AgdGjJiV6IL4ApMQOQfAhh0KH8l&mport=&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.23.99.41:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.126:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.97.141:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
trojan://0cfc3669-b9c8-419b-9c6a-742bf550190d@45.82.121.113:13973?flow=&security=tls&sni=burgerip.co.uk&type=ws&header=none&host=burgerip.co.uk&path=/199BAA6IVtycSjf%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://74ddd677-a297-4b72-aad4-3e3c3b9f1623@45.82.121.113:3254?flow=&encryption=none&security=tls&sni=burgerip.co.uk&type=ws&host=burgerip.co.uk&path=/bK9McBQAwPOuwEViSVl%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@173.245.59.50:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
hysteria2://NbOOLTdG7o4myHjpM4IhiRKy95U0ED@45.82.121.113:60547?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=KTlROPUOn24jBE9mwAX4YrAGc1KIQwYzIcSZiYFZ&mport=&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.94.26:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@198.41.223.174:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
hysteria2://c6OCypWriS9BRyaHEyVlCGUmJCJur3JU01y@45.82.121.113:52949?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=ENGt9Mic7Zv2YqmdpwNzFc5deEBDwSVVzxzvlM&mport=&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.20.251.171:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://ee149a0a-b25b-4e8e-b9dc-1e9547693582@45.82.121.113:32434?flow=&encryption=none&security=tls&sni=burgerip.co.uk&type=ws&host=burgerip.co.uk&path=/v6CCVXcGOBZ6zrWb3n0TTLOm4nec%3Fed%3D2560&headerType=none&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
hysteria2://grCL4SatmCUsZLsa8ro@45.82.121.113:54954?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=A9XhvEnyU9pvuwfQwN9x6b0NClKM8Ns&mport=&os=#1211德国 
vmess://eyJ2IjoiMiIsImFkZCI6IjQ1LjgyLjEyMS4xMTMiLCJwb3J0Ijo1NDc5NSwic2N5IjoiYXV0byIsInBzIjoiMTIxMeW+t+WbvSIsIm5ldCI6IndzIiwiaWQiOiI4MGUyYmYwMC03YWQyLTQ3OGQtYjljNS02YWJkMTRjZDhhYzgiLCJhbHBuIjoiIiwiZnAiOiIiLCJhaWQiOjAsInR5cGUiOiJub25lIiwiaG9zdCI6ImJ1cmdlcmlwLmNvLnVrIiwicGF0aCI6Ii92SUo5ZWZRUndGZ3gyNTFzblZOZjZCbXk/ZWQ9MjU2MCIsInRscyI6InRscyIsImFsbG93SW5zZWN1cmUiOnRydWUsInNuaSI6ImJ1cmdlcmlwLmNvLnVrIiwiZnJhZ21lbnQiOiIsMTAwLTIwMCwxMC02MCIsIm9zIjoiIn0= 
anytls://ph29ybLwSZVHvkFFdQEB5cQYS9sleEhp3X7zp@45.82.121.113:48430?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@190.93.245.63:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@103.21.244.235:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
vless://06e90254-3a65-4cca-9ad9-8109ba4e6bea@104.25.225.87:443?flow=&encryption=none&security=tls&sni=y.34892.qzz.io&type=xhttp&host=y.34892.qzz.io&path=/ZETj2YLh24mig7%3F16c2e5ae-6e48-4970-ad29-b639cf5b9afb&mode=packet-up&alpn=h2&fp=randomized&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
anytls://C8gwTnshntBu5LUP7orx2IovBRcHOJZ1irZ886mF@45.82.121.113:2038?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1211德国 
trojan://fd4d89cd-578b-4d94-a11c-74b9c6282cc6@45.82.121.113:31878?flow=&security=tls&sni=burgerip.co.uk&type=ws&header=none&host=burgerip.co.uk&path=/xu6iHXFYelU%3Fed%3D2560&alpn=&fp=&pbk=&sid=&spx=&allowInsecure=1&fragment=,100-200,10-60&os=#1211德国 
hysteria2://fLYN58GmsrauRl9c1PEXZQ0BsCDgyGV@45.82.121.113:18283?insecure=1&sni=burgerip.co.uk&alpn=&fp=&obfs=salamander&obfs-password=P3bM8Op8SLJNkdNNES3ftAIOu9CVWekK&mport=&os=#1211德国 
anytls://n4essqM26H8ZqkgmeIaBvgZ6dsgZj@45.82.121.113:52198?insecure=1&sni=burgerip.co.uk&alpn=h2&fp=&os=#1211德国 



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
