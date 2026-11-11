#!/usr/bin/env python3
"""
이터널 리턴 소식 → 디스코드 웹훅 알림 (스킨 · 새 시즌 · 쿠폰 · 점검 · 패치노트)

- Steam 한국어 공지 (상점 뉴스 페이지와 같은 데이터)
  · 쿠폰 코드가 있는 공지 → 항상 보냄 (코드를 따로 강조)
  · 서버 점검 안내/완료, 패치노트, 핫픽스 → 보냄
  · 제목에 '스킨'이 있는 공지 → 보냄
  · 새 시즌 번호(예: 시즌 14)가 처음 나온 날부터 3주 동안, 그 시즌 공지 → 보냄
  · 나머지(이모티콘, 만화, 당첨자 발표 등) → 건너뜀
  · 공지에 유튜브 영상이 붙어 있으면 링크를 같이 보내서 디스코드에서 바로 재생
- 쿠폰 마감 24시간 전에 한 번 더 알림 (기한을 읽을 수 있는 쿠폰만)
- 유튜브 이터널 리턴 한국 채널 (쇼츠 포함)
  · 쇼츠/영상 설명에 쿠폰 코드가 있으면 필터와 상관없이 보냄 (시즌 D-7, D-3 쇼츠 쿠폰 등)
  · 제목/설명에 스킨·시즌·미리보기·찾아옵니다 가 있는 영상만
  · KEL·마스터즈 같은 대회 영상은 제외
- 명령어 봇(Worker)에서 /쿠폰추가 로 직접 등록한 쿠폰도 마감 알림 (WORKER_URL 설정 시)
- 보낸 기록은 state.json에 저장 (중복 방지)
- 디스코드 명령어 봇(worker.js)이 읽을 모음 데이터는 data.json에 저장
  (쿠폰과 기한, 스킨 공지·쇼츠, 패치노트·핫픽스, 스킨·시즌 영상)
- 표준 라이브러리만 사용 → pip install 필요 없음

사용법
  python bot.py              평소 실행 (새 글/영상만 전송)
  python bot.py --check      지금 올라와 있는 공지/영상이 필터에서 보냄/건너뜀 중 무엇인지 목록만 출력
  python bot.py --test       필터를 통과하는 최신 공지 1개 + 영상 1개를 강제로 전송
  python bot.py --dry-run    디스코드로 보내지 않고 보낼 내용만 출력

환경 변수 (전부 선택, DISCORD_WEBHOOK_URL만 필수)
  DISCORD_WEBHOOK_URL   디스코드 채널 웹후크 주소
  MENTION               쿠폰 알림 때 붙일 멘션. 예: @everyone 또는 <@&역할ID>
  STEAM_KEYWORDS        제목에 이 단어가 있으면 보냄 (기본: 스킨)
  STEAM_PATCH_KEYWORDS  제목에 이 단어가 있으면 제외 단어와 상관없이 보냄
                        (기본: 패치노트,핫픽스,서버 점검,점검 안내,점검 완료,임시 점검,긴급 점검)
  STEAM_EXCLUDE         제목에 이 단어가 있으면 건너뜀 (기본: 당첨자,오류,이상 현상)
  SEASON_WINDOW_DAYS    새 시즌 소식을 받을 기간(일) (기본: 21, 0이면 끔)
  YOUTUBE_CHANNELS      채널 주소/@핸들/채널 ID, 쉼표로 여러 개 (기본: 이터널 리턴 한국 채널). off면 끔
  YOUTUBE_KEYWORDS      제목/설명에 이 단어가 있으면 보냄 (기본: 스킨,시즌,미리보기,미리 보기,찾아옵니다)
  YOUTUBE_EXCLUDE       제목에 이 단어가 있으면 건너뜀 (기본: KEL,마스터즈,서포트 패키지,비하인드,슈퍼컵,Masters,내셔널 리그)
  YOUTUBE_SHORTS        off면 쇼츠 제외 (기본: 쇼츠 포함)
  COUPON_REMIND_HOURS   쿠폰 마감 몇 시간 전에 한 번 더 알릴지 (기본: 24, 0이면 끔)
  WORKER_URL            명령어 봇(Cloudflare Worker) 주소. 넣으면 /쿠폰추가 로 직접 등록한 쿠폰도 마감 알림에 넣고,
                        Worker가 유튜브 새 영상을 따로 올리고 있으면 여기서는 유튜브 알림을 안 보냄 (겹침 방지)
  YOUTUBE_NOTIFY        auto(기본) = 위처럼 자동 / on = 항상 여기서도 보냄 / off = 여기서는 유튜브 알림 안 보냄

  키워드 목록은 쉼표로 구분. * 를 쓰면 전부 보냄, none 을 쓰면 키워드로는 아무것도 안 보냄.
"""

import argparse
import copy
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

APP_ID = 1049590  # 이터널 리턴 Steam 앱 ID
STEAM_SOURCE = "store-events-koreana"
STEAM_EVENTS_URL = (
    "https://store.steampowered.com/events/ajaxgetadjacentpartnerevents/"
    f"?appid={APP_ID}&count_before=0&count_after=30&lang_list=4_0&l=koreana"
)
STEAM_VIEW_URL = f"https://store.steampowered.com/news/app/{APP_ID}/view/{{}}?l=koreana"
YOUTUBE_FEED_URL = "https://www.youtube.com/feeds/videos.xml?channel_id={}"

DEFAULTS = {
    "STEAM_KEYWORDS": "스킨",
    "STEAM_PATCH_KEYWORDS": "패치노트,핫픽스,서버 점검,점검 안내,점검 완료,임시 점검,긴급 점검",
    "STEAM_EXCLUDE": "당첨자,오류,이상 현상",
    "SEASON_WINDOW_DAYS": "21",
    "YOUTUBE_CHANNELS": "UCEOaB76vS9RfiAwEzxB8QGw",  # 이터널 리턴 한국 채널 (@EternalReturnKR)
    "YOUTUBE_KEYWORDS": "스킨,시즌,미리보기,미리 보기,찾아옵니다",
    "YOUTUBE_EXCLUDE": "KEL,마스터즈,서포트 패키지,비하인드,슈퍼컵,Masters,내셔널 리그",
    "YOUTUBE_SHORTS": "on",
    "COUPON_REMIND_HOURS": "24",
    "YOUTUBE_NOTIFY": "auto",
}

