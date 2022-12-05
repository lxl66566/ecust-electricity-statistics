from contextlib import suppress
from pathlib import Path
import json,datetime,os,requests,re

# from playwright.sync_api import sync_playwright
# with sync_playwright() as playwright:
#     browser = playwright.chromium.launch(headless=True)
#     context = browser.new_context(
#         user_agent='Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; Chitanda/Akari) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 MicroMessenger/6.0.0.58_r884092.501 NetType/WIFI'
#     )
#     page = context.new_page()
#     url = os.environ.get('URL').strip()
#     page.goto(url)
#     remain = float(page.locator('text=/\d+\.\d+度/i').inner_text().rstrip("度"))

url = os.environ.get('URL').strip()
header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'yktyd.ecust.edu.cn',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'none',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; Chitanda/Akari) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 MicroMessenger/6.0.0.58_r884092.501 NetType/WIFI'
}
response = requests.get(url, headers=header)

remain = float(re.findall((r"(\d+(\.\d+)?)度"),response.text)[0][0])
originstring = '[]'
data = []
date = datetime.datetime.now().strftime("%Y-%m-%d")

with suppress(FileNotFoundError):
    with open("data.js",'r',encoding='utf-8') as f:
        originstring = f.read().lstrip("data=")

data = json.loads(originstring)
if len(data) != 0 and date in data[-1].values():
    data[-1]['kWh'] = remain
else:
    data.append({"time" : date, "kWh" : remain})

originstring = json.dumps(data,indent=4, ensure_ascii=False)
Path("data.js").write_text("data=" + originstring)