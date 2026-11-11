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
- 유튜브 이터널 리턴 한국 채널 (쇼츠 포함)
  · 제목/설명에 스킨·시즌·미리보기·찾아옵니다 가 있는 영상만
  · KEL·마스터즈 같은 대회 영상은 제외
- 보낸 기록은 state.json에 저장 (중복 방지)
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
  YOUTUBE_EXCLUDE       제목에 이 단어가 있으면 건너뜀 (기본: KEL,마스터즈,서포트 패키지,비하인드)
  YOUTUBE_SHORTS        off면 쇼츠 제외 (기본: 쇼츠 포함)

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
from datetime import datetime, timezone
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
    "YOUTUBE_EXCLUDE": "KEL,마스터즈,서포트 패키지,비하인드",
    "YOUTUBE_SHORTS": "on",
}

STATE_FILE = Path(__file__).with_name("state.json")
USER_AGENT = "Mozilla/5.0 (compatible; ER-News-Discord-Bot/1.2)"
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


# "쿠폰 코드 : SEASON13GLORY" / "Coupon Code: ERVALENTINE" 형태. 코드는 대문자+숫자만 인정.
_CODE_RE = re.compile(
    r"(?i:coupon\s*code|쿠폰\s*(?:코드|번호))\s*[:：]\s*([A-Z0-9]{4,30})(?![A-Za-z0-9])"
)
_REWARD_RE = re.compile(r"^(?:쿠폰\s*)?(?:rewards?|보상|리워드)\s*[:：]\s*(.+)$", re.I)
_VALID_RE = re.compile(
    r"^(?:쿠폰\s*)?(?:valid\s*(?:thru|through|until)|expires?|expiration|사용\s*기간|유효\s*기간|기한)\s*[:：]\s*(.+)$",
    re.I,
)


def extract_coupons(text):
    """본문에서 쿠폰 코드와 바로 뒤의 보상/기한 줄을 묶어서 뽑는다."""
    coupons = []
    current = None
    for line in text.splitlines():
        line = line.strip().lstrip("-•*·▶■◆ ").strip()
        if not line:
            continue
        m = _CODE_RE.search(line)
        if m:
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


def run_steam(state, deliver, cfg, mode="normal"):
    items = fetch_news()
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


def video_payload(video):
    kind = "쇼츠" if video["is_short"] else "영상"
    return {
        "username": BOT_NAME,
        "content": f"📺 **{_clip(video['channel'], 80)}** 새 {kind}\n{_clip(video['title'], 300)}\n{video['url']}",
        "allowed_mentions": {"parse": []},
    }


def run_youtube(state, deliver, cfg, mode="normal"):
    """채널 하나가 실패해도 나머지는 계속한다."""
    for spec in cfg["channels"]:
        try:
            cid = resolve_channel_id(spec, state["yt_ids"])
            videos = fetch_videos(cid)
        except Exception as e:  # 유튜브 RSS는 가끔 일시적으로 실패함 → 다음 실행 때 다시 시도
            print(f"[경고] 유튜브 {spec}: {e}")
            continue
        if not videos:
            print(f"유튜브 {spec}: 영상이 없어요.")
            continue
        name = videos[-1]["channel"]

        if mode == "check":
            print(f"── 유튜브 {name} (최근 {len(videos)}개)")
            for v in videos:
                send, why = decide_video(v, cfg)
                kind = "쇼츠" if v["is_short"] else "영상"
                print(f"  {'✅ 보냄  ' if send else '⏭  건너뜀'} {v['published'][5:10]} [{kind}] {v['title']}   ({why})")
            continue

        if mode == "test":
            picked = [v for v in videos if decide_video(v, cfg)[0]] or videos
            deliver(video_payload(picked[-1]))
            print(f"유튜브 테스트 전송: {name} - {picked[-1]['title']}")
            continue

        seen = set(state["seen_videos"])
        if cid not in state["yt_ready"]:
            # 이 채널은 처음: 지금 있는 영상은 기록만
            state["seen_videos"] += [v["id"] for v in videos if v["id"] not in seen]
            state["yt_ready"].append(cid)
            print(f"유튜브 첫 확인: {name} 영상 {len(videos)}개는 기록만 했어요.")
            continue

        new = 0
        for v in videos:
            if v["id"] in seen:
                continue
            send, why = decide_video(v, cfg)
            if send:
                deliver(video_payload(v))
                print(f"유튜브 전송: {name} - {v['title']} ({why})")
                new += 1
                time.sleep(1)
            else:
                print(f"유튜브 건너뜀: {v['title']} ({why})")
            state["seen_videos"].append(v["id"])
            seen.add(v["id"])
        if not new:
            print(f"유튜브 {name}: 보낼 새 영상 없음.")


# ---------------------------------------------------------------- 보내기 / 기록


def send_webhook(url, payload):
    data = json.dumps(payload).encode("utf-8")
    for _ in range(5):
        req = urllib.request.Request(
            url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json", "User-Agent": USER_AGENT},
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
    for key in ("seen_gids", "seen_codes", "seen_videos", "yt_ready"):
        state.setdefault(key, [])
    state.setdefault("yt_ids", {})
    return state


def save_state(state):
    for key in ("seen_gids", "seen_codes", "seen_videos"):
        state[key] = list(dict.fromkeys(state[key]))[-MAX_SEEN:]
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_config():
    channels_raw = setting("YOUTUBE_CHANNELS")
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
    steam_error = None
    try:
        try:
            run_steam(state, deliver, cfg, mode)
        except Exception as e:
            steam_error = e
            print(f"[오류] Steam: {e}")
        if cfg["channels"]:
            run_youtube(state, deliver, cfg, mode)
    finally:
        if mode == "normal" and not args.dry_run:
            save_state(state)

    if steam_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
