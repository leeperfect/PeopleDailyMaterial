import requests

urls = [
    "http://paper.people.com.cn/rmrb/html/2026-02/16/nbs.D110000renmrb_01.htm",
    "http://paper.people.com.cn/rmrb/pc/layout/202602/16/node_01.html",
    "http://paper.people.com.cn/rmrb/pc/layout/202602/16/node_1.html",
    "http://paper.people.com.cn/rmrb/paperindex.htm"
]

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
}

for url in urls:
    try:
        response = requests.get(url, headers=headers, timeout=5)
        print(f"{url}: {response.status_code}")
        if response.status_code == 200:
            print(response.text[:200])
    except Exception as e:
        print(f"{url}: Error {e}")
