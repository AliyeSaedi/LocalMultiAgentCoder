import sys
import io
import json
import os
import threading
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import ollama

# تنظیم انکودینگ خروجی
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

HISTORY_FILE = "ai_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_to_history(prompt, output_text, lang, mode):
    history = load_history()
    history.insert(0, {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "language": lang,
        "mode": mode,
        "prompt": prompt,
        "output": output_text
    })
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def clear_history_file():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)

def get_installed_models():
    try:
        models = ollama.list()
        return [m['model'] for m in models.get('models', [])]
    except:
        return ["qwen2.5:3b", "deepseek-r1:7b", "qwen2.5-coder:1.5b"]

class ModernAIPipelineApp:
    def __init__(self, root):
        self.root = root
        self.root.title("دستیار هوشمند برنامه‌نویسی آفلاین (حرفه‌ای و پیشرفته)")
        self.root.geometry("1150x780")
        self.root.configure(bg="#0f172a")

        self.is_running = False
        self.start_time = 0

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(".", background="#0f172a", foreground="#f8fafc", fieldbackground="#1e293b")
        style.configure("TLabel", background="#0f172a", foreground="#cbd5e1", font=("Tahoma", 10))
        style.configure("Header.TLabel", font=("Tahoma", 11, "bold"), foreground="#38bdf8")
        style.configure("TRadiobutton", background="#111827", foreground="#f8fafc", font=("Tahoma", 9))

        self.available_models = get_installed_models()
        if not self.available_models:
            self.available_models = ["qwen2.5:3b", "deepseek-r1:7b", "qwen2.5-coder:1.5b"]

        self.programming_languages = [
            "پایتون (Python)", 
            "جاوا اسکریپت (JavaScript)", 
            "تایپ اسکریپت (TypeScript)", 
            "اچ‌تی‌ام‌ال / سی‌اس‌اس (HTML/CSS)", 
            "سی‌پلاس‌پلاس (C++)", 
            "جاوا (Java)", 
            "سایر / عمومی"
        ]

        self.create_widgets()
        self.load_history_list()

    def create_widgets(self):
        main_layout = tk.PanedWindow(self.root, orient=tk.HORIZONTAL, bg="#1e293b", sashwidth=3, borderwidth=0)
        main_layout.pack(fill=tk.BOTH, expand=True, padx=12, pady=12)

        # --- ستون سمت راست (تنظیمات مدل‌ها، حالت اجرا، زبان و تاریخچه) ---
        right_sidebar = tk.Frame(main_layout, bg="#111827", padx=12, pady=12)
        main_layout.add(right_sidebar, width=330)

        # دکمه چت جدید در بالای سایدبار
        new_chat_btn = tk.Button(right_sidebar, text="➕ چت جدید", font=("Tahoma", 10, "bold"), bg="#0284c7", fg="white",
                                 relief="flat", cursor="hand2", command=self.new_chat)
        new_chat_btn.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(right_sidebar, text="⚙️ حالت اجرا (مُد)", style="Header.TLabel").pack(anchor="e", pady=(0, 4))
        
        # رادیو باتن تکی / چندتایی
        self.mode_var = tk.StringVar(value="multi")
        mode_frame = tk.Frame(right_sidebar, bg="#111827")
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Radiobutton(mode_frame, text="چندتایی (زنجیره هوشمند)", variable=self.mode_var, value="multi", command=self.toggle_mode).pack(anchor="e", pady=2)
        ttk.Radiobutton(mode_frame, text="تکی (فقط یک مدل)", variable=self.mode_var, value="single", command=self.toggle_mode).pack(anchor="e", pady=2)

        ttk.Label(right_sidebar, text="⚙️ تنظیمات مدل‌ها", style="Header.TLabel").pack(anchor="e", pady=(5, 8))

        ttk.Label(right_sidebar, text="مدل مترجم / رابط فارسی:").pack(anchor="e", pady=(2, 0))
        self.m1_combo = ttk.Combobox(right_sidebar, values=self.available_models, state="readonly", justify="right")
        self.m1_combo.pack(fill=tk.X, pady=(0, 8))
        if self.available_models: self.m1_combo.current(0)

        # فریم مدل‌های تحلیل و کدزن (برای حالت تکی غیرفعال می‌شوند)
        self.multi_models_frame = tk.Frame(right_sidebar, bg="#111827")
        self.multi_models_frame.pack(fill=tk.X, pady=(0, 5))

        ttk.Label(self.multi_models_frame, text="مدل تحلیل‌گر منطق:").pack(anchor="e", pady=(2, 0))
        self.m2_combo = ttk.Combobox(self.multi_models_frame, values=self.available_models, state="readonly", justify="right")
        self.m2_combo.pack(fill=tk.X, pady=(0, 8))
        if len(self.available_models) > 1: self.m2_combo.current(1)
        elif self.available_models: self.m2_combo.current(0)

        ttk.Label(self.multi_models_frame, text="مدل کدزن و برنامه‌نویس:").pack(anchor="e", pady=(2, 0))
        self.m3_combo = ttk.Combobox(self.multi_models_frame, values=self.available_models, state="readonly", justify="right")
        self.m3_combo.pack(fill=tk.X, pady=(0, 8))
        if len(self.available_models) > 2: self.m3_combo.current(2)
        elif self.available_models: self.m3_combo.current(0)

        ttk.Label(right_sidebar, text="زبان برنامه‌نویسی خروجی:").pack(anchor="e", pady=(2, 0))
        self.lang_combo = ttk.Combobox(right_sidebar, values=self.programming_languages, state="readonly", justify="right")
        self.lang_combo.pack(fill=tk.X, pady=(0, 15))
        self.lang_combo.current(0)

        # بخش تاریخچه
        history_header_frame = tk.Frame(right_sidebar, bg="#111827")
        history_header_frame.pack(fill=tk.X, pady=(5, 5))
        
        clear_hist_btn = tk.Button(history_header_frame, text="🗑️ پاک کردن", font=("Tahoma", 8), bg="#374151", fg="white", 
                                   relief="flat", cursor="hand2", command=self.clear_history)
        clear_hist_btn.pack(side=tk.LEFT)
        
        ttk.Label(history_header_frame, text="🕒 تاریخچه گفتگوها", style="Header.TLabel").pack(side=tk.RIGHT)
        
        history_frame = tk.Frame(right_sidebar, bg="#111827")
        history_frame.pack(fill=tk.BOTH, expand=True)

        self.history_listbox = tk.Listbox(history_frame, bg="#1f2937", fg="#f3f4f6", selectbackground="#374151", 
                                          font=("Tahoma", 9), borderwidth=0, highlightthickness=0, justify="right")
        self.history_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.history_listbox.bind("<<ListboxSelect>>", self.on_history_select)

        scrollbar = ttk.Scrollbar(history_frame, orient="vertical", command=self.history_listbox.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.history_listbox.config(yscrollcommand=scrollbar.set)

        # --- پنل اصلی سمت چپ ---
        left_main = tk.Frame(main_layout, bg="#0f172a", padx=12, pady=5)
        main_layout.add(left_main)

        ttk.Label(left_main, text="✍️ پرامپت برنامه‌نویسی خود را به فارسی بنویسید:", font=("Tahoma", 10, "bold"), foreground="#e2e8f0").pack(anchor="e", pady=(0, 5))

        self.text_input = tk.Text(left_main, height=4, font=("Tahoma", 10), bg="#1e293b", fg="#ffffff", 
                                  insertbackground="white", borderwidth=1, relief="solid")
        self.text_input.pack(fill=tk.X, pady=(0, 8))
        
        # لودر و تایمر
        progress_frame = tk.Frame(left_main, bg="#0f172a")
        progress_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.progress = ttk.Progressbar(progress_frame, orient="horizontal", mode="indeterminate")
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        self.timer_label = tk.Label(progress_frame, text="⏱️ 0 ثانیه", font=("Consolas", 9), foreground="#38bdf8", bg="#0f172a")
        self.timer_label.pack(side=tk.RIGHT)

        # دکمه‌های کنترل
        btn_frame = tk.Frame(left_main, bg="#0f172a")
        btn_frame.pack(fill=tk.X, pady=(0, 10))

        self.run_btn = tk.Button(btn_frame, text="🚀 اجرای پردازش", font=("Tahoma", 10, "bold"),
                                 bg="#0284c7", fg="white", activebackground="#0369a1", activeforeground="white",
                                 relief="flat", cursor="hand2", command=self.start_pipeline_thread)
        self.run_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(0, 4))

        self.stop_btn = tk.Button(btn_frame, text="⏹️ توقف پردازش", font=("Tahoma", 10, "bold"),
                                  bg="#dc2626", fg="white", activebackground="#b91c1c", activeforeground="white",
                                  relief="flat", cursor="hand2", state=tk.DISABLED, command=self.stop_pipeline)
        self.stop_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # هدر خروجی همراه با دکمه کپی سریع
        output_header_frame = tk.Frame(left_main, bg="#0f172a")
        output_header_frame.pack(fill=tk.X, pady=(0, 5))
        
        copy_btn = tk.Button(output_header_frame, text="📋 کپی کل خروجی", font=("Tahoma", 9), bg="#334155", fg="white",
                             relief="flat", cursor="hand2", command=self.copy_output_to_clipboard)
        copy_btn.pack(side=tk.LEFT)
        
        ttk.Label(output_header_frame, text="💻 خروجی و نتایج مدل‌ها:", font=("Tahoma", 10, "bold"), foreground="#e2e8f0").pack(side=tk.RIGHT)

        self.output_area = scrolledtext.ScrolledText(left_main, font=("Consolas", 10), bg="#111827", fg="#34d399",
                                                     insertbackground="white", borderwidth=1, relief="solid")
        self.output_area.pack(fill=tk.BOTH, expand=True)
        
        self.output_area.tag_configure("persian", justify="right", font=("Tahoma", 10), foreground="#e2e8f0")
        self.output_area.tag_configure("code", justify="left", font=("Consolas", 10), foreground="#34d399")
        self.output_area.tag_configure("header", justify="right", font=("Tahoma", 11, "bold"), foreground="#38bdf8")

    def toggle_mode(self):
        if self.mode_var.get() == "single":
            # غیرفعال کردن بخش مدل‌های چندتایی
            for child in self.multi_models_frame.winfo_children():
                child.configure(state='disabled' if isinstance(child, ttk.Combobox) else 'disabled')
        else:
            for child in self.multi_models_frame.winfo_children():
                child.configure(state='readonly' if isinstance(child, ttk.Combobox) else 'normal')

    def new_chat(self):
        self.text_input.delete(1.0, tk.END)
        self.output_area.delete(1.0, tk.END)
        self.append_text("✨ چت جدید آماده است. پرامپت خود را وارد کنید.\n", "persian")

    def load_history_list(self):
        self.history_listbox.delete(0, tk.END)
        self.history_data = load_history()
        for item in self.history_data:
            lang_tag = f"[{item.get('language', 'عمومی')}]"
            summary = f"{item['prompt'][:20]}... {lang_tag}"
            self.history_listbox.insert(tk.END, summary)

    def clear_history(self):
        if messagebox.askyesno("تایید حذف", "آیا مطمئن هستید که می‌خواهید تمام تاریخچه گفتگوها را پاک کنید؟"):
            clear_history_file()
            self.load_history_list()
            self.output_area.delete(1.0, tk.END)
            self.append_text("تاریخچه پاک شد.\n", "persian")

    def on_history_select(self, event):
        selection = self.history_listbox.curselection()
        if selection:
            index = selection[0]
            item = self.history_data[index]
            self.output_area.delete(1.0, tk.END)
            self.append_text(f"--- تاریخچه ثبت شده در [{item['time']}] | زبان: {item.get('language', 'نامشخص')} ---\n\n", "header")
            self.append_text(f"پرامپت کاربر:\n{item['prompt']}\n\n", "persian")
            self.append_text(item['output'], "code")

    def copy_output_to_clipboard(self):
        content = self.output_area.get(1.0, tk.END)
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        messagebox.showinfo("کپی شد", "محتوای خروجی با موفقیت در کلیپ‌بورد کپی شد!")

    def append_text(self, text, tag):
        self.output_area.insert(tk.END, text, tag)
        self.output_area.see(tk.END)

    def start_pipeline_thread(self):
        user_prompt = self.text_input.get("1.0", tk.END).strip()
        if not user_prompt:
            messagebox.showwarning("خطا", "لطفاً متن پرامپت را وارد کنید.")
            return

        self.is_running = True
        self.start_time = time.time()
        self.run_btn.config(state=tk.DISABLED, text="⏳ در حال پردازش...")
        self.stop_btn.config(state=tk.NORMAL)
        self.progress.start(10)
        self.output_area.delete(1.0, tk.END)
        self.append_text("سیستم فعال شد. مدل‌ها در حال کار هستند...\n\n", "persian")

        threading.Thread(target=self.update_timer, daemon=True).start()
        threading.Thread(target=self.run_pipeline_logic, args=(user_prompt,), daemon=True).start()

    def update_timer(self):
        while self.is_running:
            elapsed = int(time.time() - self.start_time)
            self.root.after(0, lambda t=elapsed: self.timer_label.config(text=f"⏱️ {t} ثانیه"))
            time.sleep(1)

    def stop_pipeline(self):
        self.is_running = False
        self.update_output("\n\n⚠️ پردازش توسط کاربر متوقف شد.\n", "persian")
        self.stop_loading_state()

    def run_pipeline_logic(self, user_prompt):
        m1 = self.m1_combo.get()
        selected_lang = self.lang_combo.get()
        mode = self.mode_var.get()

        full_output_record = ""

        try:
            if mode == "single":
                # حالت تکی: فقط استفاده از مدل اول
                if not self.is_running: return
                self.update_output(f"\n[حالت تکی] در حال پردازش توسط مدل ({m1})...\n", "persian")
                prompt_single = f"Write code in {selected_lang} based on this request, and explain briefly in Persian:\n{user_prompt}"
                res = ollama.chat(model=m1, messages=[{'role': 'user', 'content': prompt_single}])['message']['content']
                
                if not self.is_running: return
                self.update_output(f"\n--- پاسخ مدل ({m1}) ---\n{res}\n", "code")
                full_output_record += f"【 پاسخ تکی ({m1}) 】\n{res}\n"

            else:
                # حالت چندتایی (زنجیره‌ای با مترجم دوطرفه)
                m2 = self.m2_combo.get()
                m3 = self.m3_combo.get()

                # مرحله ۱: ترجمه پرامپت فارسی به انگلیسی فنی
                if not self.is_running: return
                self.update_output(f"\n[مرحله ۱/۴] مترجم ({m1}): در حال ترجمه پرامپت فارسی به انگلیسی فنی...\n", "persian")
                t_prompt = f"Translate, structure, and refine this Persian prompt into clear technical requirements in English:\n{user_prompt}"
                r1 = ollama.chat(model=m1, messages=[{'role': 'user', 'content': t_prompt}])['message']['content']
                if not self.is_running: return
                self.update_output(f"\n--- پرامپت فنی ترجمه شده ---\n{r1}\n", "code")
                full_output_record += f"【 مرحله ۱ - پرامپت فنی 】\n{r1}\n\n"

                # مرحله ۲: تحلیل منطق
                if not self.is_running: return
                self.update_output(f"\n[مرحله ۲/۴] تحلیل‌گر ({m2}): در حال طراحی الگوریتم و معماری...\n", "persian")
                l_prompt = f"Analyze these requirements and design step-by-step logic/architecture:\n{r1}"
                r2 = ollama.chat(model=m2, messages=[{'role': 'user', 'content': l_prompt}])['message']['content']
                if not self.is_running: return
                self.update_output(f"\n--- تحلیل منطق ---\n{r2}\n", "code")
                full_output_record += f"【 مرحله ۲ - تحلیل منطق 】\n{r2}\n\n"

                # مرحله ۳: تولید کد
                if not self.is_running: return
                self.update_output(f"\n[مرحله ۳/۴] کدزن ({m3}): در حال تولید کد با زبان {selected_lang}...\n", "persian")
                c_prompt = f"Based on this logic, write clean, efficient, production-ready code in {selected_lang} with comments:\n{r2}"
                r3 = ollama.chat(model=m3, messages=[{'role': 'user', 'content': c_prompt}])['message']['content']
                if not self.is_running: return
                self.update_output(f"\n--- کد نهایی خروجی ---\n{r3}\n", "code")
                full_output_record += f"【 مرحله ۳ - کد نهایی 】\n{r3}\n\n"

                # مرحله ۴: ترجمه معکوس خروجی انگلیسی به فارسی روان توسط مدل مترجم
                if not self.is_running: return
                self.update_output(f"\n[مرحله ۴/۴] مترجم ({m1}): در حال ترجمه و آماده‌سازی توضیحات نتیجه به فارسی روان...\n", "persian")
                back_translate_prompt = f"Translate and summarize the core explanation of the following developer output into smooth, natural Persian so the user can easily understand it:\n{r3}"
                r4 = ollama.chat(model=m1, messages=[{'role': 'user', 'content': back_translate_prompt}])['message']['content']
                if not self.is_running: return
                self.update_output(f"\n--- خلاصه و توضیحات فارسی روان (توسط مترجم) ---\n{r4}\n", "persian")
                full_output_record += f"【 مرحله ۴ - توضیحات فارسی روان 】\n{r4}\n"

            elapsed_total = int(time.time() - self.start_time)
            self.update_output(f"\n✨ فرآیند با موفقیت در مدت {elapsed_total} ثانیه کامل شد!\n", "persian")

            # ذخیره در تاریخچه
            save_to_history(user_prompt, full_output_record, selected_lang, mode)
            self.root.after(0, self.load_history_list)

        except Exception as e:
            if self.is_running:
                self.update_output(f"\n[خطا]:\n{str(e)}\n", "code")

        finally:
            self.root.after(0, self.stop_loading_state)

    def stop_loading_state(self, success=True):
        self.progress.stop()
        self.run_btn.config(state=tk.NORMAL, text="🚀 اجرای پردازش")
        self.stop_btn.config(state=tk.DISABLED)
        self.is_running = False

    def update_output(self, text, tag):
        self.root.after(0, lambda: self.append_text(text, tag))

if __name__ == "__main__":
    root = tk.Tk()
    app = ModernAIPipelineApp(root)
    root.mainloop()