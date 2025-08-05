import datetime
import json
import logging
import os
import re
from contextlib import suppress
from pathlib import Path
from typing import Any, Callable, TypedDict

import requests
import tomllib


class ItemType(TypedDict):
    time: str
    kWh: float


# DEBUG：开启调试模式，将 pushplus/Telegram 消息输出至 stdout
DEBUG = os.environ.get("DEBUG", os.environ.get("debug", "")).strip()
URL = os.environ.get("URL", "").strip()
PUSH_PLUS_TOKEN = os.environ.get("PUSH_PLUS_TOKEN", "").strip()
GITHUB_TRIGGERING_ACTOR = os.environ.get("GITHUB_TRIGGERING_ACTOR", "").strip()
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
if s := os.environ.get("TELEGRAM_USER_IDS"):
    TELEGRAM_USER_IDS = [*s.strip().split()]
else:
    TELEGRAM_USER_IDS = []


config = tomllib.loads(Path("config.toml").read_text(encoding="utf-8"))
logging.basicConfig(level=logging.INFO)
logging.info(f"{GITHUB_TRIGGERING_ACTOR=}")


def once(func: Callable[..., Any]) -> Callable[..., Any]:
    """Runs a function only once."""
    results: dict[Any, Callable[..., Any]] = {}

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        if func not in results:
            results[func] = func(*args, **kwargs)
        return results[func]

    return wrapper


@once
def get_date() -> str:
    return datetime.datetime.now().strftime("%Y-%m-%d")


# 你理的 buildid 真是太棒了
def building_number_map(id: int | str) -> int:
    """
    将华理的 buildid 转换为实际楼号（奉贤）
    """
    match int(id):
        case x if x >= 27 and x <= 46:
            return x - 22
        case x if x >= 49 and x <= 52:
            return x - 24
        case other:
            return other


def get_last_few_items() -> list[ItemType]:
    days_to_show: int = config.get("days_to_show", 10)
    return data[-days_to_show:]


def generate_tablestr(last_few_items: list[ItemType]) -> str:
    tablestr = ["| 序号 | 时间 | 剩余电量 |\n| --- | --- | --- |"]
    for index, item in enumerate(reversed(last_few_items), 1):
        tablestr.append(f"| {index} | {item['time']} | {item['kWh']}kWh |")
    tablestr.append("")
    return "\n".join(tablestr)


def generate_message() -> str | None:
    from urllib.parse import parse_qs, urlparse

    parsed_url = urlparse(URL)
    params = parse_qs(parsed_url.query)
    roomid = params.get("roomid")
    buildid = params.get("buildid")
    assert roomid and buildid, "roomid or buildid cannot be empty"
    last_few_items = get_last_few_items()

    # insufficient electricity warning
    if not last_few_items:
        logging.info("last_few_items is empty, ignoring pushing...")
        return None

    last_remain = last_few_items[-1]["kWh"]
    text: list[str] = []
    if config.get("warning", 10) > last_remain:
        text.append(
            f"""# <text style="color:red;">警告：电量低于阈值({last_remain}kWh)</text>\n"""
        )
    else:
        if config.get("push_warning_only", False) and not DEBUG:
            logging.info("sufficient electricity, ignoring pushing...")
            return

    tablestr = generate_tablestr(last_few_items)

    text.extend(
        [
            f"## 当前剩余电量：{remain} kWh",
            "",
            f"个人信息：{building_number_map(buildid[0])} 号楼 {roomid[0]} 室",
            f"统计时间：{get_date()}",
            "",
            f"### 最近 {len(last_few_items)} 天数据",
            "",
            f"{tablestr}",
            "",
        ]
    )

    if config.get("detail", True) and GITHUB_TRIGGERING_ACTOR:
        logging.info("show more details")
        text.append(
            f"[图表显示更多数据](https://{GITHUB_TRIGGERING_ACTOR}.github.io/ecust-electricity-statistics)"
        )

    return "\n".join(text)


def pushplus(text: str | None) -> None:
    if not PUSH_PLUS_TOKEN and not DEBUG:
        logging.info("push plus token is empty, ignoring pushing...")
        return

    from utils import sendMsgToWechat

    if not text:
        return

    with suppress():
        if DEBUG:
            print(text)
        else:
            sendMsgToWechat(
                PUSH_PLUS_TOKEN, f"{get_date()}华理电费统计", text, "markdown"
            )
        logging.info("push plus executed successfully")


def telegram(text: str | None) -> None:
    if not TELEGRAM_BOT_TOKEN:
        logging.info("telegram bot token is empty, ignoring pushing...")
        return
    if not TELEGRAM_USER_IDS:
        logging.info("telegram user ids is empty, ignoring pushing...")
        return

    if not text:
        return

    import telegramify_markdown

    for user_id in TELEGRAM_USER_IDS:
        if not user_id:
            continue

        with suppress(ValueError):
            if DEBUG:
                print(text)

            response = requests.post(
                f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": int(user_id),
                    "text": telegramify_markdown.markdownify(text),
                    "parse_mode": "MarkdownV2",
                },
                headers={"Content-Type": "application/json"},
            )
            if response.status_code == 200:
                logging.info("telegram executed successfully")
                logging.debug(response.text)
            else:
                logging.error(
                    f"telegram failed with status code {response.status_code}"
                )
                logging.error(response.text)


# main
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

try:
    remain = float(re.findall((r"(-?\d+(\.\d+)?)度"), response.text)[0][0])
    logging.info(f"剩余电量：{remain}")
except Exception as e:
    logging.exception(e)
    logging.error("剩余电量获取失败，response: " + response.text)
    exit(1)

originstring = "[]"

# read from data.js preprocessed as json
with suppress(FileNotFoundError):
    with open("data.js", "r", encoding="utf-8") as f:
        originstring = f.read().lstrip("data=")
try:
    data: list[ItemType] = json.loads(originstring)
except json.decoder.JSONDecodeError:
    logging.error("data.js 格式错误，请参考注意事项进行检查")
    exit(1)

# add new data
if data and (get_date() in data[-1].values()):
    data[-1]["kWh"] = remain
else:
    data.append({"time": get_date(), "kWh": remain})

# write back to data.js
if not DEBUG:
    originstring = json.dumps(data, indent=2, ensure_ascii=False)
    _ = Path("data.js").write_text("data=" + originstring, encoding="utf-8")
    logging.info("write back to data.js")

text = generate_message()
pushplus(text)
telegram(text)
