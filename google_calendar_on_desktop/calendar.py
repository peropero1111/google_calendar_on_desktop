from __future__ import annotations

import calendar as month_calendar
import hashlib
import json
import sys
import threading
import traceback
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from pathlib import Path
from typing import Any
import tkinter as tk
from tkinter import messagebox

try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.9+ has zoneinfo.
    ZoneInfo = None


def get_app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


APP_DIR = get_app_dir()
CONFIG_PATH = APP_DIR / "calendar_widget_config.json"

FONT_FAMILY = "Malgun Gothic"
DAY_NAMES = ["월", "화", "수", "목", "금", "토", "일"]

DEFAULT_CONFIG: dict[str, Any] = {
    "ical_urls": [
        "PASTE_GOOGLE_CALENDAR_SECRET_ICAL_URL_HERE",
    ],
    "timezone": "Asia/Seoul",
    "refresh_minutes": 30,
    "follow_current_month": True,
    "window": {
        "x": 40,
        "y": 80,
        "width": 430,
        "height": 640,
        "opacity": 0.94,
        "always_on_top": False,
        "frameless": True,
    },
    "privacy": {
        "hide_details": False,
        "mask_title": "비공개 일정",
        "hidden_events": [],
    },
    "theme": {
        "background": "#111315",
        "panel": "#1A1D21",
        "panel_soft": "#22272E",
        "text": "#F4F6F8",
        "muted": "#A9B1BA",
        "accent": "#70D6C4",
        "accent_2": "#FFB86B",
        "border": "#30363D",
        "today": "#344F52",
        "error": "#FF6B6B",
    },
}


@dataclass(frozen=True)
class CalendarEvent:
    title: str
    start: datetime
    end: datetime
    all_day: bool
    location: str = ""
    calendar_name: str = ""
    private: bool = False
    privacy_key: str = ""

def deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config() -> tuple[dict[str, Any], bool, str | None]:
    if not CONFIG_PATH.exists():
        try:
            CONFIG_PATH.write_text(
                json.dumps(DEFAULT_CONFIG, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError as exc:
            return dict(DEFAULT_CONFIG), False, f"설정 파일을 만들 수 없습니다: {exc}"
        return dict(DEFAULT_CONFIG), True, None

    try:
        user_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return dict(DEFAULT_CONFIG), False, f"설정 파일을 읽을 수 없습니다: {exc}"

    return deep_merge(DEFAULT_CONFIG, user_config), False, None


def save_config(config: dict[str, Any]) -> None:
    CONFIG_PATH.write_text(
        json.dumps(config, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def first_day_of_month(day: date) -> date:
    return date(day.year, day.month, 1)


def add_months(month_start: date, delta: int) -> date:
    month_index = month_start.month - 1 + delta
    year = month_start.year + month_index // 12
    month = month_index % 12 + 1
    return date(year, month, 1)


def clean_text(value: Any, fallback: str = "") -> str:
    text = str(value or fallback).replace("\\n", " ").replace("\n", " ").strip()
    return " ".join(text.split()) or fallback


def make_timezone(name: str):
    if ZoneInfo is not None:
        try:
            return ZoneInfo(name)
        except Exception:
            pass
    return datetime.now().astimezone().tzinfo


def date_to_datetime(value: date | datetime, tz) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=tz)
        return value.astimezone(tz)
    return datetime.combine(value, time.min).replace(tzinfo=tz)


def month_range(month_start: date, tz) -> tuple[datetime, datetime]:
    start = datetime.combine(month_start, time.min).replace(tzinfo=tz)
    end = datetime.combine(add_months(month_start, 1), time.min).replace(tzinfo=tz)
    return start, end


def valid_ical_urls(urls: list[str]) -> list[str]:
    valid_urls = []
    for raw_url in urls:
        url = str(raw_url).strip()
        if not url or "PASTE_GOOGLE_CALENDAR" in url:
            continue
        valid_urls.append(url)
    return valid_urls


def make_event_privacy_key(
    calendar_name: str,
    uid: str,
    recurrence_id: str,
    start: datetime,
    title: str,
    location: str,
) -> str:
    source = "|".join([calendar_name, uid, recurrence_id, start.isoformat(), title, location])
    return hashlib.sha256(source.encode("utf-8")).hexdigest()

def event_from_component(component, tz, calendar_name: str) -> CalendarEvent | None:
    start_prop = component.get("DTSTART")
    if start_prop is None:
        return None

    raw_start = start_prop.dt
    raw_end = component.get("DTEND").dt if component.get("DTEND") is not None else None

    all_day = isinstance(raw_start, date) and not isinstance(raw_start, datetime)
    start = date_to_datetime(raw_start, tz)

    if raw_end is None:
        end = start + (timedelta(days=1) if all_day else timedelta(hours=1))
    else:
        end = date_to_datetime(raw_end, tz)

    if end <= start:
        end = start + (timedelta(days=1) if all_day else timedelta(hours=1))

    title = clean_text(component.get("SUMMARY"), "(제목 없음)")
    location = clean_text(component.get("LOCATION"))
    uid = clean_text(component.get("UID"))
    recurrence_id = clean_text(component.get("RECURRENCE-ID"))

    return CalendarEvent(
        title=title,
        start=start,
        end=end,
        all_day=all_day,
        location=location,
        calendar_name=calendar_name,
        private=str(component.get("CLASS", "")).upper() == "PRIVATE",
        privacy_key=make_event_privacy_key(
            calendar_name,
            uid,
            recurrence_id,
            start,
            title,
            location,
        ),
    )


def fetch_month_events(ical_urls: list[str], month_start: date, tz) -> list[CalendarEvent]:
    try:
        import recurring_ical_events
        import requests
        from icalendar import Calendar
    except ImportError as exc:
        raise RuntimeError(
            "필요한 패키지가 없습니다. 먼저 `python -m pip install -r requirements.txt`를 실행하세요."
        ) from exc

    period_start, period_end = month_range(month_start, tz)
    query_start = period_start - timedelta(days=31)
    query_end = period_end + timedelta(days=1)

    events: list[CalendarEvent] = []
    seen: set[tuple[str, datetime, datetime, str]] = set()

    for url in ical_urls:
        response = requests.get(
            url,
            headers={"User-Agent": "GoogleCalendarDesktopWidget/1.0"},
            timeout=25,
        )
        response.raise_for_status()

        calendar_data = Calendar.from_ical(response.content)
        calendar_name = clean_text(calendar_data.get("X-WR-CALNAME"))
        expanded_events = recurring_ical_events.of(calendar_data).between(query_start, query_end)

        for component in expanded_events:
            if getattr(component, "name", "") != "VEVENT":
                continue
            event = event_from_component(component, tz, calendar_name)
            if event is None:
                continue
            if event.end <= period_start or event.start >= period_end:
                continue

            key = (event.title, event.start, event.end, event.location)
            if key in seen:
                continue
            seen.add(key)
            events.append(event)

    return sorted(events, key=lambda item: (item.start, item.end, item.title.lower()))


def day_bounds(day: date, tz) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time.min).replace(tzinfo=tz)
    return start, start + timedelta(days=1)


def event_active_on_day(event: CalendarEvent, day: date, tz) -> bool:
    day_start, day_end = day_bounds(day, tz)
    return event.start < day_end and event.end > day_start


def build_events_by_day(
    events: list[CalendarEvent],
    month_start: date,
    tz,
) -> dict[date, list[CalendarEvent]]:
    result: dict[date, list[CalendarEvent]] = {}
    month_end = add_months(month_start, 1)
    current = month_start

    while current < month_end:
        active = [event for event in events if event_active_on_day(event, current, tz)]
        day_start, _ = day_bounds(current, tz)
        active.sort(
            key=lambda event: (
                0 if event.all_day else 1,
                max(event.start, day_start).time(),
                event.title.lower(),
            )
        )
        result[current] = active
        current += timedelta(days=1)

    return result


def format_date_heading(day: date) -> str:
    weekday = DAY_NAMES[day.weekday()]
    return f"{day.month}월 {day.day}일 ({weekday})"


def format_event_time(event: CalendarEvent, day: date) -> str:
    if event.all_day:
        return "종일"

    end_for_date = event.end - timedelta(microseconds=1)
    if event.start.date() == day and end_for_date.date() == day:
        return f"{event.start:%H:%M}-{event.end:%H:%M}"
    if event.start.date() == day:
        return f"{event.start:%H:%M} 시작"
    if end_for_date.date() == day:
        return f"{event.end:%H:%M} 종료"
    return "계속"


def mark_name_for_day(day: date) -> str:
    return f"day_{day:%Y%m%d}"


class CalendarWidgetApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.config, self.created_config, self.config_error = load_config()
        self.theme = self.config["theme"]
        self.tz = make_timezone(str(self.config.get("timezone", "Asia/Seoul")))
        self.today = datetime.now(self.tz).date()
        self.view_month = first_day_of_month(self.today)
        self.events: list[CalendarEvent] = []
        self.loading = False
        self.last_error: str | None = None
        privacy_config = self.config.get("privacy", {})
        self.hidden_event_keys: set[str] = set(privacy_config.get("hidden_events", []))
        self.privacy_select_mode = False
        self.drag_offset: tuple[int, int] | None = None

        self.root.title("Google Calendar Desktop Widget")
        self.configure_window()
        self.build_ui()
        self.render()

        if self.config_error is not None:
            self.show_error(self.config_error)
        elif not valid_ical_urls(self.config.get("ical_urls", [])):
            self.show_setup_message()
        else:
            self.refresh_events()

        self.schedule_auto_refresh()
        self.schedule_month_rollover_check()
        self.root.protocol("WM_DELETE_WINDOW", self.close)

    def configure_window(self) -> None:
        window_config = self.config["window"]
        width = int(window_config.get("width", 430))
        height = int(window_config.get("height", 640))
        x = int(window_config.get("x", 40))
        y = int(window_config.get("y", 80))
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.minsize(330, 460)
        self.root.configure(bg=self.theme["background"])

        try:
            self.root.attributes("-alpha", float(window_config.get("opacity", 0.94)))
            self.root.attributes("-topmost", bool(window_config.get("always_on_top", False)))
        except tk.TclError:
            pass

        if bool(window_config.get("frameless", True)):
            self.root.overrideredirect(True)

    def build_ui(self) -> None:
        self.container = tk.Frame(
            self.root,
            bg=self.theme["background"],
            highlightthickness=1,
            highlightbackground=self.theme["border"],
        )
        self.container.pack(fill="both", expand=True)

        self.title_bar = tk.Frame(self.container, bg=self.theme["panel"], height=44)
        self.title_bar.pack(fill="x")
        self.title_bar.pack_propagate(False)
        self.title_bar.bind("<ButtonPress-1>", self.start_drag)
        self.title_bar.bind("<B1-Motion>", self.drag_window)

        self.month_label = tk.Label(
            self.title_bar,
            text="",
            bg=self.theme["panel"],
            fg=self.theme["text"],
            font=(FONT_FAMILY, 13, "bold"),
            anchor="w",
        )
        self.month_label.pack(side="left", padx=(14, 8), fill="x", expand=True)
        self.month_label.bind("<ButtonPress-1>", self.start_drag)
        self.month_label.bind("<B1-Motion>", self.drag_window)

        button_specs = [
            ("‹", self.previous_month, "이전 달"),
            ("오늘", self.go_today, "이번 달"),
            ("›", self.next_month, "다음 달"),
            (self.privacy_button_text(), self.toggle_privacy, "숨길 일정 선택"),
            ("↻", self.refresh_events, "새로고침"),
            ("×", self.close, "닫기"),
        ]
        for label, command, tooltip in button_specs:
            button = tk.Button(
                self.title_bar,
                text=label,
                command=command,
                bd=0,
                relief="flat",
                bg=self.theme["panel"],
                fg=self.theme["text"],
                activebackground=self.theme["panel_soft"],
                activeforeground=self.theme["accent"],
                font=(FONT_FAMILY, 10, "bold"),
                width=4 if label == "오늘" else 3,
                cursor="hand2",
                takefocus=False,
            )
            button.pack(side="left", padx=(0, 2), pady=7)
            if command == self.toggle_privacy:
                self.privacy_button = button
            button.bind("<Enter>", lambda event, text=tooltip: self.set_status(text))
            button.bind("<Leave>", lambda event: self.render_status())

        self.calendar_holder = tk.Frame(self.container, bg=self.theme["background"], height=212)
        self.calendar_holder.pack(fill="x", padx=12, pady=(12, 6))
        self.calendar_holder.pack_propagate(False)

        self.status_label = tk.Label(
            self.container,
            text="",
            bg=self.theme["background"],
            fg=self.theme["muted"],
            font=(FONT_FAMILY, 9),
            anchor="w",
        )
        self.status_label.pack(fill="x", padx=14, pady=(0, 6))

        agenda_frame = tk.Frame(self.container, bg=self.theme["background"])
        agenda_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self.agenda_text = tk.Text(
            agenda_frame,
            bd=0,
            wrap="word",
            bg=self.theme["panel"],
            fg=self.theme["text"],
            insertbackground=self.theme["text"],
            selectbackground=self.theme["today"],
            font=(FONT_FAMILY, 10),
            padx=12,
            pady=10,
            relief="flat",
            height=8,
        )
        self.agenda_text.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(
            agenda_frame,
            orient="vertical",
            command=self.agenda_text.yview,
            width=12,
        )
        scrollbar.pack(side="right", fill="y")
        self.agenda_text.configure(yscrollcommand=scrollbar.set)

        self.agenda_text.tag_configure(
            "date",
            foreground=self.theme["accent"],
            font=(FONT_FAMILY, 10, "bold"),
            spacing1=9,
            spacing3=2,
        )
        self.agenda_text.tag_configure(
            "time",
            foreground=self.theme["accent_2"],
            font=(FONT_FAMILY, 9, "bold"),
        )
        self.agenda_text.tag_configure("muted", foreground=self.theme["muted"])
        self.agenda_text.tag_configure("error", foreground=self.theme["error"])
        self.agenda_text.tag_configure("private", foreground=self.theme["muted"])
        self.agenda_text.configure(state="disabled")

    def make_day_cell(self, parent: tk.Frame, day: date, count: int, in_month: bool) -> tk.Frame:
        today = datetime.now(self.tz).date()
        is_today = day == today
        bg = self.theme["today"] if is_today else self.theme["panel"]
        fg = self.theme["text"] if in_month else self.theme["muted"]

        if not in_month:
            bg = self.theme["background"]

        cursor = "hand2" if in_month and count else ""
        cell = tk.Frame(
            parent,
            bg=bg,
            bd=0,
            relief="flat",
            cursor=cursor,
        )

        date_label = tk.Label(
            cell,
            text=str(day.day),
            bg=bg,
            fg=fg,
            font=(FONT_FAMILY, 9, "bold" if is_today else "normal"),
            anchor="nw",
            justify="left",
            padx=6,
            pady=0,
            cursor=cursor,
        )
        date_label.pack(anchor="nw", fill="x", pady=(5, 0))

        if count:
            count_label = tk.Label(
                cell,
                text=f"{count}건",
                bg=bg,
                fg=self.theme["error"],
                font=(FONT_FAMILY, 8, "bold"),
                anchor="nw",
                justify="left",
                padx=6,
                pady=0,
                cursor=cursor,
            )
            count_label.pack(anchor="nw", fill="x", pady=(0, 5))
            count_label.bind(
                "<Button-1>",
                lambda _event, selected_day=day: self.jump_to_day(selected_day),
            )

        cell.grid(sticky="nsew", padx=1, pady=1)
        cell.bind("<Button-1>", lambda _event, selected_day=day: self.jump_to_day(selected_day))
        date_label.bind("<Button-1>", lambda _event, selected_day=day: self.jump_to_day(selected_day))
        return cell

    def render(self) -> None:
        self.month_label.configure(text=f"{self.view_month.year}년 {self.view_month.month}월")
        if hasattr(self, "privacy_button"):
            self.privacy_button.configure(text=self.privacy_button_text())
        by_day = build_events_by_day(self.events, self.view_month, self.tz)
        self.render_calendar_grid(by_day)
        self.render_agenda(by_day)
        self.render_status()

    def render_calendar_grid(self, by_day: dict[date, list[CalendarEvent]]) -> None:
        for child in self.calendar_holder.winfo_children():
            child.destroy()

        for col in range(7):
            self.calendar_holder.columnconfigure(col, weight=1, uniform="day")

        for row in range(7):
            self.calendar_holder.rowconfigure(row, weight=1, uniform="week")

        for col, name in enumerate(DAY_NAMES):
            label = tk.Label(
                self.calendar_holder,
                text=name,
                bg=self.theme["background"],
                fg=self.theme["muted"],
                font=(FONT_FAMILY, 9, "bold"),
                anchor="center",
            )
            label.grid(row=0, column=col, sticky="nsew", padx=1, pady=(0, 2))

        calendar = month_calendar.Calendar(firstweekday=0)
        weeks = calendar.monthdatescalendar(self.view_month.year, self.view_month.month)
        for row_index, week in enumerate(weeks, start=1):
            for col_index, day in enumerate(week):
                in_month = day.month == self.view_month.month
                count = len(by_day.get(day, [])) if in_month else 0
                cell = self.make_day_cell(self.calendar_holder, day, count, in_month)
                cell.grid(row=row_index, column=col_index)

    def render_agenda(self, by_day: dict[date, list[CalendarEvent]]) -> None:
        self.agenda_text.configure(state="normal")
        self.agenda_text.delete("1.0", "end")
        self.agenda_event_tags: dict[str, str] = {}
        if self.config_error:
            self.agenda_text.insert("end", self.config_error + "\n", "error")
            self.agenda_text.configure(state="disabled")
            return

        if not valid_ical_urls(self.config.get("ical_urls", [])):
            self.insert_setup_text()
            self.agenda_text.configure(state="disabled")
            return

        any_events = False
        current = self.view_month
        month_end = add_months(self.view_month, 1)

        while current < month_end:
            day_events = by_day.get(current, [])
            if day_events:
                any_events = True
                self.agenda_text.mark_set(mark_name_for_day(current), "end")
                self.agenda_text.insert("end", format_date_heading(current) + "\n", "date")
                for event in day_events:
                    time_label = format_event_time(event, current)
                    event_tag = self.register_agenda_event_tag(event)
                    click_tags = (event_tag, "event_click")
                    self.agenda_text.insert("end", f"  {time_label:<11}", ("time", *click_tags))
                    title = self.display_event_title(event)
                    title_tags = ("private", *click_tags) if self.should_mask_event(event) else click_tags
                    self.agenda_text.insert("end", title + "\n", title_tags)
                    if event.location and not self.should_mask_event(event):
                        self.agenda_text.insert("end", f"    {event.location}\n", ("muted", *click_tags))
                self.agenda_text.insert("end", "\n")
            current += timedelta(days=1)

        if not any_events:
            self.agenda_text.insert(
                "end",
                "이번 달 일정이 없습니다.\n",
                "muted",
            )

        if self.last_error:
            self.agenda_text.insert("end", "\n최근 새로고침 실패:\n", "error")
            self.agenda_text.insert("end", self.last_error + "\n", "muted")

        self.agenda_text.configure(state="disabled")

    def privacy_button_text(self) -> str:
        return "완료" if self.privacy_select_mode else "선택"

    def register_agenda_event_tag(self, event: CalendarEvent) -> str:
        event_tag = f"event_{event.privacy_key}"
        self.agenda_event_tags[event_tag] = event.privacy_key
        self.agenda_text.tag_bind(
            event_tag,
            "<Button-1>",
            lambda _event, event_key=event.privacy_key: self.toggle_event_hidden(event_key),
        )
        self.agenda_text.tag_bind(
            event_tag,
            "<Enter>",
            lambda _event: self.agenda_text.configure(cursor="hand2"),
        )
        self.agenda_text.tag_bind(
            event_tag,
            "<Leave>",
            lambda _event: self.agenda_text.configure(cursor=""),
        )
        return event_tag

    def should_mask_event(self, event: CalendarEvent) -> bool:
        return event.private or event.privacy_key in self.hidden_event_keys

    def display_event_title(self, event: CalendarEvent) -> str:
        if self.should_mask_event(event):
            privacy_config = self.config.get("privacy", {})
            return str(privacy_config.get("mask_title", "비공개 일정"))
        return event.title

    def toggle_privacy(self) -> None:
        self.privacy_select_mode = not self.privacy_select_mode
        self.render()

    def toggle_event_hidden(self, event_key: str) -> None:
        if not self.privacy_select_mode:
            self.set_status("상단의 선택을 누른 뒤 숨길 일정을 클릭하세요.")
            return

        if event_key in self.hidden_event_keys:
            self.hidden_event_keys.remove(event_key)
        else:
            self.hidden_event_keys.add(event_key)

        self.save_hidden_events()
        self.render()

    def save_hidden_events(self) -> None:
        privacy_config = self.config.setdefault("privacy", {})
        privacy_config["hide_details"] = False
        privacy_config["hidden_events"] = sorted(self.hidden_event_keys)
        try:
            save_config(self.config)
        except OSError as exc:
            messagebox.showwarning("저장 실패", f"프라이버시 설정을 저장하지 못했습니다:\n{exc}")

    def insert_setup_text(self) -> None:
        self.agenda_text.insert("end", "처음 실행 설정\n", "date")
        self.agenda_text.insert(
            "end",
            (
                "1. Google Calendar 웹에서 설정을 엽니다.\n"
                "2. 왼쪽에서 표시할 캘린더를 고릅니다.\n"
                "3. `캘린더 통합`에서 `iCal 형식의 비공개 주소`를 복사합니다.\n"
                f"4. {CONFIG_PATH.name} 파일의 ical_urls 안에 붙여 넣습니다.\n"
                "5. 이 앱을 다시 실행하거나 새로고침을 누릅니다.\n\n"
                "비공개 iCal 주소는 비밀번호처럼 다루세요.\n"
            ),
            "muted",
        )

    def render_status(self) -> None:
        if self.loading:
            self.set_status("일정을 불러오는 중...")
            return

        if self.config_error:
            self.set_status("설정 파일 오류")
            return

        if not valid_ical_urls(self.config.get("ical_urls", [])):
            self.set_status(f"{CONFIG_PATH.name}에 Google Calendar iCal 주소를 넣어주세요.")
            return

        total = len(self.events)
        refresh_minutes = int(self.config.get("refresh_minutes", 30))
        hidden_count = len(self.hidden_event_keys)
        if self.privacy_select_mode:
            self.set_status(f"숨김 선택 중 | 숨김 {hidden_count}개 | 일정을 클릭하세요")
        else:
            self.set_status(f"{total}개 일정 표시 | 숨김 {hidden_count}개 | {refresh_minutes}분마다 새로고침")

    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def show_setup_message(self) -> None:
        if self.created_config:
            self.set_status(f"{CONFIG_PATH.name} 파일을 만들었습니다.")
        self.render()

    def show_error(self, message: str) -> None:
        self.last_error = message
        self.render()

    def refresh_events(self) -> None:
        urls = valid_ical_urls(self.config.get("ical_urls", []))
        if self.loading or not urls or self.config_error is not None:
            self.render()
            return

        self.loading = True
        self.last_error = None
        self.render_status()
        target_month = self.view_month

        worker = threading.Thread(
            target=self.fetch_worker,
            args=(urls, target_month),
            daemon=True,
        )
        worker.start()

    def fetch_worker(self, urls: list[str], target_month: date) -> None:
        try:
            events = fetch_month_events(urls, target_month, self.tz)
        except Exception:
            error = traceback.format_exc(limit=2).strip()
            self.root.after(0, lambda: self.finish_refresh(target_month, [], error))
            return

        self.root.after(0, lambda: self.finish_refresh(target_month, events, None))

    def finish_refresh(
        self,
        target_month: date,
        events: list[CalendarEvent],
        error: str | None,
    ) -> None:
        self.loading = False
        if target_month != self.view_month:
            self.refresh_events()
            return

        if error:
            self.last_error = error
        else:
            self.events = events
            self.last_error = None

        self.render()

    def schedule_auto_refresh(self) -> None:
        refresh_minutes = max(1, int(self.config.get("refresh_minutes", 30)))
        self.root.after(refresh_minutes * 60 * 1000, self.auto_refresh)

    def auto_refresh(self) -> None:
        self.refresh_events()
        self.schedule_auto_refresh()

    def schedule_month_rollover_check(self) -> None:
        self.root.after(60 * 1000, self.check_month_rollover)

    def check_month_rollover(self) -> None:
        today = datetime.now(self.tz).date()
        current_month = first_day_of_month(today)
        if bool(self.config.get("follow_current_month", True)) and current_month != self.view_month:
            self.today = today
            self.view_month = current_month
            self.refresh_events()
        self.schedule_month_rollover_check()

    def previous_month(self) -> None:
        self.view_month = add_months(self.view_month, -1)
        self.events = []
        self.refresh_events()
        self.render()

    def next_month(self) -> None:
        self.view_month = add_months(self.view_month, 1)
        self.events = []
        self.refresh_events()
        self.render()

    def go_today(self) -> None:
        self.view_month = first_day_of_month(datetime.now(self.tz).date())
        self.events = []
        self.refresh_events()
        self.render()

    def jump_to_day(self, day: date) -> None:
        if day.month != self.view_month.month:
            return
        mark = mark_name_for_day(day)
        if mark in self.agenda_text.mark_names():
            self.agenda_text.see(mark)

    def start_drag(self, event) -> None:
        self.drag_offset = (event.x_root - self.root.winfo_x(), event.y_root - self.root.winfo_y())

    def drag_window(self, event) -> None:
        if self.drag_offset is None:
            return
        offset_x, offset_y = self.drag_offset
        self.root.geometry(f"+{event.x_root - offset_x}+{event.y_root - offset_y}")

    def save_window_position(self) -> None:
        if self.config_error is not None:
            return

        window_config = self.config.setdefault("window", {})
        window_config["x"] = self.root.winfo_x()
        window_config["y"] = self.root.winfo_y()
        window_config["width"] = self.root.winfo_width()
        window_config["height"] = self.root.winfo_height()
        try:
            save_config(self.config)
        except OSError as exc:
            messagebox.showwarning("저장 실패", f"창 위치를 저장하지 못했습니다:\n{exc}")

    def close(self) -> None:
        self.save_window_position()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    CalendarWidgetApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