STATE_FILE = Path(__file__).with_name("state.json")
DATA_FILE = Path(__file__).with_name("data.json")  # 디스코드 명령어 봇(worker.js)이 읽는 모음 데이터
USER_AGENT = "Mozilla/5.0 (compatible; ER-News-Discord-Bot/1.3)"
DISCORD_USER_AGENT = "DiscordBot (https://github.com, 1.3)"
KST = timezone(timedelta(hours=9))
DATA_LIMITS = {"coupons": 60, "skins": 300, "patches": 40, "videos": 60}
# 스킨 모음(/스킨)에 넣을 유튜브 영상: 제목에 '스킨'이 있거나, 설명에 스킨 소개 문구가 있는 것.
# (대회 영상 설명의 "뉴스레터 구독하고 '○○' 스킨도 받아가세요", 보상 목록의 "스킨 데이터 세트" 같은 건 안 걸리게)
_SKIN_DESC_RE = re.compile(
    r"찾아옵니다|#신규\s*스킨|#신스킨"
    r"|(?:특별한?|보너스|영웅|신규|새로운|첫(?:\s*번째)?|두\s*번째|세\s*번째|ER\s*(?:Pass|패스)(?::\s*\w+)?의?)\s*(?:등급\s*)?스킨"
    r"|스킨을\s*지급",
    re.I,
)
_SKIN_TITLE_EXCLUDE = re.compile(r"신규\s*캐릭터|신규\s*실험체|실험체|신캐|\bMV\b")
# "새로운 실험체 ○○가 여러분을 찾아옵니다" 같은 캐릭터 소개는 스킨이 아님
_CHARACTER_DESC = re.compile(r"새로운\s*실험체|신규\s*실험체|신규\s*캐릭터|오리지널\s*캐릭터")
# Steam 스킨 공지 중 모음에서 뺄 것 (스킨 박스 판매, 환불, 사용 제한 같은 운영 공지)
SKIN_NOTICE_EXCLUDE = ("당첨자", "오류", "박스", "환불", "제한", "중단", "비활성화", "원복", "교환권",
                       "확률", "후속", "정상화", "보급권", "선택권", "현상", "소개 페이지", "전체 스킨", "올 스킨")


# 실험체 이름 (나무위키 '분류:이터널 리턴/실험체' 기준). 새 캐릭터는 공지 제목에서 자동으로 배움(data.json의 chars_extra).
CHARACTERS = (
    "가넷 나딘 나타폰 니아 니키 다니엘 다르코 데비&마를렌 띠아 라우라 레녹스 레니 레온 로지 루치아 루크 르노어 "
    "리 다이린 리오 마르티나 마이 마커스 매그너스 미르카 바냐 바바라 버니스 블레어 비앙카 비형 샬럿 세레스 셀린 쇼우 "
    "쇼이치 수아 슈린 시셀라 실비아 아델라 아드리아나 아디나 아르다 아비게일 아야 아이솔 아이작 알렉스 알론소 얀 에스텔 "
    "에이든 에키온 엘레나 엠마 요한 윌리엄 유민 유스티나 유키 이렘 이바 이슈트반 이안 일레븐 자히르 재키 제니 츠바메 "
    "카밀로 카티야 칼라 캐시 케네스 코렐라인 크레이버 클로에 키아라 타지아 테오도르 펜리르 펠릭스 프리야 피오라 피올로 "
    "하트 헤이즈 헨리 현우 혜진 히스이"
).replace("리 다이린", "리_다이린").split()
CHARACTERS = [c.replace("_", " ") for c in CHARACTERS]
_CHAR_ALIASES = {
    "데비&마를렌": ["데비&마를렌", "데비 & 마를렌", "데비마를렌", "데비와 마를렌", "데비", "마를렌", "뎁마", "데마", "데비 마를렌"],
    "리 다이린": ["리 다이린", "리다이린", "다이린"],
    "자히르": ["자히르", "부자히르"],   # 스킨 이름 말장난 (부자 + 자히르)
    "쇼우": ["쇼우", "판다왔쇼우"],
}
# 이름 뒤에 이 글자가 오면 다른 단어 (마이크, 이바지 …)
_CHAR_NOT_FOLLOWED = {"마이": "크|너|페이지|룸|웨이|홈|트|스터", "이바": "지", "제니": "퍼", "로지": "컬|스틱", "칼라": "풀|파"}
_CHAR_STOP = {"미리", "미리보기", "출시", "소개", "스킨", "이벤트", "안내", "업데이트", "공개", "등장", "추가"}


def _char_regex(name):
    aliases = sorted(_CHAR_ALIASES.get(name, [name]), key=len, reverse=True)
    tail = _CHAR_NOT_FOLLOWED.get(name)
    body = "|".join(re.escape(a) for a in aliases)
    return re.compile(r"(?<![가-힣A-Za-z0-9])(?:" + body + r")" + (rf"(?!{tail})" if tail else "") + r"(?![A-Za-z0-9])")


_CHAR_RE_CACHE = {}


def extract_characters(text, extra=(), limit=3):
    """글 속에 나온 실험체 이름을 나온 순서대로 (최대 limit개)."""
    found = []
    for name in list(CHARACTERS) + [e for e in extra if e not in CHARACTERS]:
        rx = _CHAR_RE_CACHE.get(name) or _CHAR_RE_CACHE.setdefault(name, _char_regex(name))
        m = rx.search(text or "")
        if m:
            found.append((m.start(), name))
    return [n for _, n in sorted(found)][:limit]


def learn_characters(title):
    """'신규 캐릭터 세레스 미리보기', '세레스 : 신규 실험체 출시' 같은 제목에서 새 캐릭터 이름 뽑기."""
    names = re.findall(r"신규\s*(?:캐릭터|실험체)\s*\]?\s*[-:]?\s*([가-힣]{2,6})", title or "")
    names += re.findall(r"([가-힣]{2,6})\s*:\s*신규\s*실험체", title or "")
    return [n for n in names if n not in _CHAR_STOP]


def is_skin_video(title, desc):
    desc = desc or ""
    if _SKIN_TITLE_EXCLUDE.search(title):
        return False
    if "스킨" in title:
        return True
    if _SKIN_DESC_RE.search(desc) and not _CHARACTER_DESC.search(desc):
        return True
    return bool(re.search(r"미리\s*보기", title)) and "스킨" in desc
