import flet as ft
import json
import os
import tempfile  # Add this import
from datetime import datetime, timedelta

# This line is the fix:
# It looks for a safe internal folder on Android; if it can't find it, it uses a temp folder.
DATA_FILE = os.path.join(ft.app_storage_dir or tempfile.gettempdir(), "expenses.json")

CATEGORIES = [
    "Groceries", "Rent", "Electricity", "Gas/LPG",
    "Mobile/Internet", "Medicine", "School/Tuition",
    "Travel/Auto/Petrol", "Milk/Dairy", "Vegetables",
    "Clothing", "Temple/Pooja", "Restaurant/Eating Out",
    "Water Bill", "Other"
]

def load_expenses():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return []

def save_expenses(expenses):
    with open(DATA_FILE, "w") as f:
        json.dump(expenses, f, indent=2)

def get_week_total(expenses):
    now = datetime.now()
    return sum(e["amount"] for e in expenses if (now - datetime.strptime(e["date"], "%Y-%m-%d")).days <= 7)

def get_month_total(expenses):
    now = datetime.now()
    return sum(e["amount"] for e in expenses if datetime.strptime(e["date"], "%Y-%m-%d").month == now.month and datetime.strptime(e["date"], "%Y-%m-%d").year == now.year)

def get_day_total(expenses, date_str):
    return sum(e["amount"] for e in expenses if e["date"] == date_str)

def get_top_category(expenses):
    if not expenses:
        return "None"
    cat_totals = {}
    for e in expenses:
        cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
    return max(cat_totals, key=cat_totals.get)

def get_expenses_for_date(expenses, date_str):
    return [e for e in expenses if e["date"] == date_str]

def get_expenses_for_month(expenses, year, month):
    return [e for e in expenses if datetime.strptime(e["date"], "%Y-%m-%d").month == month and datetime.strptime(e["date"], "%Y-%m-%d").year == year]

