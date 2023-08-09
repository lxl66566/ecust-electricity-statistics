import datetime
import json
import logging
import os
import re
from contextlib import suppress
from pathlib import Path

import requests

URL = os.environ.get("URL").strip()
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "").strip()
PUSH_PLUS_DETAIL = os.environ.get("PUSH_PLUS_DETAIL", "").strip()
GITHUB_TRIGGERING_ACTOR = os.environ.get("GITHUB_TRIGGERING_ACTOR", "").strip()
logging.basicConfig(level=logging.INFO)
logging.info(f"github.triggering_actor is {GITHUB_TRIGGERING_ACTOR}")

header = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Connection": "keep-alive",
    "Host": "yktyd.ecust.edu.cn",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Upgrade-Insecure-Requests": "1",
    "User-Agent": "Mozilla/5.0 (Linux; U; Android 4.1.2; zh-cn; Chitanda/Akari) AppleWebKit/534.30 (KHTML, like Gecko) Version/4.0 Mobile Safari/534.30 MicroMessenger/6.0.0.58_r884092.501 NetType/WIFI",
}
response = requests.get(URL, headers=header)

remain = float(re.findall((r"(\d+(\.\d+)?)度"), response.text)[0][0])
originstring = "[]"
date = datetime.datetime.now().strftime("%Y-%m-%d")

# read from data.js preprocessed as json
with suppress(FileNotFoundError):
    with open("data.js", "r", encoding="utf-8") as f:
        originstring = f.read().lstrip("data=")
data: list = json.loads(originstring)

# add new data
if data and date in data[-1].values():
    data[-1]["kWh"] = remain
else:
    data.append({"time": date, "kWh": remain})

# write back to data.js
originstring = json.dumps(data, indent=2, ensure_ascii=False)
Path("data.js").write_text("data=" + originstring, encoding="utf-8")
logging.info("write back to data.js")

# push plus
if PUSH_PLUS_TOKEN:
    from urllib.parse import parse_qs, urlparse

    from utils import sendMsgToWechat

    parsed_url = urlparse(URL)
    params = parse_qs(parsed_url.query)
    roomid = params.get("roomid")
    buildid = params.get("buildid")
    stime = date  # TODO timezone
    days_to_show = 10
    last_few_items = data[-days_to_show:]
    tablestr = "| 序号 | 时间 | 剩余电量 |\n|---|---|---|\n"
    index = 1
    for item in reversed(last_few_items):
        tablestr += f'| {index} | {item["time"]} | {item["kWh"]}kWh |\n'
        index += 1
    text = f"## 当前剩余电量：{remain}kWh\n个人信息：{buildid[0]}号楼{roomid[0]}室\n\n统计时间：{stime}\n\n### 最近{days_to_show}天数据\n"
    text += tablestr + "\n"
    if PUSH_PLUS_DETAIL and GITHUB_TRIGGERING_ACTOR:
        website = (
            f"https://{GITHUB_TRIGGERING_ACTOR}.github.io/ecust-electricity-statistics"
        )
        text += f"[图表显示更多数据]({website})\n"
        logging.info("show more details")
    with suppress():
        sendMsgToWechat(PUSH_PLUS_TOKEN, f"{stime}华理电费统计", text, "markdown")
        logging.info("push plus executed successfully")