CLAN_IMAGE_BASE = "https://clan.fastly.steamstatic.com/images"
BOT_NAME = "이터널 리턴 알리미"
MAX_SEEN = 300
COLOR_NEWS = 0x5865F2
COLOR_SEASON = 0x2ECC71
COLOR_COUPON = 0xF1C40F
PREVIEW_CHARS = 350
MAX_VIDEOS_PER_POST = 2
DAY = 86400

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "yt": "http://www.youtube.com/xml/schemas/2015",
    "media": "http://search.yahoo.com/mrss/",
}

# ---------------------------------------------------------------- 공통


def http_get(url, retries=3):
    req = urllib.request.Request(
        url, headers={"User-Agent": USER_AGENT, "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8"}
    )
    last_err = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                return resp.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt + 1 < retries:
                time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{url} 요청 실패: {last_err}")


def _clip(s, n):
    s = s or ""
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def watch_url(video_id):
    return f"https://www.youtube.com/watch?v={video_id}"


def _split_list(value):
    return [x.strip() for x in re.split(r"[,\n]", value or "") if x.strip()]


def setting(name):
    """환경 변수가 비어 있으면 기본값."""
    value = os.environ.get(name, "").strip()
    return value if value else DEFAULTS.get(name, "")


def keyword_list(name):
    value = setting(name)
    if value.lower() in ("none", "off", "-"):
        return []
    return _split_list(value)


def contains_any(text, words):
    if "*" in words:
        return True
    text = (text or "").lower()
    return next((w for w in words if w.lower() in text), None)


# ---------------------------------------------------------------- Steam 공지


def fetch_news():
    """Steam 한국어 공지 목록을 오래된 것부터 정렬해서 돌려준다."""
    data = json.loads(http_get(STEAM_EVENTS_URL).decode("utf-8"))
    items = []
    for e in data.get("events", []):
        body = e.get("announcement_body") or {}
        gid = str(e.get("gid") or body.get("event_gid") or body.get("gid") or "")
        if not gid:
            continue
        items.append({
            "gid": gid,
            "title": e.get("event_name") or body.get("headline") or "(제목 없음)",
            "date": int(body.get("posttime") or e.get("rtime32_start_time") or 0),
            "contents": body.get("body") or "",
            "url": STEAM_VIEW_URL.format(gid),
        })
    return sorted(items, key=lambda i: i["date"])


# Steam 공지에서 쓰는 BBCode 태그만 지운다.
# ([Settings] → [Support] 같은 일반 대괄호 글자는 남겨야 해서 태그 이름을 정해 둠)
_BB_TAGS = (
    r"(?:b|i|u|s|strike|h[1-6]|p|list|olist|quote|code|spoiler|noparse|hr|"
    r"table|tr|td|th|url|img|previewyoutube|video|carousel|expand)"
)
_BB_TAG_RE = re.compile(r"\[/?" + _BB_TAGS + r"(?:[= ][^\]]*)?\]", re.I)


def bbcode_to_text(raw):
    s = html.unescape(raw or "")
    s = s.replace("\\[", "[").replace("\\]", "]")
    s = re.sub(r"\[img[^\]]*\].*?\[/img\]", "", s, flags=re.S | re.I)
    s = re.sub(r"\[previewyoutube[^\]]*\].*?\[/previewyoutube\]", "", s, flags=re.S | re.I)
    s = re.sub(r"\[url=[^\]]*\](.*?)\[/url\]", r"\1", s, flags=re.S | re.I)
    s = re.sub(r"\[(?:/p|br|/h[1-6]|/list|/olist|/tr|hr)\]", "\n", s, flags=re.I)
    s = s.replace("[/*]", "")
    s = re.sub(r"\[\*\]\s*", "\n• ", s)
    s = _BB_TAG_RE.sub("", s)
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("​", "")
    s = re.sub(r"[ \t]+\n", "\n", s)
    s = re.sub(r"\n\s*\n(?=• )", "\n", s)  # 목록 사이 빈 줄 정리
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def first_image(raw):
    raw = raw or ""
    m = re.search(r"\{STEAM_CLAN_IMAGE\}(/[^\s\"'\[\]]+?\.(?:png|jpe?g|gif|webp))", raw, re.I)
    if m:
        return CLAN_IMAGE_BASE + m.group(1)
    m = re.search(r"(https?://[^\s\"'\[\]]+?\.(?:png|jpe?g|gif|webp))", raw, re.I)
    return m.group(1) if m else None


def youtube_ids_in(raw):
    """공지 본문에 들어 있는 유튜브 영상 ID (순서 유지, 중복 제거)."""
    ids = re.findall(
        r"(?:previewyoutube=|youtube\.com/watch\?v=|youtube\.com/shorts/|youtu\.be/)([\w-]{11})",
        raw or "",
    )
    return list(dict.fromkeys(ids))


# "쿠폰 코드 : SEASON13GLORY", "쿠폰 번호: GLORYBLAIR", "쿠폰: THX3RDANNIVERSARY", "쿠폰코드: s8SPLASH0710",
# "Coupon Code: ERVALENTINE" 형태.
_CODE_RE = re.compile(
    r"(?i:coupon\s*code|쿠폰\s*(?:코드|번호)|쿠폰)\s*[:：]\s*([A-Za-z0-9]{4,30})(?![A-Za-z0-9])"
)
_REWARD_RE = re.compile(r"^(?:쿠폰\s*)?(?:rewards?|보상|리워드)\s*[:：]\s*(.+)$", re.I)
_VALID_RE = re.compile(
    r"^(?:쿠폰\s*)?(?:valid\s*(?:thru|through|until)|expires?|expiration|사용\s*기간|유효\s*기간|등록\s*기간|기간|기한)\s*[:：]\s*(.+)$",
    re.I,
)


