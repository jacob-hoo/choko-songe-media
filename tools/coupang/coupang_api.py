"""쿠팡파트너스 Open API 클라이언트 (최종승인 후 사용).

주의: 경로·서명 형식은 공개 예제와 n8n-nodes-coupang-partners 문서(2026-10-26 대조)를 따랐다. 공식 가이드와는 키 발급 후 첫 호출로 확인한다.
키를 발급받으면 파트너스 API 문서와 대조할 것.
"""
import hashlib
import hmac
import json
import os
import time
import urllib.parse
import urllib.request

DOMAIN = "https://api-gateway.coupang.com"
BASE = "/v2/providers/affiliate_open_api/apis/openapi/v1"


def _auth(method: str, path: str, query: str) -> str:
    access = os.environ["COUPANG_ACCESS_KEY"]
    secret = os.environ["COUPANG_SECRET_KEY"]
    signed_date = time.strftime("%y%m%dT%H%M%SZ", time.gmtime())
    message = signed_date + method + path + query
    signature = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return (f"CEA algorithm=HmacSHA256, access-key={access}, "
            f"signed-date={signed_date}, signature={signature}")


def _request(method: str, path: str, params: dict | None = None, body: dict | None = None) -> dict:
    query = urllib.parse.urlencode(params or {})
    url = DOMAIN + path + (f"?{query}" if query else "")
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method, headers={
        "Authorization": _auth(method, path, query),
        "Content-Type": "application/json;charset=UTF-8",
    })
    with urllib.request.urlopen(req, timeout=20) as resp:
        return json.loads(resp.read())


def search(keyword: str, limit: int = 10) -> list[dict]:
    res = _request("GET", f"{BASE}/products/search", {"keyword": keyword, "limit": limit})
    return res.get("data", {}).get("productData", [])


def goldbox() -> list[dict]:
    return _request("GET", f"{BASE}/products/goldbox").get("data", [])


def best_in_category(category_id: int, limit: int = 20) -> list[dict]:
    return _request("GET", f"{BASE}/products/bestcategories/{category_id}", {"limit": limit}).get("data", [])


def deeplinks(urls: list[str]) -> list[dict]:
    return _request("POST", f"{BASE}/deeplink", body={"coupangUrls": urls}).get("data", [])


def to_rows(products: list[dict], category: str) -> list[dict]:
    """API 응답을 products.csv와 같은 형식으로 변환."""
    return [{
        "product_id": str(p.get("productId")),
        "name": p.get("productName", ""),
        "price": str(p.get("productPrice", "")),
        "category": category,
        "partner_url": p.get("productUrl", ""),  # API 응답 URL은 이미 파트너스 추적 링크
        "image": p.get("productImage", ""),
        "features": "",
        "my_take": "",
    } for p in products]
