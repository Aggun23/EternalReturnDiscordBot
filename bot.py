#!/usr/bin/env python3
"""
이터널 리턴 소식 → 디스코드 알림 (스킨 · 새 시즌 · 쿠폰 · 점검 · 패치노트)

- 공식 홈페이지(playeternalreturn.com) 패치노트 게시판
  · 패치노트, 핫픽스 → 패치 채널로 보냄
  · 공식 홈페이지가 2시간 넘게 안 열리면 그동안만 Steam 패치노트 공지로 대신 (같은 패치를 두 번 보내지 않음)
- Steam 한국어 공지 (상점 뉴스 페이지와 같은 데이터)
  · 쿠폰 코드가 있는 공지 → 항상 보냄 (코드를 따로 강조)
  · 서버 점검 안내/완료 → 패치 채널로 보냄
  · 제목에 '스킨'이 있는 공지 → 보냄
  · 새 시즌 번호(예: 시즌 14)가 처음 나온 날부터 3주 동안, 그 시즌 공지 → 보냄
  · 나머지(이모티콘, 만화, 당첨자 발표 등) → 건너뜀
  · 공지에 유튜브 영상이 붙어 있으면 링크를 같이 보내서 디스코드에서 바로 재생
- 쿠폰 마감 24시간 전에 한 번 더 알림 (기한을 읽을 수 있는 쿠폰만)
- 유튜브 이터널 리턴 한국 채널 (쇼츠 포함)
  · 쇼츠/영상 설명에 쿠폰 코드가 있으면 필터와 상관없이 보냄 (시즌 D-7, D-3 쇼츠 쿠폰 등)
  · 제목/설명에 스킨·시즌·미리보기·찾아옵니다 가 있는 영상만
  · KEL·마스터즈 같은 대회 영상은 제외
  · 스킨 영상은 스킨 채널로, 나머지(시즌 영상·쿠폰 있는 영상)는 유튜브 채널로
- 명령어 봇(Worker)에서 /쿠폰추가 로 직접 등록한 쿠폰도 마감 알림 (WORKER_URL 설정 시)
- 보낸 기록은 state.json에 저장 (중복 방지)
- 디스코드 명령어 봇(worker.js)이 읽을 모음 데이터는 data.json에 저장
  (쿠폰과 기한, 스킨 공지·쇼츠, 패치노트·핫픽스, 스킨·시즌 영상)
- 표준 라이브러리만 사용 → pip install 필요 없음

사용법
  python bot.py              평소 실행 (새 글/영상만 전송)
  python bot.py --check      지금 올라와 있는 공지/영상이 필터에서 보냄/건너뜀 중 무엇인지 목록만 출력
  python bot.py --test       최신 패치노트 1개 + 필터를 통과하는 최신 공지 1개 + 영상 1개를 강제로 전송
  python bot.py --dry-run    디스코드로 보내지 않고 보낼 내용만 출력

환경 변수 (보낼 곳: DISCORD_CHANNEL_ID + DISCORD_BOT_TOKEN, 또는 DISCORD_WEBHOOK_URL 중 하나는 필수)
  DISCORD_CHANNEL_ID    알림 채널 ID. DISCORD_BOT_TOKEN과 같이 넣으면 봇 계정으로 직접 올림 (웹후크 대신)
  DISCORD_PATCH_CHANNEL_ID  (선택) 패치노트·핫픽스·점검 전용 채널 ID. 없으면 알림 채널로
  DISCORD_VIDEO_CHANNEL_ID  (선택) 유튜브 알림 채널 ID. 없으면 알림 채널로
  DISCORD_SKIN_CHANNEL_ID   (선택) 유튜브 스킨 영상 전용 채널 ID. 없으면 유튜브 알림 채널로
  DISCORD_WEBHOOK_URL   디스코드 채널 웹후크 주소 (봇 계정으로 올리지 않을 때)
  PATCH_WEBHOOK_URL / YOUTUBE_WEBHOOK_URL / SKIN_WEBHOOK_URL  (선택) 위 전용 채널들을 웹후크로 쓸 때
  PATCH_SOURCE          official(기본) = 패치노트·핫픽스를 공식 홈페이지에서 / steam = 예전처럼 Steam 공지에서
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
  DISCORD_BOT_TOKEN     (선택) 넣으면 알림 글도 개발자 포털의 봇 이름·프로필 사진으로 보냄 (명령어 등록용과 같은 토큰)
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
INNERTUBE_URL = "https://www.youtube.com/youtubei/v1/{}?prettyPrint=false"  # RSS 고장 때 쓰는 예비 경로
INNERTUBE_CLIENT = {"clientName": "WEB", "clientVersion": "2.20261106.00.00", "hl": "ko", "gl": "KR"}
BROWSER_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36"

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
    "PATCH_SOURCE": "official",
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
# 봇 이름·프로필 사진: DISCORD_BOT_TOKEN이 있으면 개발자 포털 Bot 탭의 이름·사진을 그대로 씀 (모든 채널 통일).
# 없으면 각 채널 웹후크에 설정된 이름·사진.
# 공식 홈페이지 패치노트 게시판 (패치노트·핫픽스)
OFFICIAL_NEWS_API = "https://playeternalreturn.com/api/v1/posts/news?category=patchnote&page={}&hl=ko-KR"
OFFICIAL_POST_URL = "https://playeternalreturn.com/posts/news/{}"
OFFICIAL_FALLBACK_AFTER = 4  # 공식 홈페이지가 이만큼 연속으로(30분마다 → 약 2시간) 안 열리면 그동안은 Steam 패치노트로 대신
PATCH_CHANNEL_KINDS = ("maintenance", "maintenance_done", "hotfix", "patch")  # 패치 채널로 보내는 공지 종류

# ---------------------------------------------------------------- 말투 (코렐라인)
# 봇이 하는 말은 전부 여기 모여 있어요. 문구를 고치거나 줄을 더하거나 빼도 돼요.
# - 한 종류에 문구가 여러 개면 소식마다 하나를 골라 써요 (같은 소식엔 늘 같은 문구).
# - {codes} {code} {hours} {channel} {kind} 같은 중괄호 칸은 그 자리에 실제 값이 들어가요. 지우지 마세요.
# - 명령어(/쿠폰 등) 답장 말투는 worker.js 맨 위 TONE 에 있어요.
TONE = {
    # 새 쿠폰 ({codes} = 쿠폰 코드들)
    "coupon": [
        "🎁 내 거울에 새 쿠폰이 비쳤어: {codes}\n진짜냐고? 난 거짓말 안 해. 후후훗.",
        "🎁 반짝이는 걸 찾았어. 새 쿠폰 {codes}\n빛이 꺼지기 전에 얼른 챙겨.",
        "🎁 새 쿠폰이야: {codes}\n알고도 안 쓰면... 그건 유죄지? 후훗.",
    ],
    # 쿠폰 마감 하루 전 ({code} = 쿠폰 코드, {hours} = 남은 시간)
    "remind": [
        "⏰ {code} 쿠폰, 마감까지 {hours}시간 남았어. 빛이 꺼지기 전에 써.",
        "⏰ 마감 {hours}시간 전이야: {code}\n받아 놓고 안 쓰면 유죄야. 후훗.",
    ],
    # Steam 공지 종류별 한마디
    "season": [
        "🌟 새 시즌 소식이야. 새로운 빛이 떠오르려나 봐. 후후훗.",
        "🌟 새 시즌 이야기가 들려왔어. 이번엔 어떤 색일지 궁금하네.",
    ],
    "maintenance": [
        "🧹 점검 소식이야. 섬도 가끔은 깨끗이 닦아 줘야지.",
        "🧹 점검이 있대. 얼룩을 지우는 시간이니까 얌전히 기다려 줘.",
    ],
    "maintenance_done": [
        "✨ 점검이 끝났대. 깨끗해진 섬에서 다시 만나.",
        "✨ 다 닦았나 봐. 이제 돌아와도 돼. 후훗.",
    ],
    "hotfix": [
        "🩹 핫픽스 소식이야. 얼룩은 보이는 대로 바로 닦아야 하는 법이지.",
        "🩹 급하게 고친 게 있대. 뭘 고쳤는지 확인해 볼래?",
    ],
    "patch": [
        "📜 패치노트가 나왔어. 뭐가 바뀌었는지 숨김없이 적혀 있을 거야.",
        "📜 새 패치노트야. 꼼꼼히 읽어 봐. 모르고 당하면 억울하잖아?",
    ],
    "skin": [
        "👗 새 스킨 소식이야. 반짝이는 건 언제든 환영이거든. 후훗.",
        "👗 스킨 소식이 왔어. 예쁜지 아닌지는 내 거울로 직접 확인해 줄게.",
    ],
    # 유튜브 새 영상 ({channel} = 채널 이름, {kind} = "쇼츠가" 또는 "영상이")
    "video": [
        "📺 **{channel}** 채널에 새 {kind} 올라왔어. 같이 볼래? 후훗.",
        "📺 **{channel}** 채널에 새 {kind} 떴어. 놓치지 말고 챙겨 봐.",
    ],
    # 유튜브 스킨 영상 (스킨 채널로 가는 영상. {kind} = "쇼츠가" 또는 "영상이")
    "skin_video": [
        "👗 새 스킨 {kind} 올라왔어. 반짝이는 건 그냥 지나칠 수가 없거든. 후훗.",
        "👗 스킨 {kind} 떴어. 예쁜지 아닌지는 직접 보고 판단해.",
    ],
    # 제목·안내 (하나씩)
    "coupon_title": "🎁 새 쿠폰 코드",
    "remind_title": "⏰ 곧 꺼지는 쿠폰",
    "redeem": "쓰는 곳: 게임 안 [옵션] → [서비스] → [쿠폰]",
}


def say(key, pick_by="", **values):
    """TONE[key]에서 문구 하나를 골라 값을 채움. pick_by가 같으면 늘 같은 문구."""
    options = TONE[key]
    if isinstance(options, str):
        options = [options]
    line = options[sum(map(ord, str(pick_by))) % len(options)]
    for name, value in values.items():
        line = line.replace("{" + name + "}", str(value))
    return line


def send_to(deliver, payload, to="main"):
    """소식 종류에 맞는 채널로 보냄. to = main(알림) / patch(패치노트·핫픽스·점검) / video(유튜브) / skin(유튜브 스킨 영상).
    deliver가 채널 나누기를 지원하면(.route) 그쪽으로, 아니면 그냥 보냄."""
    route = getattr(deliver, "route", None)
    if route:
        route(payload, to)
    else:
        deliver(payload)


_PATCH_KEY_RE = re.compile(r"(\d+\.\d+)\s*([a-z])?\s*(?:패치\s*노트|핫픽스)", re.I)


def patch_key(title):
    """'13.0a 핫픽스' → '13.0a', '2026.10.29 - 12.7 패치노트' → '12.7'. 공식 홈페이지 글과 Steam 공지가 같은 패치인지 볼 때 씀."""
    m = _PATCH_KEY_RE.search(title or "")
    return (m.group(1) + (m.group(2) or "")).lower() if m else None


def notice_kind(title):
    """공지 제목 → 말투 종류 (없으면 None)."""
    if "점검" in title:
        return "maintenance_done" if re.search(r"점검\s*(완료|종료)", title) else "maintenance"
    if "핫픽스" in title:
        return "hotfix"
    if re.search(r"패치\s*노트", title):
        return "patch"
    if "스킨" in title:
        return "skin"
    return None


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
    lines.append(say("redeem"))
    return {
        "title": say("coupon_title"),
        "description": _clip("\n".join(lines), 4000),
        "color": COLOR_COUPON,
    }


def build_news_payload(item, coupons, seen_videos, mention="", season_news=False):
    """공지 1개 → (디스코드 JSON, 같이 보낸 영상 ID)."""
    raw = item.get("contents", "")
    text = bbcode_to_text(raw)
    videos = [v for v in youtube_ids_in(raw) if v not in seen_videos][:MAX_VIDEOS_PER_POST]

    payload = {"embeds": [], "allowed_mentions": {"parse": []}}
    content = []
    title = item.get("title", "")
    kind = notice_kind(title)
    if coupons:
        codes = ", ".join(f"`{c['code']}`" for c in coupons)
        content.append(f"{mention} {say('coupon', coupons[0]['code'], codes=codes)}".strip())
        payload["embeds"].append(coupon_embed(coupons))
        if mention:
            payload["allowed_mentions"] = {"parse": ["everyone", "roles"]}
    elif season_news:  # 제목에 새 시즌 번호가 있는 공지 (예: '시즌 13 …', '13.0 패치노트')
        content.append(say("season", title))
    elif kind:
        content.append(say(kind, title))
    if videos:
        content += [watch_url(v) for v in videos]  # 링크를 본문에 넣으면 디스코드가 플레이어로 펼쳐 줌
    if content:
        payload["content"] = "\n".join(content)
    payload["embeds"].append(news_embed(item, text, season_news))
    return payload, videos


def steam_patch_rule(item, coupons, patch_mode, state):
    """패치노트를 공식 홈페이지에서 받을 때, Steam의 패치노트·핫픽스 공지를 어떻게 할지.
    돌려주는 값: None(평소대로) / ("skip", 이유) / ("defer", 이유) / ("send", 덧붙일 이유)"""
    if patch_mode == "steam" or coupons or notice_kind(item["title"]) not in ("patch", "hotfix"):
        return None
    if patch_mode == "official":
        return "skip", "패치노트는 공식 홈페이지에서 받음"
    if patch_mode == "defer":
        return "defer", "공식 홈페이지가 잠깐 안 열려서 다음에 다시 확인"
    key = patch_key(item["title"])
    if key and f"official:{key}" in state["patch_sent"]:
        return "skip", "공식 홈페이지 패치노트로 이미 보냄"
    return "send", "공식 홈페이지가 계속 안 열려서 Steam 공지로 대신"


def steam_channel(item, coupons):
    """쿠폰이 있으면 알림 채널(모두가 봐야 하니까), 점검·패치노트·핫픽스는 패치 채널."""
    return "patch" if not coupons and notice_kind(item["title"]) in PATCH_CHANNEL_KINDS else "main"


def run_steam(state, deliver, cfg, mode="normal", data=None, patch_mode="steam"):
    """patch_mode: steam = Steam 패치노트도 보냄 / official = 공식 홈페이지에서 받으니 건너뜀 /
    defer = 공식 홈페이지가 잠깐 실패해서 보류 / fallback = 공식 홈페이지가 계속 실패해서 Steam으로 대신"""
    items = fetch_news()
    if data is not None:
        collect_steam(data, items, patches=patch_mode in ("steam", "fallback"))
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
            send, why, cs, _ = decide_steam(i, season, cfg, set())
            rule = steam_patch_rule(i, cs, patch_mode, state) if send else None
            if rule and rule[0] != "send":
                send, why = False, rule[1]
            elif send and steam_channel(i, cs) == "patch":
                why += " → 패치 채널"
            day = datetime.fromtimestamp(i["date"], tz=timezone.utc).strftime("%m-%d")
            print(f"  {'✅ 보냄  ' if send else '⏭  건너뜀'} {day} {i['title']}   ({why})")
        return

    if mode == "test":
        season = copy.deepcopy(state["season"])
        decided = [(i, decide_steam(i, season, cfg, set())) for i in items]
        picked = [(i, d) for i, d in decided
                  if d[0] and (steam_patch_rule(i, d[2], patch_mode, state) or ("send",))[0] == "send"] or decided
        item, (_, why, coupons, season_news) = picked[-1]
        payload, _ = build_news_payload(item, coupons, set(), cfg["mention"], season_news)
        send_to(deliver, payload, steam_channel(item, coupons))
        print(f"Steam 테스트 전송: {item['title']} ({why})")
        return

    seen_gids = set(state["seen_gids"])
    seen_codes = set(state["seen_codes"])
    seen_videos = set(state["seen_videos"])
    new_items = [i for i in items if i["gid"] not in seen_gids]
    for item in new_items:
        send, why, coupons, season_news = decide_steam(item, state["season"], cfg, seen_codes)
        rule = steam_patch_rule(item, coupons, patch_mode, state) if send else None
        if rule:
            action, reason = rule
            if action == "defer":  # 기록하지 않음 → 다음 실행 때 다시 봄
                print(f"Steam 보류: {item['title']} ({reason})")
                continue
            if action == "skip":
                send, why = False, reason
            else:
                why += " · " + reason
                key = patch_key(item["title"])
                if key:
                    state["patch_sent"].append(f"steam:{key}")
        if send:
            payload, videos = build_news_payload(item, coupons, seen_videos, cfg["mention"], season_news)
            send_to(deliver, payload, steam_channel(item, coupons))
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


# ---------------------------------------------------------------- 공식 홈페이지 패치노트


def fetch_official_patches(page=1):
    """공식 홈페이지 패치노트 게시판 목록 (오래된 것부터). 핫픽스도 이 게시판에 올라옴."""
    board = json.loads(http_get(OFFICIAL_NEWS_API.format(page), retries=2))
    items = []
    for a in board.get("articles") or []:
        i18ns = a.get("i18ns") or {}
        loc = i18ns.get("ko_KR") or next(iter(i18ns.values()), None) or {}
        title = (loc.get("title") or "").strip()
        if not title or a.get("is_hidden") or loc.get("is_hidden"):
            continue
        items.append({
            "id": str(a["id"]),
            "title": title,
            "summary": (loc.get("summary") or "").strip(),
            "url": a.get("url") or OFFICIAL_POST_URL.format(a["id"]),
            "date": _iso_ts((a.get("created_at") or "").replace("Z", "+00:00")),
            "image": a.get("thumbnail_url") or None,
        })
    return sorted(items, key=lambda i: (i["date"], int(i["id"]) if i["id"].isdigit() else 0))


def official_preview(url):
    """패치노트 글 본문 앞부분 (글 페이지에서 본문 칸만 뽑아 글자만 남김)."""
    page = http_get(url + ("&" if "?" in url else "?") + "hl=ko-KR", retries=1).decode("utf-8", "replace")
    start = page.find("er-article-detail__content")
    if start < 0:
        return ""
    start = page.find(">", start) + 1
    ends = [pos for pos in (page.find(mark, start) for mark in ("er-article-detail__recent", "er-article-side", "er-recent-articles")) if pos > 0]
    seg = page[start:min(ends + [start + 6000])]
    seg = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", seg)
    seg = re.sub(r"<[^>]*$", "", seg)  # 잘린 태그
    seg = re.sub(r"(?i)<(?:br|/p|/li|/h\d|/div|/tr)[^>]*>", "\n", seg)
    seg = html.unescape(re.sub(r"<[^>]+>", "", seg))
    lines = [re.sub(r"[ \t\u200b\xa0]+", " ", line).strip() for line in seg.split("\n")]
    return "\n".join(line for line in lines if line)


def official_text(item):
    try:
        return official_preview(item["url"]) or item.get("summary", "")
    except Exception as e:
        print(f"[경고] 패치노트 본문 미리보기 실패 ({item['title']}): {e}")
        return item.get("summary", "")


def official_payload(item, text=""):
    kind = "hotfix" if "핫픽스" in item["title"] else "patch"
    embed = {
        "title": _clip(item["title"], 256),
        "url": item["url"],
        "color": COLOR_NEWS,
        "footer": {"text": "이터널 리턴 · 공식 홈페이지"},
    }
    if text:
        embed["description"] = _clip(text, PREVIEW_CHARS)
    if item.get("date"):
        embed["timestamp"] = datetime.fromtimestamp(item["date"], tz=timezone.utc).isoformat()
    if item.get("image"):
        embed["image"] = {"url": item["image"]}
    return {"content": say(kind, item["title"]), "embeds": [embed], "allowed_mentions": {"parse": []}}


def collect_official(data, items):
    """/패치 목록은 공식 홈페이지 글로 채움 (예전에 Steam에서 모은 패치 항목은 뺌)."""
    data["patches"] = [p for p in data["patches"] if str(p.get("id", "")).startswith("official:")]
    for i in items:
        _upsert(data["patches"], "id", {
            "id": f"official:{i['id']}", "title": i["title"], "url": i["url"], "date": i["date"],
            "kind": "핫픽스" if "핫픽스" in i["title"] else "패치노트",
        })


def run_official(state, deliver, cfg, mode="normal", data=None):
    """공식 홈페이지 패치노트·핫픽스 → 패치 채널. 목록을 가져오는 데 성공하면 True."""
    try:
        items = fetch_official_patches()
    except Exception as e:
        if mode == "normal":
            state["official_fail"] += 1
        print(f"[경고] 공식 홈페이지 패치노트를 못 가져왔어요 (연속 {state['official_fail']}번): {e}")
        return False
    if mode == "normal":
        state["official_fail"] = 0
    if data is not None:
        collect_official(data, items)
        if len(data["patches"]) < 30:  # 처음 한 번: /패치 목록용으로 지난 글도 채움
            for page in (2, 3):
                try:
                    collect_official(data, fetch_official_patches(page))
                except Exception as e:
                    print(f"[경고] 공식 홈페이지 지난 패치노트({page}쪽) 실패: {e}")
                    break
    if not items:
        print("공식 홈페이지: 가져온 패치노트가 없어요.")
        return True

    seen = set(state["seen_official"])
    if mode == "check":
        print("── 공식 홈페이지 패치노트·핫픽스 (패치 채널로)" + ("" if state["official_ready"] else "  ※ 첫 실행에서는 기록만 해요"))
        for i in items:
            day = datetime.fromtimestamp(i["date"], tz=timezone.utc).strftime("%m-%d")
            print(f"  {'·  이미 봄 ' if i['id'] in seen else '✅ 보냄  '} {day} {i['title']}")
        return True
    if mode == "test":
        item = items[-1]
        send_to(deliver, official_payload(item, official_text(item)), "patch")
        print(f"공식 패치노트 테스트 전송: {item['title']}")
        return True
    if not state["official_ready"]:
        # 처음: 지금 올라와 있는 글은 기록만 (채널 도배 방지)
        state["seen_official"] += [i["id"] for i in items]
        state["official_ready"] = True
        print(f"공식 홈페이지 첫 확인: 패치노트 {len(items)}개는 기록만 했어요. 다음 글부터 알림이 가요.")
        return True

    new = [i for i in items if i["id"] not in seen]
    for item in new:
        key = patch_key(item["title"])
        if key and f"steam:{key}" in state["patch_sent"]:
            print(f"공식 패치노트 건너뜀: {item['title']} (공식 홈페이지가 안 열리던 동안 Steam 공지로 이미 보냄)")
        else:
            send_to(deliver, official_payload(item, official_text(item)), "patch")
            if key:
                state["patch_sent"].append(f"official:{key}")
            print(f"공식 패치노트 전송: {item['title']}")
            time.sleep(1)
        state["seen_official"].append(item["id"])
    if not new:
        print("공식 홈페이지: 새 패치노트 없음.")
    return True


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


def innertube(endpoint, body):
    req = urllib.request.Request(
        INNERTUBE_URL.format(endpoint),
        data=json.dumps({"context": {"client": INNERTUBE_CLIENT}, **body}).encode("utf-8"),
        method="POST",
        headers={"Content-Type": "application/json", "User-Agent": BROWSER_UA, "Accept-Language": "ko-KR,ko;q=0.9"},
    )
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def _to_utc_iso(s):
    try:
        dt = datetime.fromisoformat(s)
    except (TypeError, ValueError):
        return ""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat()


def fetch_videos_fallback(channel_id, limit=15):
    """RSS가 고장 났을 때: 채널 업로드 목록 + 영상 정보(YouTube 내부 API)로 RSS와 같은 모양의 목록을 만든다."""
    page = innertube("browse", {"browseId": "VLUU" + channel_id[2:]})
    ids = []
    for pattern in (r'"contentId":"([\w-]{11})","contentType":"LOCKUP_CONTENT_TYPE_VIDEO"', r'"videoId":"([\w-]{11})"'):
        for vid in re.findall(pattern, page):
            if vid not in ids:
                ids.append(vid)
            if len(ids) >= limit:
                break
        if ids:
            break
    videos = []
    for vid in ids:
        try:
            pj = json.loads(innertube("player", {"videoId": vid}))
        except Exception as e:
            print(f"[경고] 영상 정보 실패 {vid}: {e}")
            continue
        d = pj.get("videoDetails") or {}
        mf = (pj.get("microformat") or {}).get("playerMicroformatRenderer") or {}
        if d.get("channelId") != channel_id:
            continue
        short = "/shorts/" in (mf.get("canonicalUrl") or "")
        videos.append({
            "id": vid,
            "title": d.get("title", ""),
            "description": d.get("shortDescription", ""),
            "url": f"https://www.youtube.com/shorts/{vid}" if short else watch_url(vid),
            "published": _to_utc_iso(mf.get("publishDate") or mf.get("uploadDate") or ""),
            "channel": d.get("author") or mf.get("ownerChannelName") or "",
            "is_short": short,
        })
    if not videos:
        raise RuntimeError("예비 경로로도 영상 정보를 못 가져왔어요")
    return sorted(videos, key=lambda v: v["published"])


def _worker_video(v):
    """Worker(/coupons.json)의 영상 → RSS와 같은 모양."""
    return {
        "id": v["id"],
        "title": v.get("title") or "",
        "description": v.get("description") or "",
        "url": v.get("url") or watch_url(v["id"]),
        "published": _to_utc_iso(v.get("published") or ""),
        "channel": v.get("author") or "",
        "is_short": bool(v.get("isShort")),
    }


def worker_videos(info, channel_id):
    """명령어 봇(Worker)이 YouTube에서 직접 확인한 새 영상 (GitHub에서 YouTube가 막힐 때 대신 씀)."""
    if not info or info.get("channel") != channel_id:
        return []
    return sorted((_worker_video(v) for v in info.get("videos") or [] if isinstance(v, dict) and v.get("id")),
                  key=lambda v: v["published"])


def fetch_videos(channel_id, worker=None):
    try:
        return parse_youtube_feed(http_get(YOUTUBE_FEED_URL.format(channel_id), retries=2))
    except Exception as e:  # YouTube RSS는 몇 시간씩 404가 나는 일이 잦음
        if worker:
            print(f"[경고] 유튜브 RSS 실패 ({e}) → 명령어 봇(Worker)이 확인한 영상 {len(worker)}개로 대신")
            return worker
        print(f"[경고] 유튜브 RSS 실패 ({e}) → 예비 경로로 확인")
        return fetch_videos_fallback(channel_id)


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


def video_route(video, coupons, cfg):
    """유튜브 영상을 어느 채널로: 쿠폰이 있으면 유튜브 채널(모두가 봐야 하니까), 스킨 영상이면 스킨 채널, 나머지는 유튜브 채널."""
    if coupons:
        return "video"
    excluded = contains_any(video["title"], cfg["yt_exclude"]) if cfg.get("yt_exclude") else None
    return "skin" if not excluded and is_skin_video(video["title"], video.get("description", "")) else "video"


def video_payload(video, coupons=None, mention="", skin=False):
    kind = "쇼츠가" if video["is_short"] else "영상이"
    intro = say("skin_video" if skin and not coupons else "video", video["id"],
                channel=_clip(video["channel"] or "이터널 리턴", 80), kind=kind)
    head = f"{intro}\n{_clip(video['title'], 300)}\n{video['url']}"
    if not coupons:
        return {"content": head, "allowed_mentions": {"parse": []}}
    codes = ", ".join(f"`{c['code']}`" for c in coupons)
    return {
        "content": f"{mention} {say('coupon', coupons[0]['code'], codes=codes)}".strip() + "\n" + head,
        "embeds": [coupon_embed(coupons)],
        "allowed_mentions": {"parse": ["everyone", "roles"]} if mention else {"parse": []},
    }


def video_coupons(video, seen_codes=()):
    return [c for c in extract_coupons(video.get("description", "")) if c["code"] not in seen_codes]


def run_youtube(state, deliver, cfg, mode="normal", data=None, notify=True, info=None):
    """채널 하나가 실패해도 나머지는 계속한다.
    notify=False: 유튜브는 Worker가 따로 보내는 중 → 여기서는 기록과 모음 데이터만 (보내지 않음)."""
    for spec in cfg["channels"]:
        try:
            cid = resolve_channel_id(spec, state["yt_ids"])
            wv = worker_videos(info, cid)
            videos = fetch_videos(cid, wv) if wv else fetch_videos(cid)
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
                if send and video_route(v, cs, cfg) == "skin":
                    why += " → 스킨 채널"
                print(f"  {'✅ 보냄  ' if send else '⏭  건너뜀'} {v['published'][5:10]} [{kind}] {v['title']}   ({why})")
            continue

        if mode == "test":
            if not notify:
                print(f"유튜브 테스트 건너뜀: {name} 영상은 명령어 봇(Worker)이 유튜브 채널로 보내고 있어요.")
                continue
            picked = [v for v in videos if decide_video(v, cfg)[0]] or videos
            to = video_route(picked[-1], [], cfg)
            send_to(deliver, video_payload(picked[-1], skin=to == "skin"), to)
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
                to = video_route(v, coupons, cfg)
                send_to(deliver, video_payload(v, coupons, cfg["mention"], skin=to == "skin"), to)
                print(f"유튜브 전송: {name} - {v['title']} ({why}{' → 스킨 채널' if to == 'skin' else ''})")
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


def collect_steam(data, items, patches=True):
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
        if kind and patches:  # 패치노트를 공식 홈페이지에서 받을 땐 collect_official이 채움
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


def _norm_name(name):
    return re.sub(r"[\s&·]+", "", name or "").lower()


def alias_map():
    """별명 → 캐릭터 이름 ('뎁마' → '데비&마를렌'). 명령어 봇의 /스킨 캐릭터 검색이 씀."""
    return {_norm_name(a): name for name, aliases in _CHAR_ALIASES.items() for a in aliases if _norm_name(a) != _norm_name(name)}


def save_data(data, state):
    """내용이 바뀌었을 때만 저장 (30분마다 쓸데없는 커밋 방지)."""
    tag_characters(data)
    out = {"season": state.get("season"), "chars_extra": data.get("chars_extra", []), "aliases": alias_map()}
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


def run_handoff(state, info, deliver, cfg, mode="normal"):
    """Worker가 디스코드 전송에 30분 넘게 실패해서 넘긴 유튜브 영상을 여기서 대신 보냄.
    (디스코드가 Cloudflare 서버 IP를 잠시 막는 일이 있음. GitHub 서버에서는 보통 됨)"""
    done = set(state["handoff_sent"])
    todo = [v for v in (info or {}).get("unsent") or [] if isinstance(v, dict) and v.get("id") and v["id"] not in done]
    if mode == "check":
        for v in todo:
            print(f"  📮 Worker 대신 보낼 영상: {v.get('title')} ({v['id']})")
        return
    if mode == "test":
        return
    for v in todo:
        video = _worker_video(v)
        coupons = video_coupons(video)
        to = v.get("target") if v.get("target") in ("skin", "video") else video_route(video, coupons, cfg)
        send_to(deliver, video_payload(video, coupons, cfg["mention"], skin=to == "skin"), to)
        state["handoff_sent"].append(v["id"])
        state["seen_codes"] += [c["code"] for c in coupons]
        print(f"유튜브 대신 전송 (Worker가 못 보낸 영상): {video['title']}")
        time.sleep(1)


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
    lines.append(say("redeem"))
    line = say("remind", c["code"], code=f"`{c['code']}`", hours=left)
    return {
        "content": f"{mention} {line}".strip(),
        "embeds": [{"title": say("remind_title"), "description": "\n".join(lines), "color": COLOR_COUPON}],
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


def bot_profile(token):
    """디스코드 개발자 포털 → Bot 탭의 이름·프로필 사진. 웹후크 글도 이걸로 보내서 모든 채널을 봇 프로필 하나로 통일."""
    if not token:
        return {}
    req = urllib.request.Request(
        "https://discord.com/api/v10/users/@me",
        headers={"Authorization": f"Bot {token}", "User-Agent": DISCORD_USER_AGENT},
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            user = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[경고] 봇 프로필을 못 읽어서 웹후크 기본 이름·사진으로 보내요: {e}")
        return {}
    return profile_from_user(user)


def profile_from_user(user):
    out = {}
    name = (user.get("global_name") or user.get("username") or "").strip()
    # 웹후크 이름에는 'discord', 'clyde'가 들어가면 디스코드가 거절함 → 그땐 이름은 웹후크 것 그대로
    if 1 <= len(name) <= 80 and not re.search(r"discord|clyde", name, re.I):
        out["username"] = name
    uid, avatar = user.get("id"), user.get("avatar")
    if uid and avatar:
        out["avatar_url"] = f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.{'gif' if avatar.startswith('a_') else 'png'}?size=256"
    elif uid:
        out["avatar_url"] = f"https://cdn.discordapp.com/embed/avatars/{(int(uid) >> 22) % 6}.png"
    return out


def target_for(channel_id, token, webhook):
    """봇 계정으로 채널에 올리기(채널 ID + 봇 토큰)가 우선, 없으면 웹후크."""
    if channel_id and token:
        return ("bot", channel_id, token)
    if webhook:
        return ("webhook", webhook)
    return None


class Outbox:
    """소식 종류별로 보낼 채널을 고름. 전용 채널이 없으면: skin → video → main, patch → main."""

    FALLBACK = {"skin": "video", "video": "main", "patch": "main"}
    NAMES = {"main": "알림 채널", "patch": "패치 채널", "video": "유튜브 채널", "skin": "스킨 영상 채널"}

    def __init__(self, targets, dry_run=False, profile=None):
        self.targets = targets
        self.dry_run = dry_run
        self.profile = profile or {}

    def resolve(self, to):
        while to != "main" and not self.targets.get(to):
            to = self.FALLBACK.get(to, "main")
        return to

    def route(self, payload, to="main"):
        to = self.resolve(to)
        if self.dry_run:
            print(f"[{self.NAMES.get(to, to)}] " + json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            send_discord(self.targets[to], payload, self.profile)

    def __call__(self, payload):
        self.route(payload, "main")


def send_discord(target, payload, profile=None):
    if target[0] == "bot":
        send_bot_message(target[1], target[2], payload)
    else:
        send_webhook(target[1], {**payload, **(profile or {})})


def send_bot_message(channel_id, token, payload):
    """봇 계정으로 채널에 글 올리기 (내가 디스코드에서 글 쓰는 것과 같은 방식)."""
    body = {k: v for k, v in payload.items() if k not in ("username", "avatar_url")}
    data = json.dumps(body).encode("utf-8")
    for _ in range(5):
        req = urllib.request.Request(
            f"https://discord.com/api/v10/channels/{channel_id}/messages",
            data=data,
            method="POST",
            headers={"Authorization": f"Bot {token}", "Content-Type": "application/json", "User-Agent": DISCORD_USER_AGENT},
        )
        try:
            with urllib.request.urlopen(req, timeout=20):
                return
        except urllib.error.HTTPError as e:
            raw = e.read()
            if e.code == 429:
                try:
                    wait = float(json.loads(raw or b"{}").get("retry_after", 1))
                except ValueError:
                    wait = 2.0
                time.sleep(min(wait, 30) + 0.5)
                continue
            hint = {
                401: "봇 토큰이 틀렸어요 (DISCORD_BOT_TOKEN).",
                403: "봇이 그 채널에 글을 쓸 수 없어요. 봇을 'bot' 권한으로 서버에 초대했는지, 채널 권한에서 봇에게 "
                     "채널 보기·메시지 보내기·링크 첨부가 허용돼 있는지 확인해 주세요.",
                404: "채널 ID가 틀렸어요.",
            }.get(e.code, "")
            raise RuntimeError(f"봇 메시지 전송 실패 (HTTP {e.code}) {hint} {raw[:200]!r}") from None
    raise RuntimeError("봇 메시지 전송 실패: 재시도 횟수 초과")


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
    for key in ("seen_gids", "seen_codes", "seen_videos", "yt_ready", "reminded", "handoff_sent", "seen_official", "patch_sent"):
        state.setdefault(key, [])
    state.setdefault("official_ready", False)
    state.setdefault("official_fail", 0)
    state.setdefault("yt_ids", {})
    return state


def save_state(state):
    for key in ("seen_gids", "seen_codes", "seen_videos", "reminded", "handoff_sent", "seen_official", "patch_sent"):
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
        "patch_source": "steam" if setting("PATCH_SOURCE").lower() in ("steam", "off", "none") else "official",
    }


# ---------------------------------------------------------------- 실행


def main(argv=None):
    ap = argparse.ArgumentParser(description="이터널 리턴 스킨·새 시즌·쿠폰 디스코드 알림")
    group = ap.add_mutually_exclusive_group()
    group.add_argument("--check", action="store_true", help="보냄/건너뜀 목록만 출력")
    group.add_argument("--test", action="store_true", help="최신 패치노트 1개 + 필터를 통과하는 최신 공지 1개 + 영상 1개를 강제로 전송")
    ap.add_argument("--dry-run", action="store_true", help="전송하지 않고 내용만 출력")
    args = ap.parse_args(argv)
    mode = "check" if args.check else "test" if args.test else "normal"

    token = os.environ.get("DISCORD_BOT_TOKEN", "").strip()
    env = lambda name: os.environ.get(name, "").strip()
    targets = {
        "main": target_for(env("DISCORD_CHANNEL_ID"), token, env("DISCORD_WEBHOOK_URL")),
        "patch": target_for(env("DISCORD_PATCH_CHANNEL_ID"), token, env("PATCH_WEBHOOK_URL")),  # 패치노트·핫픽스·점검
        "video": target_for(env("DISCORD_VIDEO_CHANNEL_ID"), token, env("YOUTUBE_WEBHOOK_URL")),  # 유튜브 영상
        "skin": target_for(env("DISCORD_SKIN_CHANNEL_ID"), token, env("SKIN_WEBHOOK_URL")),  # 유튜브 스킨 영상
    }
    if not targets["main"] and not (args.dry_run or args.check):
        sys.exit("보낼 곳이 없어요. DISCORD_CHANNEL_ID + DISCORD_BOT_TOKEN(봇 계정으로 올리기) 또는 DISCORD_WEBHOOK_URL 을 넣어 주세요. "
                 "(--check, --dry-run 은 없이도 실행돼요)")
    cfg = load_config()
    # 웹후크로 보낼 때만: 개발자 포털 봇 이름·사진을 웹후크 글에도 똑같이
    uses_webhook = any(t and t[0] == "webhook" for t in targets.values())
    profile = bot_profile(token) if uses_webhook and not args.check else {}
    deliver = Outbox(targets, args.dry_run, profile)

    state = load_state()
    data = load_data()
    steam_error = None
    try:
        # 패치노트·핫픽스: 공식 홈페이지에서 (PATCH_SOURCE=steam 이면 예전처럼 Steam 공지에서)
        patch_mode = "steam"
        if cfg["patch_source"] == "official":
            try:
                official_ok = run_official(state, deliver, cfg, mode, data)
            except Exception as e:
                official_ok = False
                print(f"[오류] 공식 홈페이지 패치노트: {e}")
            patch_mode = ("official" if official_ok
                          else "fallback" if state["official_fail"] >= OFFICIAL_FALLBACK_AFTER else "defer")
            if patch_mode == "fallback":
                print("  → 공식 홈페이지가 계속 안 열려서, 그동안은 Steam 패치노트 공지로 대신 보내요.")
        try:
            run_steam(state, deliver, cfg, mode, data, patch_mode)
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
            run_youtube(state, deliver, cfg, mode, data, notify=youtube_notify(cfg, info, state), info=info)
        if info is not None:
            run_handoff(state, info, deliver, cfg, mode)
    finally:
        if mode == "normal" and not args.dry_run:
            save_state(state)
            if save_data(data, state):
                print("data.json 갱신 (명령어 봇용 모음 데이터)")

    if steam_error:
        sys.exit(1)


if __name__ == "__main__":
    main()