def _looks_like_code(s):
    """'Coming' 같은 영어 단어는 빼고, 대문자·숫자가 절반 이상인 것만 코드로 봄."""
    return sum(ch.isupper() or ch.isdigit() for ch in s) >= max(3, len(s) // 2)


def extract_coupons(text):
    """본문에서 쿠폰 코드와 바로 뒤의 보상/기한 줄을 묶어서 뽑는다."""
    coupons = []
    current = None
    for line in text.splitlines():
        line = re.sub(r"^[^0-9A-Za-z가-힣]+", "", line.strip())  # 앞쪽 '- ', '🎫 ', '⏰ ' 같은 기호 제거
        if not line:
            continue
        m = _CODE_RE.search(line)
        if m and _looks_like_code(m.group(1)):
            code = m.group(1)
            current = next((c for c in coupons if c["code"] == code), None)
            if current is None:
                current = {"code": code, "reward": None, "valid": None}
                coupons.append(current)
            continue
        if current is None:
            continue
        r = _REWARD_RE.match(line)
        if r and not current["reward"]:
            current["reward"] = r.group(1).strip()
            continue
        v = _VALID_RE.match(line)
        if v and not current["valid"]:
            current["valid"] = v.group(1).strip()
    return coupons


# 제목 속 시즌 번호: "시즌 13", "시즌13", "Season 13", "S13", "13.0 패치노트"
_SEASON_RE = re.compile(
    r"(?:시즌|season)\s*(\d{1,2})(?!\d)"
    r"|\bS(\d{1,2})(?![\d.])"
    r"|(?<![\d.])(\d{1,2})\.0(?!\d)\s*(?:패치\s*노트|patch)",
    re.I,
)


def season_numbers(title):
    return [int(n) for m in _SEASON_RE.finditer(title or "") for n in m.groups() if n]


def initial_season(items):
    """처음 실행할 때: 지금 공지에 나온 가장 큰 시즌 번호와 그 번호가 처음 나온 날."""
    best = {"num": 0, "since": 0}
    for i in items:  # 오래된 순
        nums = season_numbers(i["title"])
        if nums and max(nums) > best["num"]:
            best = {"num": max(nums), "since": i["date"]}
    return best


def decide_steam(item, season, cfg, seen_codes):
    """공지 1개를 보낼지 정한다. season(dict)은 새 시즌이 나오면 여기서 갱신된다.
    돌려주는 값: (보낼지, 이유, 새 쿠폰 목록, 새 시즌 소식인지)"""
    title = item["title"]
    text = bbcode_to_text(item.get("contents", ""))
    coupons = [c for c in extract_coupons(text) if c["code"] not in seen_codes]

    in_window = False
    nums = season_numbers(title)
    if nums and cfg["window_days"] > 0:
        top = max(nums)
        if top > season["num"]:
            season.update(num=top, since=item["date"])
            in_window = True
        elif top == season["num"] and item["date"] - season["since"] <= cfg["window_days"] * DAY:
            in_window = True

    if coupons:
        return True, "쿠폰 " + ", ".join(c["code"] for c in coupons), coupons, in_window
    excluded = contains_any(title, cfg["steam_exclude"]) if cfg["steam_exclude"] else None
    if in_window and not excluded:
        return True, f"새 시즌 {season['num']} 소식", [], True
    # 점검·패치노트는 제외 단어와 상관없이 보냄 (예: '접속 오류 긴급 점검 안내')
    patch = contains_any(title, cfg["steam_patch"]) if cfg["steam_patch"] else None
    if patch:
        return True, "점검·패치노트 " + ("전체" if patch is True else f"'{patch}'"), [], False
    if excluded:
        return False, f"제외 단어 '{excluded}'", [], False
    kw = contains_any(title, cfg["steam_keywords"]) if cfg["steam_keywords"] else None
    if kw:
        return True, "키워드 " + ("전체" if kw is True else f"'{kw}'"), [], False
    return False, "해당 없음", [], False


def news_embed(item, text, season_news=False):
    embed = {
        "title": _clip(item.get("title", "(제목 없음)"), 256),
        "url": item.get("url"),
        "description": _clip(text, PREVIEW_CHARS),
        "color": COLOR_SEASON if season_news else COLOR_NEWS,
        "footer": {"text": "이터널 리턴 · Steam 공지"},
    }
    if item.get("date"):
        embed["timestamp"] = datetime.fromtimestamp(item["date"], tz=timezone.utc).isoformat()
    img = first_image(item.get("contents"))
    if img:
        embed["image"] = {"url": img}
    return embed


def coupon_embed(coupons):
    lines = []
    for c in coupons:
        lines.append(f"```\n{c['code']}\n```")
        if c["reward"]:
            lines.append(f"**보상** {c['reward']}")
        if c["valid"]:
            lines.append(f"**기한** {c['valid']}")
        lines.append("")
    lines.append("입력: 게임 안 [옵션] → [서비스] → [쿠폰]")
    return {
        "title": "🎁 새 쿠폰 코드",
        "description": _clip("\n".join(lines), 4000),
        "color": COLOR_COUPON,
    }


def build_news_payload(item, coupons, seen_videos, mention="", season_news=False):
    """공지 1개 → (디스코드 JSON, 같이 보낸 영상 ID)."""
    raw = item.get("contents", "")
    text = bbcode_to_text(raw)
    videos = [v for v in youtube_ids_in(raw) if v not in seen_videos][:MAX_VIDEOS_PER_POST]

    payload = {"username": BOT_NAME, "embeds": [], "allowed_mentions": {"parse": []}}
    content = []
    if coupons:
        codes = ", ".join(f"`{c['code']}`" for c in coupons)
        content.append(f"{mention} 🎁 새 쿠폰: {codes}".strip())
        payload["embeds"].append(coupon_embed(coupons))
        if mention:
            payload["allowed_mentions"] = {"parse": ["everyone", "roles"]}
    elif season_news:
        content.append("🌟 새 시즌 소식")
    if videos:
        content += [watch_url(v) for v in videos]  # 링크를 본문에 넣으면 디스코드가 플레이어로 펼쳐 줌
    if content:
        payload["content"] = "\n".join(content)
    payload["embeds"].append(news_embed(item, text, season_news))
    return payload, videos


def run_steam(state, deliver, cfg, mode="normal", data=None):
    items = fetch_news()
    if data is not None:
        collect_steam(data, items)
    if not items:
        print("Steam: 가져온 공지가 없어요.")
        return

    if state.get("steam_source") != STEAM_SOURCE:
        # 처음이거나 공지 소스가 바뀜: 지금 있는 공지는 '이미 본 것'으로 기록만 (채널 도배 방지)
        state["seen_gids"] = []
        state["steam_ready"] = False
    if not state["steam_ready"]:
        state["season"] = initial_season(items)
        if mode == "normal":
            for i in items:
                raw = i.get("contents", "")
                state["seen_gids"].append(i["gid"])
                state["seen_codes"] += [c["code"] for c in extract_coupons(bbcode_to_text(raw))]
                state["seen_videos"] += youtube_ids_in(raw)
            state["steam_ready"] = True
            state["steam_source"] = STEAM_SOURCE
            print(f"Steam 첫 실행: 기존 공지 {len(items)}개는 기록만 했어요. "
                  f"(현재 시즌 {state['season']['num']}) 다음 공지부터 알림이 가요.")
            return

    if mode == "check":
        season = copy.deepcopy(state["season"])
        print(f"── Steam 공지 (현재 시즌 {season['num']}, 새 시즌 소식 기간 {cfg['window_days']}일)")
        for i in items:
            send, why, _, _ = decide_steam(i, season, cfg, set())
            day = datetime.fromtimestamp(i["date"], tz=timezone.utc).strftime("%m-%d")
            print(f"  {'✅ 보냄  ' if send else '⏭  건너뜀'} {day} {i['title']}   ({why})")
        return

    if mode == "test":
        season = copy.deepcopy(state["season"])
        decided = [(i, decide_steam(i, season, cfg, set())) for i in items]
        picked = [(i, d) for i, d in decided if d[0]] or decided
        item, (_, why, coupons, season_news) = picked[-1]
        payload, _ = build_news_payload(item, coupons, set(), cfg["mention"], season_news)
        deliver(payload)
        print(f"Steam 테스트 전송: {item['title']} ({why})")
        return

    seen_gids = set(state["seen_gids"])
    seen_codes = set(state["seen_codes"])
    seen_videos = set(state["seen_videos"])
    new_items = [i for i in items if i["gid"] not in seen_gids]
    for item in new_items:
        send, why, coupons, season_news = decide_steam(item, state["season"], cfg, seen_codes)
        if send:
            payload, videos = build_news_payload(item, coupons, seen_videos, cfg["mention"], season_news)
            deliver(payload)
            state["seen_videos"] += videos
            seen_videos.update(videos)
            codes = [c["code"] for c in coupons]
            state["seen_codes"] += codes
            seen_codes.update(codes)
            print(f"Steam 전송: {item['title']} ({why})")
            time.sleep(1)
        else:
            print(f"Steam 건너뜀: {item['title']} ({why})")
        state["seen_gids"].append(item["gid"])
    if not new_items:
        print("Steam: 새 공지 없음.")


# ---------------------------------------------------------------- 유튜브


_CHANNEL_ID_RE = re.compile(r"^UC[\w-]{22}$")


def resolve_channel_id(spec, cache):
    """채널 주소/@핸들/채널 ID → UC로 시작하는 채널 ID. 찾은 값은 cache(state)에 저장."""
    spec = spec.strip()
    if _CHANNEL_ID_RE.match(spec):
        return spec
    m = re.search(r"/channel/(UC[\w-]{22})", spec)
    if m:
        return m.group(1)
    key = re.sub(r"/(?:featured|videos|shorts|streams|about)/?$", "", spec.rstrip("/"))
    if key in cache:
        return cache[key]

    if key.startswith("http"):
        url = key
    else:
        url = "https://www.youtube.com/" + (key if key.startswith("@") else "@" + key)
    page = http_get(url).decode("utf-8", "replace")
    for pattern in (
        r'<link rel="canonical" href="https://www\.youtube\.com/channel/(UC[\w-]{22})"',
        r'"externalId":"(UC[\w-]{22})"',
        r'<meta itemprop="(?:channelId|identifier)" content="(UC[\w-]{22})"',
    ):
        m = re.search(pattern, page)
        if m:
            cache[key] = m.group(1)
            return m.group(1)
    raise RuntimeError("채널 ID를 찾지 못했어요. 채널 주소를 다시 확인하거나 UC로 시작하는 채널 ID를 넣어 주세요.")


def parse_youtube_feed(xml_bytes):
    root = ET.fromstring(xml_bytes)
    channel = root.findtext("a:title", default="", namespaces=NS)
    videos = []
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", default="", namespaces=NS)
        if not vid:
            continue
        title = e.findtext("a:title", default="", namespaces=NS)
        link = e.find("a:link[@rel='alternate']", NS)
        href = link.get("href") if link is not None else watch_url(vid)
        videos.append({
            "id": vid,
            "title": title,
            "description": e.findtext("media:group/media:description", default="", namespaces=NS),
            "url": href,
            "published": e.findtext("a:published", default="", namespaces=NS),
            "channel": e.findtext("a:author/a:name", default=channel, namespaces=NS) or channel,
            "is_short": "/shorts/" in href or "#shorts" in title.lower(),
        })
    return sorted(videos, key=lambda v: v["published"])


def fetch_videos(channel_id):
    return parse_youtube_feed(http_get(YOUTUBE_FEED_URL.format(channel_id)))


def decide_video(video, cfg):
    if video["is_short"] and not cfg["shorts"]:
        return False, "쇼츠 제외"
    ex = contains_any(video["title"], cfg["yt_exclude"]) if cfg["yt_exclude"] else None
    if ex:
        return False, f"제외 단어 '{ex}'"
    kw = contains_any(video["title"] + "\n" + video.get("description", ""), cfg["yt_keywords"]) if cfg["yt_keywords"] else None
    if kw:
        return True, "키워드 " + ("전체" if kw is True else f"'{kw}'")
    return False, "해당 없음"


def video_payload(video, coupons=None, mention=""):
    kind = "쇼츠" if video["is_short"] else "영상"
    head = f"📺 **{_clip(video['channel'], 80)}** 새 {kind}\n{_clip(video['title'], 300)}\n{video['url']}"
    if not coupons:
        return {"username": BOT_NAME, "content": head, "allowed_mentions": {"parse": []}}
    codes = ", ".join(f"`{c['code']}`" for c in coupons)
    return {
        "username": BOT_NAME,
        "content": f"{mention} 🎁 새 쿠폰: {codes}".strip() + "\n" + head,
        "embeds": [coupon_embed(coupons)],
        "allowed_mentions": {"parse": ["everyone", "roles"]} if mention else {"parse": []},
    }


def video_coupons(video, seen_codes=()):
    return [c for c in extract_coupons(video.get("description", "")) if c["code"] not in seen_codes]


def run_youtube(state, deliver, cfg, mode="normal", data=None, notify=True):
    """채널 하나가 실패해도 나머지는 계속한다.
    notify=False: 유튜브는 Worker가 따로 보내는 중 → 여기서는 기록과 모음 데이터만 (보내지 않음)."""
    for spec in cfg["channels"]:
        try:
            cid = resolve_channel_id(spec, state["yt_ids"])
            videos = fetch_videos(cid)
            if data is not None:
                collect_youtube(data, videos, cfg)
        except Exception as e:  # 유튜브 RSS는 가끔 일시적으로 실패함 → 다음 실행 때 다시 시도
            print(f"[경고] 유튜브 {spec}: {e}")
            continue
        if not videos:
            print(f"유튜브 {spec}: 영상이 없어요.")
            continue
        name = videos[-1]["channel"]

        if mode == "check":
            print(f"── 유튜브 {name} (최근 {len(videos)}개)" + ("" if notify else "  ※ 전송은 명령어 봇(Worker)이 유튜브 채널로 함"))
            for v in videos:
                send, why = decide_video(v, cfg)
                cs = video_coupons(v)
                if cs:
                    send, why = True, "쿠폰 " + ", ".join(c["code"] for c in cs)
                kind = "쇼츠" if v["is_short"] else "영상"
                print(f"  {'✅ 보냄  ' if send else '⏭  건너뜀'} {v['published'][5:10]} [{kind}] {v['title']}   ({why})")
            continue

        if mode == "test":
            if not notify:
                print(f"유튜브 테스트 건너뜀: {name} 영상은 명령어 봇(Worker)이 유튜브 채널로 보내고 있어요.")
                continue
            picked = [v for v in videos if decide_video(v, cfg)[0]] or videos
            deliver(video_payload(picked[-1]))
            print(f"유튜브 테스트 전송: {name} - {picked[-1]['title']}")
            continue

        seen = set(state["seen_videos"])
        if not notify:
            state["seen_videos"] += [v["id"] for v in videos if v["id"] not in seen]
            state["seen_codes"] += [c["code"] for v in videos for c in video_coupons(v, set(state["seen_codes"]))]
            if cid not in state["yt_ready"]:
                state["yt_ready"].append(cid)
            print(f"유튜브 {name}: 명령어 봇(Worker)이 보내는 중이라 기록만 했어요.")
            continue
        if cid not in state["yt_ready"]:
            # 이 채널은 처음: 지금 있는 영상은 기록만
            state["seen_videos"] += [v["id"] for v in videos if v["id"] not in seen]
            state["seen_codes"] += [c["code"] for v in videos for c in video_coupons(v)]
            state["yt_ready"].append(cid)
            print(f"유튜브 첫 확인: {name} 영상 {len(videos)}개는 기록만 했어요.")
            continue

        new = 0
        for v in videos:
            if v["id"] in seen:
                continue
            send, why = decide_video(v, cfg)
            coupons = video_coupons(v, set(state["seen_codes"]))
            if coupons:  # 쇼츠 설명에 쿠폰이 있으면 필터와 상관없이 보냄
                send, why = True, "쿠폰 " + ", ".join(c["code"] for c in coupons)
                state["seen_codes"] += [c["code"] for c in coupons]
            if send:
                deliver(video_payload(v, coupons, cfg["mention"]))
                print(f"유튜브 전송: {name} - {v['title']} ({why})")
                new += 1
                time.sleep(1)
            else:
                print(f"유튜브 건너뜀: {v['title']} ({why})")
            state["seen_videos"].append(v["id"])
            seen.add(v["id"])
        if not new:
            print(f"유튜브 {name}: 보낼 새 영상 없음.")


# ---------------------------------------------------------------- 명령어용 모음 데이터 (data.json)


def parse_expiry(text, posted_ts=None):
    """'2026.11.10(화) 23:59 (KST)까지', '10월 19일 05:00 (KST)까지', '~ 2026년 11월 26일(목) 점검 전까지'
    같은 기한 문장 → 유닉스 시각. 시간이 없으면 그날 23:59, 못 읽으면 None."""
    if not text:
        return None
    posted = datetime.fromtimestamp(posted_ts, KST) if posted_ts else datetime.now(KST)
    m = re.search(r"(20\d{2})\s*(?:[./-]|년)\s*(\d{1,2})\s*(?:[./-]|월)\s*(\d{1,2})", text)
    has_year = bool(m)
    if m:
        y, mo, d = map(int, m.groups())
    else:
        m = re.search(r"(\d{1,2})\s*월\s*(\d{1,2})\s*일", text) or re.search(r"(?<![\d.:])(\d{1,2})[./](\d{1,2})(?![\d.:])", text)
        if not m:
            return None
        mo, d = map(int, m.groups())
        y = posted.year
    rest = text[m.end():]
    t = re.search(r"(\d{1,2}):(\d{2})", rest)
    if t:
        hh, mm = int(t.group(1)), int(t.group(2))
    else:
        t = re.search(r"(오전|오후)?\s*(\d{1,2})\s*시", rest)  # '오전 5시까지'
        if t:
            hh, mm = int(t.group(2)) % 12 + (12 if t.group(1) == "오후" else 0), 0
            if not t.group(1) and int(t.group(2)) >= 12:
                hh = int(t.group(2))
        else:
            hh, mm = 23, 59
    tz = timezone.utc if re.search(r"\bUTC\b", text) else KST
    try:
        dt = datetime(y, mo, d, min(hh, 23), min(mm, 59), tzinfo=tz)
    except ValueError:
        return None
    if not has_year and dt < posted - timedelta(days=7):
        dt = dt.replace(year=dt.year + 1)  # 12월 공지에 '1월 5일까지' 같은 경우
    return int(dt.timestamp())


def _upsert(items, key_name, item):
    """같은 키가 있으면 빈 칸만 채우고, 없으면 추가."""
    for old in items:
        if old.get(key_name) == item[key_name]:
            for k, v in item.items():
                if v not in (None, "") and old.get(k) in (None, ""):
                    old[k] = v
            return old
    items.append(item)
    return item


def _learn(data, title):
    extra = data.setdefault("chars_extra", [])
    for n in learn_characters(title):
        if n not in CHARACTERS and n not in extra:
            extra.append(n)


def collect_steam(data, items):
    for i in items:
        title, raw, gid = i["title"], i.get("contents", ""), i["gid"]
        text = bbcode_to_text(raw)
        _learn(data, title)
        for c in extract_coupons(text):
            _upsert(data["coupons"], "code", {
                "code": c["code"], "reward": c["reward"], "valid": c["valid"],
                "expires": parse_expiry(c["valid"], i["date"]),
                "date": i["date"], "title": title, "url": i["url"],
            })
        if "스킨" in title and not any(w in title for w in SKIN_NOTICE_EXCLUDE):
            _upsert(data["skins"], "id", {
                "id": f"steam:{gid}", "title": title, "url": i["url"], "date": i["date"],
                "source": "steam", "kind": "공지", "text": _clip(text, 300),
            })
        kind = "핫픽스" if "핫픽스" in title else "패치노트" if re.search(r"패치\s*노트", title) else None
        if kind:
            _upsert(data["patches"], "id", {"id": gid, "title": title, "url": i["url"], "date": i["date"], "kind": kind})
        for vid in youtube_ids_in(raw):
            _upsert(data["videos"], "id", {
                "id": vid, "title": title, "url": watch_url(vid), "date": i["date"], "kind": "영상", "source": "steam",
            })


def _iso_ts(s):
    try:
        return int(datetime.fromisoformat(s).timestamp())
    except (TypeError, ValueError):
        return 0


def collect_youtube(data, videos, cfg):
    for v in videos:
        _learn(data, v["title"])
        kind = "쇼츠" if v["is_short"] else "영상"
        date = _iso_ts(v["published"])
        for c in video_coupons(v):
            _upsert(data["coupons"], "code", {
                "code": c["code"], "reward": c["reward"], "valid": c["valid"],
                "expires": parse_expiry(c["valid"], date),
                "date": date, "title": v["title"], "url": v["url"],
            })
        if decide_video(v, cfg)[0]:
            entry = {"id": v["id"], "title": v["title"], "url": v["url"], "date": date, "kind": kind, "source": "youtube"}
            old = _upsert(data["videos"], "id", entry)
            if old.get("source") == "steam":  # Steam 공지 제목 대신 실제 영상 제목으로
                old.update(entry)
        excluded = contains_any(v["title"], cfg["yt_exclude"]) if cfg["yt_exclude"] else None
        if is_skin_video(v["title"], v.get("description", "")) and not excluded:
            _upsert(data["skins"], "id", {
                "id": f"yt:{v['id']}", "title": v["title"], "url": v["url"], "date": date,
                "source": "youtube", "kind": kind, "text": _clip(v.get("description", ""), 300),
            })


def load_data():
    data = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    for key in DATA_LIMITS:
        data.setdefault(key, [])
    data.setdefault("chars_extra", [])
    return data


def tag_characters(data):
    """스킨 항목마다 캐릭터 이름 붙이기 (제목에 있으면 제목 기준, 없으면 본문/설명에서)."""
    extra = data.setdefault("chars_extra", [])
    for s in data["skins"]:
        names = extract_characters(s.get("title"), extra)
        if not names:
            names = extract_characters(s.get("text"), extra, limit=2)
        s["chars"] = names


def save_data(data, state):
    """내용이 바뀌었을 때만 저장 (30분마다 쓸데없는 커밋 방지)."""
    tag_characters(data)
    out = {"season": state.get("season"), "chars_extra": data.get("chars_extra", [])}
    for key, limit in DATA_LIMITS.items():
        out[key] = sorted(data[key], key=lambda x: x.get("date") or 0, reverse=True)[:limit]
    old = json.loads(DATA_FILE.read_text(encoding="utf-8")) if DATA_FILE.exists() else {}
    old.pop("updated", None)
    if old == out:
        return False
    out = {"updated": int(time.time()), **out}
    DATA_FILE.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return True


# ---------------------------------------------------------------- 명령어 봇(Worker) 연동


def worker_base(url):
    url = (url or "").strip().rstrip("/")
    for tail in ("/coupons.json", "/youtube"):
        if url.endswith(tail):
            url = url[: -len(tail)]
    return url


def fetch_worker(cfg):
    """Worker의 /coupons.json → {"coupons": [직접 등록한 쿠폰], "youtube": 유튜브 알림 켜짐 여부}. 실패하면 None."""
    if not cfg["worker_url"]:
        return None
    try:
        info = json.loads(http_get(cfg["worker_url"] + "/coupons.json", retries=2))
        return info if isinstance(info, dict) else None
    except Exception as e:
        print(f"[경고] 명령어 봇(Worker) 확인 실패: {e}")
        return None


def merge_manual_coupons(data, manual):
    """/쿠폰추가 로 직접 등록한 쿠폰을 data.json 쿠폰 목록에 합침 (마감 알림용).
    Worker에서 지운 쿠폰은 여기서도 지움. 공지에서 모은 같은 코드가 있으면 빈 칸만 채움."""
    manual = [m for m in manual or [] if isinstance(m, dict) and re.fullmatch(r"[A-Za-z0-9]{4,30}", str(m.get("code", "")))]
    keep = {m["code"].upper() for m in manual}
    data["coupons"] = [c for c in data["coupons"] if c.get("source") != "manual" or c["code"].upper() in keep]
    for m in manual:
        entry = {
            "code": m["code"], "reward": m.get("reward"), "valid": m.get("valid"),
            "expires": int(m["expires"]) if m.get("expires") else None,
            "date": int(m.get("date") or time.time()), "title": "직접 등록", "url": None,
            "source": "manual", "by": m.get("by"),
        }
        old = next((c for c in data["coupons"] if c["code"].upper() == m["code"].upper()), None)
        if old is None:
            data["coupons"].append(entry)
        elif old.get("source") == "manual":
            old.clear()
            old.update(entry)
        else:
            for k in ("reward", "valid", "expires"):
                if entry[k] and not old.get(k):
                    old[k] = entry[k]
    return len(manual)


def youtube_notify(cfg, info, state):
    """여기(GitHub 봇)서 유튜브 알림을 보낼지. auto면 Worker가 유튜브를 맡고 있을 땐 안 보냄."""
    mode = cfg["yt_notify"]
    if mode in ("off", "false", "0", "no"):
        return False
    if mode in ("on", "true", "1", "yes") or not cfg["worker_url"]:
        return True
    if info is not None:
        state["worker_youtube"] = bool(info.get("youtube"))
    return not state.get("worker_youtube", False)  # Worker 확인이 잠깐 실패하면 지난번 상태대로


# ---------------------------------------------------------------- 쿠폰 마감 알림


def due_reminders(state, data, hours, now=None):
    """마감까지 hours 시간 이내로 남았고 아직 안 알린 쿠폰.
    처음부터 마감이 코앞인 쿠폰(공지 후 hours×1.5 시간 안에 끝나는 것)은 새 쿠폰 알림과 겹치니 뺌."""
    if hours <= 0:
        return []
    now = now or time.time()
    done = set(state["reminded"])
    due = [
        c for c in data.get("coupons", [])
        if c.get("expires") and now < c["expires"] <= now + hours * 3600
        and c["code"] not in done
        and c["expires"] - (c.get("date") or 0) > hours * 3600 * 1.5
    ]
    return sorted(due, key=lambda c: c["expires"])


def reminder_payload(c, mention="", now=None):
    now = now or time.time()
    left = max(1, round((c["expires"] - now) / 3600))
    lines = [f"```\n{c['code']}\n```"]
    if c.get("reward"):
        lines.append(f"**보상** {c['reward']}")
    lines.append(f"**마감** <t:{c['expires']}:f> (<t:{c['expires']}:R>)")
    if c.get("url"):
        lines.append(f"[{'영상 보기' if 'youtu' in c['url'] else '공지 보기'}]({c['url']})")
    lines.append("입력: 게임 안 [옵션] → [서비스] → [쿠폰]")
    return {
        "username": BOT_NAME,
        "content": f"{mention} ⏰ 쿠폰 마감 {left}시간 전: `{c['code']}`".strip(),
        "embeds": [{"title": "⏰ 쿠폰 마감 임박", "description": "\n".join(lines), "color": COLOR_COUPON}],
        "allowed_mentions": {"parse": ["everyone", "roles"]} if mention else {"parse": []},
    }


def run_coupon_reminders(state, data, deliver, cfg, mode="normal", now=None):
    due = due_reminders(state, data, cfg["remind_hours"], now)
    if mode == "check":
        print(f"── 쿠폰 마감 알림 ({cfg['remind_hours']}시간 전)")
        for c in due:
            print(f"  ⏰ 보낼 예정  {c['code']}  (마감 {datetime.fromtimestamp(c['expires'], KST):%m-%d %H:%M})")
        if not due:
            print("  마감이 임박한 쿠폰 없음")
        return
    if mode == "test":
        return
    for c in due:
        deliver(reminder_payload(c, cfg["mention"], now))
        state["reminded"].append(c["code"])
        print(f"쿠폰 마감 알림: {c['code']}")
        time.sleep(1)


# ---------------------------------------------------------------- 보내기 / 기록


def send_webhook(url, payload):
    data = json.dumps(payload).encode("utf-8")
    for _ in range(5):
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": DISCORD_USER_AGENT},
        )
        try:
            with urllib.request.urlopen(req, timeout=20):
                return
        except urllib.error.HTTPError as e:
            body = e.read()
            if e.code == 429:  # 너무 빨리 보냄 → 디스코드가 알려준 시간만큼 대기
                try:
                    wait = float(json.loads(body or b"{}").get("retry_after", 1))
                except ValueError:
                    wait = 2.0
                time.sleep(wait + 0.5)
                continue
            raise RuntimeError(f"웹훅 전송 실패 (HTTP {e.code}): {body[:300]!r}") from None
    raise RuntimeError("웹훅 전송 실패: 재시도 횟수 초과")


