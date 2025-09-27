import hashlib, datetime as dt
from hulldeknaptar import get_mohu_data

def _ical_escape(s: str) -> str:
    # RFC5545 escaping
    return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")

def _fold(line: str) -> str:
    # Fold long lines at 75 octets (simple, byte-safe for ASCII)
    out = []
    while len(line) > 75:
        out.append(line[:75])
        line = " " + line[75:]
    out.append(line)
    return "\r\n".join(out)

def build_ics(rows, prodid="-//Noone//MOHU Calendar//HU"):
    # rows like: {"day": "Csütörtök", "date": "2025.10.09", "services": ["Kommunális","Szelektív"]}
    today_utc = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
    location = f"Budapest"
    cal_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"PRODID:{prodid}",
        "X-WR-CALNAME:MOHU Hulladéknaptár",
        "X-WR-TIMEZONE:Europe/Budapest",
    ]

    for r in rows:
        # Skip empty days
        if not r.get("services"):
            continue
        # Parse date
        d = dt.datetime.strptime(r["date"], "%Y.%m.%d").date()
        ymd = d.strftime("%Y%m%d")

        for svc in r["services"]:
            summary = f"{svc} hulladék"
            desc = f"{svc} gyűjtés napja."
            # Stable UID: hash of date+svc
            uid_src = f"{ymd}|{svc}"
            uid = hashlib.sha1(uid_src.encode("utf-8")).hexdigest() + "@mohu-local"
            ev = [
                "BEGIN:VEVENT",
                f"UID:{uid}",
                f"DTSTAMP:{today_utc}",
                f"DTSTART;VALUE=DATE:{ymd}",
                f"SUMMARY:{_ical_escape(summary)}",
                f"LOCATION:{_ical_escape(location)}",
                f"DESCRIPTION:{_ical_escape(desc)}",
                "CATEGORIES:Waste",
                "END:VEVENT",
            ]
            # fold any long lines for safety
            for i, line in enumerate(ev):
                ev[i] = _fold(line)
            cal_lines.extend(ev)

    cal_lines.append("END:VCALENDAR")
    ics_text = "\r\n".join(cal_lines) + "\r\n"
    return ics_text


def main():
    rows = get_mohu_data()
    # --- usage with your variables and parsed `rows` ---
    ics_text = build_ics(rows)
    with open("mohu.ics", "w", encoding="utf-8", newline="") as f:
        f.write(ics_text)
    print("Wrote mohu.ics")

if __name__ == '__main__':
    main()
