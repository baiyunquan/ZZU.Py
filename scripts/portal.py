"""Portal 认证测试脚本 — 使用指定无线网卡"""
import re
import urllib.parse
from urllib.parse import parse_qs

import httpx
import sys
from bs4 import BeautifulSoup

from loguru import logger

from zzupy.web import EPortalClient

# ── 凭据（来自 password.h）──
ACCOUNT = "202407010202"
PASSWORD = "sNmcc$0506"

# 无线网卡 IP（Intel Wi-Fi 6E AX211 — WLAN 2）
WIRELESS_IP = "10.178.164.14"

logger.remove()
logger.add(sys.stderr, level="TRACE")
logger.enable("zzupy")


def _discover_portal_via_wireless() -> dict:
    """通过无线网卡自动探测 Portal 信息"""
    transport = httpx.HTTPTransport(local_address=WIRELESS_IP)

    with httpx.Client(transport=transport, timeout=10.0) as client:
        # 1. 访问 http，触发 Portal 重定向
        r = client.get("http://bilibili.com", follow_redirects=True)

        if str(r.url).startswith("https://"):
            raise RuntimeError("未被 MITM，请检查校园网是否已认证")

        portal_url = str(r.url)

        # 解析重定向 URL
        soup = BeautifulSoup(r.text, features="html.parser")
        a_tag = soup.find("a")
        if a_tag and a_tag.get("href"):
            portal_url = a_tag["href"]

        # 提取 user_ip
        parsed = urllib.parse.urlparse(portal_url)
        query_params = parse_qs(parsed.query)
        user_ip = (
            query_params.get("userip", [None])[0]
            or query_params.get("wlanuserip", [None])[0]
            or WIRELESS_IP
        )

        auth_url = f"{parsed.scheme}://{parsed.netloc}"

        # 获取 Portal 服务器端口
        hostname = parsed.hostname
        try:
            js_r = client.get(f"{auth_url}/a41.js")
            pattern = r"var\s+(\w+)\s*=\s*(\d+);"
            js_params = {k: int(v) for k, v in re.findall(pattern, js_r.text)}
            if js_params.get("enableHttps") == 0:
                port = js_params.get("epHTTPPort", 801)
                portal_server_url = f"http://{hostname}:{port}"
            else:
                port = js_params.get("enHTTPSPort", 802)
                portal_server_url = f"https://{hostname}:{port}"
        except Exception:
            portal_server_url = f"http://{hostname}:801"

        return {
            "auth_url": auth_url,
            "portal_server_url": portal_server_url,
            "user_ip": user_ip,
        }


def main() -> bool:
    print("=== Portal 认证测试（无线网卡）===")
    print(f"网卡 IP: {WIRELESS_IP}")
    print(f"账号: {ACCOUNT}\n")

    try:
        # 1. 通过无线网卡探测 Portal 信息
        print("[1/3] 探测 Portal 信息（无线网卡）...")
        info = _discover_portal_via_wireless()
        print(f"  auth_url:           {info['auth_url']}")
        print(f"  portal_server_url:  {info['portal_server_url']}")
        print(f"  user_ip:            {info['user_ip']}\n")

        # 2. 用无线网卡 IP 创建客户端并认证
        print("[2/3] 发送认证请求...")
        with EPortalClient(
            info["portal_server_url"],
            bind_address=WIRELESS_IP,
            force_bind=True,
        ) as client:
            result = client.auth(ACCOUNT, PASSWORD)
            print(f"  success:  {result.success}")
            print(f"  message:  {result.message}\n")

        # 3. 验证：重新探测，若不再被重定向则说明认证成功
        print("[3/3] 验证认证结果...")
        try:
            info2 = _discover_portal_via_wireless()
            print(f"  仍然被重定向到 Portal → 可能未成功")
            print(f"  portal_url: {info2['auth_url']}")
        except Exception as e:
            print(f"  无法访问公网 Portal ({e}) → 认证很可能已成功 ✓")

        return True

    except Exception as e:
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