def load_state():
    state = json.loads(STATE_FILE.read_text(encoding="utf-8")) if STATE_FILE.exists() else {}
    state.setdefault("steam_ready", False)
    state.setdefault("steam_source", None)
    state.setdefault("season", {"num": 0, "since": 0})
    for key in ("seen_gids", "seen_codes", "seen_videos", "yt_ready", "reminded"):
        state.setdefault(key, [])
    state.setdefault("yt_ids", {})
    return state


def save_state(state):
    for key in ("seen_gids", "seen_codes", "seen_videos", "reminded"):
        state[key] = list(dict.fromkeys(state[key]))[-MAX_SEEN:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config():
    channels_raw = setting("YOUTUBE_CHANNELS")
    try:
        remind = max(0, int(setting("COUPON_REMIND_HOURS")))
    except ValueError:
        remind = 24
    try:
        window = int(setting("SEASON_WINDOW_DAYS"))
    except ValueError:
        window = 21
    return {
        "mention": os.environ.get("MENTION", "").strip(),
        "steam_keywords": keyword_list("STEAM_KEYWORDS"),
        "steam_patch": keyword_list("STEAM_PATCH_KEYWORDS"),
        "steam_exclude": keyword_list("STEAM_EXCLUDE"),
        "window_days": window,
        "channels": [] if channels_raw.lower() in ("off", "none", "-") else _split_list(channels_raw),
        "yt_keywords": keyword_list("YOUTUBE_KEYWORDS"),
        "yt_exclude": keyword_list("YOUTUBE_EXCLUDE"),
        "shorts": setting("YOUTUBE_SHORTS").lower() not in ("off", "false", "0", "no"),
        "remind_hours": remind,
        "worker_url": worker_base(os.environ.get("WORKER_URL", "")),
        "yt_notify": setting("YOUTUBE_NOTIFY").lower(),
    }


# ---------------------------------------------------------------- 실행


def main(argv=None):
    ap = argparse.ArgumentParser(description="이터널 리턴 스킨·새 시즌·쿠폰 디스코드 알림")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="보냄/건너뜀 목록만 출력")
    group.add_argument("--test", action="store_true", help="필터를 통과하는 최신 공지 1개 + 영상 1개를 강제로 전송")
    ap.add_argument("--dry-run", action="store_true", help="전송하지 않고 내용만 출력")
    args = ap.parse_args(argv)
    mode = "check" if args.check else "test" if args.test else "normal"

    webhook = os.environ.get("DISCORD_WEBHOOK_URL", "").strip()
    if not webhook and not (args.dry_run or args.check):
        sys.exit("DISCORD_WEBHOOK_URL 환경 변수가 비어 있어요. (--check, --dry-run 은 없이도 실행돼요)")
    cfg = load_config()

    def deliver(payload):
        if args.dry_run:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            send_webhook(webhook, payload)

    state = load_state()
    data = load_data()
    steam_error = None
    try:
        try:
            run_steam(state, deliver, cfg, mode, data)
        except Exception as e:
            steam_error = e
            print(f"[오류] Steam: {e}")
        info = fetch_worker(cfg)
        if info is not None:
            n = merge_manual_coupons(data, info.get("coupons"))
            if mode == "check":
                print(f"── 명령어 봇(Worker): 직접 등록 쿠폰 {n}개, 유튜브 알림 {'Worker가 보냄' if info.get('youtube') else '꺼짐'}")
        run_coupon_reminders(state, data, deliver, cfg, mode)
        if cfg["channels"]:
            run_youtube(state, deliver, cfg, mode, data, notify=youtube_notify(cfg, info, state))
    finally:
        if mode == "normal" and not args.dry_run:
            save_state(state)
            if save_data(data, state):
                print("data.json 갱신 (명령어 봇용 모음 데이터)")

    if steam_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
