# config.py 自定义配置,包括阅读次数、推送token的填写
import os
import re
import json
import random
import logging  # 新增日志模块

# 配置日志（仅输出到控制台，不影响 run_data.log）
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# =================== 配置部分 ===================
try:
    READ_NUM = int(os.getenv("READ_NUM", "120"))
except ValueError:
    READ_NUM = 120

PUSH_METHOD = os.getenv("PUSH_METHOD", "").strip()
PUSHPLUS_TOKEN = os.getenv("PUSHPLUS_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
WXPUSHER_SPT = os.getenv("WXPUSHER_SPT", "")
curl_str = os.getenv("WXREAD_CURL_BASH", "")

# =================== 书籍映射和随机选择 ===================
book_mapping = {
    "66b3227071c0abb966b281b": "罪连环（全集）",
    "a57325c05c8ed3a57224187": "明朝那些事儿(全集)",
    "39f329907161e25e39f893e": "明朝那些事儿(增补版)(套装全九册)",
}
b_values = list(book_mapping.keys())
random_b_value = random.choice(b_values)

# =================== 定义方法 ===================
def get_book_info():
    return book_mapping[random_b_value], random_b_value

# =================== 请求数据 ===================
REQUEST_DATA = {
    "appId": "wb182564874663h152492176",
    "b": random_b_value,
    "c": "7cb321502467cbbc409e62d",
    "ci": 70,
    "co": 0,
    "sm": "示例章节",
    "pr": 74,
    "rt": 30,
    "ts": 1727660516749,
    "rn": 31,
    "sg": "991118cc229871a5442993ecb08b5d2844d7f001dbad9a9bc7b2ecf73dc8db7e",
    "ct": 1727660516,
    "ps": "b1d32a307a4c3259g016b67",
    "pc": "080327b07a4c3259g018787",
}

# =================== 解析 Curl 命令 ===================
def convert(curl_command):
    headers_temp = {}
    cookies_temp = {}
    try:
        for match in re.findall(r"-H '([^:]+): ([^']+)'", curl_command):
            headers_temp[match[0]] = match[1]
        cookie_header = next((v for k, v in headers_temp.items() if k.lower() == "cookie"), "")
        cookie_b = re.search(r"-b '([^']+)'", curl_command)
        cookie_string = cookie_b.group(1) if cookie_b else cookie_header
        if cookie_string:
            for cookie in cookie_string.split("; "):
                if "=" in cookie:
                    key, value = cookie.split("=", 1)
                    cookies_temp[key.strip()] = value.strip()
        headers = {k: v for k, v in headers_temp.items() if k.lower() != "cookie"}
    except Exception as e:
        logger.warning(f"⚠️ 解析 Curl 命令出错: {e}")
        return default_headers, default_cookies
    return headers, cookies_temp

# =================== 默认值 ===================
default_headers = {
    "accept": "application/json, text/plain, */*",
    "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ko;q=0.5",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0",
}
default_cookies = {
    "RK": "oxEY1bTnXf",
    "ptcz": "53e3b35a9486dd63c4d06430b05aa169402117fc407dc5cc9329b41e59f62e2b",
    "pac_uid": "0_e63870bcecc18",
    "iip": "0",
    "_qimei_uuid42": "183070d3135100ee797b08bc922054dc3062834291",
    "wr_avatar": "https%3A%2F%2Fthirdwx.qlogo.cn%2Fmmopen%2FeeOpSbFh2Mb1bUxMW9Y3FRPfXwWvOLaNlsjWIkcKeeNg6vlVS5kOVuhNKGQ1M8zaggLqMPmpE5qIUdqEXlQgYg%2F132",
    "wr_gender": "0",
}
HEADERS, COOKIES = convert(curl_str) if curl_str else (default_headers, default_cookies)

# =================== 输出信息（通过日志模块输出到控制台） ===================
logger.info(f"📚 书籍映射表: {json.dumps(book_mapping, ensure_ascii=False, indent=2)}")
logger.info(f"📖 可用书籍 b 值: {b_values}")
logger.info(f"🎯 选定书籍: {book_mapping.get(random_b_value, '未知书籍')} (b值: {random_b_value})")
logger.info(f"📑 读取次数: {READ_NUM}")
logger.info(f"📤 推送方式: {PUSH_METHOD}")