def main(page: ft.Page):
    page.title = "Ghar ka Hisaab"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = "#f0f4f8"
    page.padding = 16
    page.scroll = ft.ScrollMode.AUTO

    expenses = load_expenses()
    today_str = datetime.now().strftime("%Y-%m-%d")

    # ── Summary cards ──────────────────────────────────────
    week_text   = ft.Text(f"₹{get_week_total(expenses):,.0f}",  size=20, weight=ft.FontWeight.BOLD, color="#1D9E75")
    month_text  = ft.Text(f"₹{get_month_total(expenses):,.0f}", size=20, weight=ft.FontWeight.BOLD, color="#1D9E75")
    top_cat     = ft.Text(get_top_category(expenses), size=13, weight=ft.FontWeight.BOLD, color="#1D9E75")
    entry_count = ft.Text(str(len(expenses)), size=20, weight=ft.FontWeight.BOLD, color="#1D9E75")
    today_text  = ft.Text(f"₹{get_day_total(expenses, today_str):,.0f}", size=20, weight=ft.FontWeight.BOLD, color="#1D9E75")

    def summary_card(label, value_widget):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=12, color="#000000", weight=ft.FontWeight.BOLD),
                value_widget,
            ], spacing=6),
            bgcolor="white",
            border_radius=12,
            padding=ft.padding.all(14),
            border=ft.border.all(1, "#e0e0e0"),
            expand=True,
        )

    summary_row  = ft.Row([summary_card("Today's Spend", today_text),  summary_card("This Week",    week_text)],  spacing=10)
    summary_row2 = ft.Row([summary_card("This Month",    month_text),  summary_card("Top Category", top_cat)],    spacing=10)
    summary_row3 = ft.Row([summary_card("Total Entries", entry_count)], spacing=10)

    def refresh_summary():
        today_str2 = datetime.now().strftime("%Y-%m-%d")
        today_text.value  = f"₹{get_day_total(expenses, today_str2):,.0f}"
        week_text.value   = f"₹{get_week_total(expenses):,.0f}"
        month_text.value  = f"₹{get_month_total(expenses):,.0f}"
        top_cat.value     = get_top_category(expenses)
        entry_count.value = str(len(expenses))

    # ── Input fields ───────────────────────────────────────
    category_dd = ft.Dropdown(
        label="Category",
        options=[ft.dropdown.Option(c) for c in CATEGORIES],
        value="Groceries",
        bgcolor="white",
        border_radius=10,
    )
    amount_field = ft.TextField(label="Amount (₹)", keyboard_type=ft.KeyboardType.NUMBER, bgcolor="white", border_radius=10)
    note_field   = ft.TextField(label="Note (optional)", bgcolor="white", border_radius=10)
    status_text  = ft.Text("", size=13)

    # ── Daily expenses list ────────────────────────────────
    daily_list     = ft.Column(spacing=6)
    daily_date_lbl = ft.Text(f"Today — {datetime.now().strftime('%d %b %Y')}", size=14, weight=ft.FontWeight.BOLD, color="#333")
    daily_total_lbl= ft.Text("", size=13, color="#888")

    def refresh_daily(date_str=None):
        if date_str is None:
            date_str = datetime.now().strftime("%Y-%m-%d")
        day_expenses = get_expenses_for_date(expenses, date_str)
        daily_list.controls.clear()
        if not day_expenses:
            daily_list.controls.append(ft.Text("No expenses for this day.", color="#aaa", size=13))
        else:
            for e in day_expenses:
                daily_list.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Column([
                                ft.Text(e["category"], size=13, weight=ft.FontWeight.W_500),
                                ft.Text(e["note"], size=11, color="#888"),
                            ], spacing=2, expand=True),
                            ft.Text(f"₹{e['amount']:,.0f}", size=15, weight=ft.FontWeight.BOLD, color="#D85A30"),
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        bgcolor="white", border_radius=10,
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        border=ft.border.all(1, "#eee"),
                    )
                )
        total = get_day_total(expenses, date_str)
        daily_total_lbl.value = f"Total: ₹{total:,.0f}"
        page.update()

    # ── Calendar date picker for daily ────────────────────
    selected_daily_date = ft.Text(today_str, visible=False)

    def on_daily_date_picked(e):
        picked = e.control.value
        date_str = picked.strftime("%Y-%m-%d")
        selected_daily_date.value = date_str
        daily_date_lbl.value = f"{picked.strftime('%d %b %Y')}"
        refresh_daily(date_str)

    daily_date_picker = ft.DatePicker(on_change=on_daily_date_picked)
    page.overlay.append(daily_date_picker)

    def open_daily_picker(e):
        daily_date_picker.open = True
        page.update()

    pick_day_btn = ft.OutlinedButton(
        "Pick a Date",
        icon=ft.Icons.CALENDAR_TODAY,
        on_click=open_daily_picker,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    # ── History section ────────────────────────────────────
    history_list     = ft.Column(spacing=6)
    history_title    = ft.Text("", size=14, weight=ft.FontWeight.BOLD, color="#333")
    history_total_lbl= ft.Text("", size=13, color="#888")
    history_mode     = {"value": "month"}  # can be 'day' or 'month'

    def render_history_entries(entries):
        history_list.controls.clear()
        if not entries:
            history_list.controls.append(ft.Text("No expenses found.", color="#aaa", size=13))
        else:
            # Group by date
            by_date = {}
            for e in entries:
                by_date.setdefault(e["date"], []).append(e)
            for date_str in sorted(by_date.keys(), reverse=True):
                day_entries = by_date[date_str]
                day_total   = sum(x["amount"] for x in day_entries)
                d = datetime.strptime(date_str, "%Y-%m-%d")
                history_list.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(d.strftime("%d %b %Y"), size=13, weight=ft.FontWeight.BOLD, color="#444"),
                                ft.Text(f"₹{day_total:,.0f}", size=13, weight=ft.FontWeight.BOLD, color="#1D9E75"),
                            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                            ft.Column([
                                ft.Row([
                                    ft.Text(f"  • {x['category']}", size=12, expand=True, color="#555"),
                                    ft.Text(f"₹{x['amount']:,.0f}", size=12, color="#D85A30"),
                                ]) for x in day_entries
                            ], spacing=2),
                        ], spacing=6),
                        bgcolor="white", border_radius=10,
                        padding=ft.padding.symmetric(horizontal=14, vertical=10),
                        border=ft.border.all(1, "#eee"),
                    )
                )
        total = sum(e["amount"] for e in entries)
        history_total_lbl.value = f"Total: ₹{total:,.0f}"
        page.update()

    # ── History calendar pickers ───────────────────────────
    hist_date_picker  = ft.DatePicker()
    hist_month_picker = ft.DatePicker()
    page.overlay.append(hist_date_picker)
    page.overlay.append(hist_month_picker)

    def on_hist_date_picked(e):
        picked   = e.control.value
        date_str = picked.strftime("%Y-%m-%d")
        history_title.value = f"History — {picked.strftime('%d %b %Y')}"
        entries = get_expenses_for_date(expenses, date_str)
        render_history_entries(entries)

    def on_hist_month_picked(e):
        picked = e.control.value
        history_title.value = f"History — {picked.strftime('%B %Y')}"
        entries = get_expenses_for_month(expenses, picked.year, picked.month)
        render_history_entries(entries)

    hist_date_picker.on_change  = on_hist_date_picked
    hist_month_picker.on_change = on_hist_month_picked

    def open_hist_day(e):
        hist_date_picker.open = True
        page.update()

    def open_hist_month(e):
        hist_month_picker.open = True
        page.update()

    def show_all_history(e):
        history_title.value = "History — All Time"
        render_history_entries(expenses)

    hist_day_btn   = ft.OutlinedButton("By Day",   icon=ft.Icons.CALENDAR_TODAY,    on_click=open_hist_day,   style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
    hist_month_btn = ft.OutlinedButton("By Month", icon=ft.Icons.CALENDAR_MONTH,    on_click=open_hist_month, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))
    hist_all_btn   = ft.OutlinedButton("All Time", icon=ft.Icons.HISTORY,           on_click=show_all_history, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)))

    # ── Expense list (recent 30) ───────────────────────────
    expense_list = ft.Column(spacing=6)

    def refresh_list():
        expense_list.controls.clear()
        for e in reversed(expenses[-30:]):
            expense_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Column([
                            ft.Text(e["category"], size=13, weight=ft.FontWeight.W_500),
                            ft.Text(f"{e['note']}  ·  {e['date']}", size=11, color="#888"),
                        ], spacing=2, expand=True),
                        ft.Text(f"₹{e['amount']:,.0f}", size=15, weight=ft.FontWeight.BOLD, color="#D85A30"),
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    bgcolor="white", border_radius=10,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    border=ft.border.all(1, "#eee"),
                )
            )
        page.update()

    # ── Add expense ────────────────────────────────────────
    def add_expense(e):
        if not amount_field.value:
            status_text.value = "Please enter an amount!"
            status_text.color = "red"
            page.update()
            return
        try:
            amt = float(amount_field.value)
        except ValueError:
            status_text.value = "Enter a valid number!"
            status_text.color = "red"
            page.update()
            return
        entry = {
            "category": category_dd.value,
            "amount":   amt,
            "note":     note_field.value or "-",
            "date":     datetime.now().strftime("%Y-%m-%d"),
        }
        expenses.append(entry)
        save_expenses(expenses)
        amount_field.value = ""
        note_field.value   = ""
        status_text.value  = "Expense added!"
        status_text.color  = "green"
        refresh_summary()
        refresh_list()
        refresh_daily()

    add_btn = ft.ElevatedButton(
        "Add Expense", icon=ft.Icons.ADD,
        bgcolor="#1D9E75", color="white",
        on_click=add_expense,
        width=float("inf"),
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
    )

    # ── Breakdown ──────────────────────────────────────────
    breakdown_col = ft.Column(spacing=6)

    def get_weekly_breakdown():
        now = datetime.now()
        cat_totals = {}
        for e in expenses:
            if (now - datetime.strptime(e["date"], "%Y-%m-%d")).days <= 7:
                cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
        return cat_totals

    def get_monthly_breakdown():
        now = datetime.now()
        cat_totals = {}
        for e in expenses:
            d = datetime.strptime(e["date"], "%Y-%m-%d")
            if d.month == now.month and d.year == now.year:
                cat_totals[e["category"]] = cat_totals.get(e["category"], 0) + e["amount"]
        return cat_totals

    def show_breakdown(e):
        breakdown_col.controls.clear()
        data = get_weekly_breakdown() if breakdown_toggle.value == "weekly" else get_monthly_breakdown()
        if not data:
            breakdown_col.controls.append(ft.Text("No data yet.", color="#888"))
        else:
            total = sum(data.values())
            for cat, amt in sorted(data.items(), key=lambda x: -x[1]):
                pct = (amt / total * 100) if total else 0
                breakdown_col.controls.append(
                    ft.Column([
                        ft.Row([
                            ft.Text(cat, size=13, expand=True),
                            ft.Text(f"₹{amt:,.0f}  ({pct:.0f}%)", size=13, weight=ft.FontWeight.W_500, color="#D85A30"),
                        ]),
                        ft.ProgressBar(value=pct / 100, bgcolor="#eee", color="#1D9E75", height=6, border_radius=4),
                    ], spacing=4)
                )
        page.update()

    breakdown_toggle = ft.RadioGroup(
        content=ft.Row([
            ft.Radio(value="weekly",  label="This Week"),
            ft.Radio(value="monthly", label="This Month"),
        ]),
        value="weekly",
        on_change=show_breakdown,
    )

    # ── Initial load ───────────────────────────────────────
    refresh_list()
    refresh_daily()
    history_title.value = "History — All Time"
    render_history_entries(expenses)

    # ── Build page ─────────────────────────────────────────
    page.add(
        ft.Text("Ghar ka Hisaab", size=26, weight=ft.FontWeight.BOLD, color="#1D9E75"),
        ft.Text("Your daily expense tracker", size=13, color="#888"),
        ft.Divider(height=10, color="transparent"),

        summary_row,
        ft.Container(height=8),
        summary_row2,
        ft.Container(height=8),
        summary_row3,
        ft.Divider(height=16, color="transparent"),

        # Add Expense
        ft.Container(
            content=ft.Column([
                ft.Text("Add Expense", size=16, weight=ft.FontWeight.W_500),
                category_dd, amount_field, note_field, add_btn, status_text,
            ], spacing=10),
            bgcolor="white", border_radius=14,
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#e0e0e0"),
        ),
        ft.Divider(height=10, color="transparent"),

        # Daily Spends
        ft.Container(
            content=ft.Column([
                ft.Text("Daily Spends", size=16, weight=ft.FontWeight.W_500),
                ft.Row([daily_date_lbl, pick_day_btn], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                daily_total_lbl,
                daily_list,
            ], spacing=10),
            bgcolor="white", border_radius=14,
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#e0e0e0"),
        ),
        ft.Divider(height=10, color="transparent"),

        # Breakdown
        ft.Container(
            content=ft.Column([
                ft.Text("Breakdown by Category", size=16, weight=ft.FontWeight.W_500),
                breakdown_toggle,
                breakdown_col,
            ], spacing=10),
            bgcolor="white", border_radius=14,
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#e0e0e0"),
        ),
        ft.Divider(height=10, color="transparent"),

        # History
        ft.Container(
            content=ft.Column([
                ft.Text("History", size=16, weight=ft.FontWeight.W_500),
                ft.Row([hist_day_btn, hist_month_btn, hist_all_btn], spacing=8, wrap=True),
                history_title,
                history_total_lbl,
                history_list,
            ], spacing=10),
            bgcolor="white", border_radius=14,
            padding=ft.padding.all(16),
            border=ft.border.all(1, "#e0e0e0"),
        ),
    )

ft.app(target=main)
