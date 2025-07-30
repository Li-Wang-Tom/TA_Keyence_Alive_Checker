import tkinter as tk
from tkinter import ttk, scrolledtext
import socket
import threading
import datetime
import time

class PLCControlGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KVシリーズ 上位リンクテストツール")
        self.root.geometry("600x600")

        # PLC初期設定
        self.plc_ip = "192.168.0.100"
        self.plc_port = 8501

        # 機種リストと選択
        self.model_list = {
            "KV-5000": "55",
            "KV-7000": "56",
            "KV-8000": "57"
        }
        self.selected_model = tk.StringVar(value="KV-8000")

        self.create_widgets()
        self.log_message("GUI起動完了")

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 接続設定
        connection_frame = ttk.LabelFrame(main_frame, text="PLC接続設定", padding="5")
        connection_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(connection_frame, text="IP:").grid(row=0, column=0, sticky=tk.W)
        self.ip_var = tk.StringVar(value=self.plc_ip)
        ttk.Entry(connection_frame, textvariable=self.ip_var, width=15).grid(row=0, column=1, padx=5)

        ttk.Label(connection_frame, text="Port:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.port_var = tk.StringVar(value=str(self.plc_port))
        ttk.Entry(connection_frame, textvariable=self.port_var, width=8).grid(row=0, column=3, padx=5)

        ttk.Label(connection_frame, text="機種:").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        model_combo = ttk.Combobox(connection_frame, textvariable=self.selected_model,
                                   values=list(self.model_list.keys()), width=10, state="readonly")
        model_combo.grid(row=0, column=5, padx=5)

        ttk.Button(connection_frame, text="接続テスト", command=self.test_connection).grid(row=0, column=6, padx=10)

        self.connection_status = tk.StringVar(value="未接続")
        self.status_label = ttk.Label(connection_frame, textvariable=self.connection_status, foreground="red")
        self.status_label.grid(row=0, column=7, padx=10)

        # デバイス操作
        device_frame = ttk.LabelFrame(main_frame, text="デバイス操作", padding="5")
        device_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(device_frame, text="デバイス:").grid(row=0, column=0, sticky=tk.W)
        self.device_type = tk.StringVar(value="DM")
        device_combo = ttk.Combobox(device_frame, textvariable=self.device_type, values=["DM", "W", "R", "MR"], width=5, state="readonly")
        device_combo.grid(row=0, column=1, padx=5)

        ttk.Label(device_frame, text="番号:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.device_number = tk.StringVar(value="100")
        ttk.Entry(device_frame, textvariable=self.device_number, width=8).grid(row=0, column=3, padx=5)

        ttk.Label(device_frame, text="現在値:").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        self.current_value = tk.StringVar(value="---")
        ttk.Label(device_frame, textvariable=self.current_value, foreground="blue", font=("Arial", 12, "bold")).grid(row=0, column=5, padx=5)

        ttk.Button(device_frame, text="読み込み", command=self.read_device).grid(row=0, column=6, padx=5)

        # 0/1送信ボタン
        button_frame = ttk.Frame(device_frame)
        button_frame.grid(row=1, column=0, columnspan=7, pady=10)

        self.send_0_btn = ttk.Button(button_frame, text="0を送信", command=lambda: self.write_device(0))
        self.send_0_btn.grid(row=0, column=0, padx=10, ipadx=20)

        self.send_1_btn = ttk.Button(button_frame, text="1を送信", command=lambda: self.write_device(1))
        self.send_1_btn.grid(row=0, column=1, padx=10, ipadx=20)

        # カスタム値送信
        custom_frame = ttk.Frame(device_frame)
        custom_frame.grid(row=2, column=0, columnspan=7, pady=5)

        ttk.Label(custom_frame, text="カスタム値:").grid(row=0, column=0, sticky=tk.W)
        self.custom_value = tk.StringVar()
        ttk.Entry(custom_frame, textvariable=self.custom_value, width=10).grid(row=0, column=1, padx=5)
        ttk.Button(custom_frame, text="送信", command=self.write_custom_value).grid(row=0, column=2, padx=5)

        # ハートビート機能
        heartbeat_frame = ttk.LabelFrame(main_frame, text="標準ハートビート機能（0/1繰り返し）", padding="5")
        heartbeat_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        hb_setting_frame = ttk.Frame(heartbeat_frame)
        hb_setting_frame.grid(row=0, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(hb_setting_frame, text="デバイス:").grid(row=0, column=0, sticky=tk.W)
        self.hb_device_type = tk.StringVar(value="DM")
        hb_device_combo = ttk.Combobox(hb_setting_frame, textvariable=self.hb_device_type, values=["DM", "W", "R", "MR"], width=5, state="readonly")
        hb_device_combo.grid(row=0, column=1, padx=5)

        ttk.Label(hb_setting_frame, text="番号:").grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        self.hb_device_number = tk.StringVar(value="200")
        ttk.Entry(hb_setting_frame, textvariable=self.hb_device_number, width=8).grid(row=0, column=3, padx=5)

        ttk.Label(hb_setting_frame, text="間隔(秒):").grid(row=0, column=4, sticky=tk.W, padx=(10, 0))
        self.hb_interval = tk.StringVar(value="1.0")
        ttk.Entry(hb_setting_frame, textvariable=self.hb_interval, width=8).grid(row=0, column=5, padx=5)

        hb_control_frame = ttk.Frame(heartbeat_frame)
        hb_control_frame.grid(row=1, column=0, columnspan=4, pady=10)

        self.hb_start_btn = ttk.Button(hb_control_frame, text="ハートビート開始", command=self.start_heartbeat)
        self.hb_start_btn.grid(row=0, column=0, padx=10, ipadx=20)

        self.hb_stop_btn = ttk.Button(hb_control_frame, text="ハートビート停止", command=self.stop_heartbeat, state="disabled")
        self.hb_stop_btn.grid(row=0, column=1, padx=10, ipadx=20)

        self.hb_status = tk.StringVar(value="停止中")
        self.hb_status_label = ttk.Label(hb_control_frame, textvariable=self.hb_status, foreground="red", font=("Arial", 10, "bold"))
        self.hb_status_label.grid(row=0, column=2, padx=20)

        self.hb_count = tk.StringVar(value="送信回数: 0")
        ttk.Label(hb_control_frame, textvariable=self.hb_count).grid(row=0, column=3, padx=10)

        self.heartbeat_running = False
        self.heartbeat_thread = None
        self.hb_counter = 0
        self.hb_current_value = 0

        log_frame = ttk.LabelFrame(main_frame, text="通信ログ", padding="5")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=80)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Button(log_frame, text="ログクリア", command=self.clear_log).grid(row=1, column=0, pady=5)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(3, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

    def log_message(self, message):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        self.root.update()

    def clear_log(self):
        self.log_text.delete(1.0, tk.END)

    def get_device_address(self):
        device_type = self.device_type.get()
        device_num = self.device_number.get()
        try:
            num = int(device_num)
            return f"{device_type}{num:04d}" if device_type in ["DM", "W"] else f"{device_type}{num}"
        except ValueError:
            return None

    def plc_command(self, command):
        try:
            ip = self.ip_var.get()
            port = int(self.port_var.get())
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((ip, port))
            sock.send(command.encode("ascii"))
            response = sock.recv(64).decode("utf-8").strip()
            sock.close()
            return True, response
        except Exception as e:
            return False, str(e)

    def test_connection(self):
        self.log_message("接続テスト開始...")

        def test_thread():
            success, response = self.plc_command("?K\r")
            expected_model = self.selected_model.get()
            expected_code = self.model_list.get(expected_model, "")

            if success:
                if response == expected_code:
                    self.connection_status.set(f"✓ {expected_model}接続")
                    self.status_label.configure(foreground="green")
                    self.log_message(f"✓ 接続成功: {expected_model} (機種番号: {response})")
                else:
                    self.connection_status.set(f"✓ 接続 (不一致: {response})")
                    self.status_label.configure(foreground="orange")
                    self.log_message(f"✓ 接続成功: 期待={expected_model}({expected_code}) 実際={response}")
            else:
                self.connection_status.set("✗ 接続失敗")
                self.status_label.configure(foreground="red")
                self.log_message(f"✗ 接続失敗: {response}")

        threading.Thread(target=test_thread, daemon=True).start()

    def read_device(self):
        device_addr = self.get_device_address()
        if not device_addr:
            self.log_message("✗ デバイス番号が不正です")
            return

        self.log_message(f"読み込み中: {device_addr}")

        def read_thread():
            command = f"RD {device_addr}\r"
            success, response = self.plc_command(command)
            if success:
                try:
                    value = int(response)
                    self.current_value.set(str(value))
                    self.log_message(f"✓ {device_addr} = {value}")
                except ValueError:
                    self.log_message(f"✗ 読み込み応答エラー: {response}")
            else:
                self.log_message(f"✗ 読み込み失敗: {response}")

        threading.Thread(target=read_thread, daemon=True).start()

    def write_device(self, value):
        device_addr = self.get_device_address()
        if not device_addr:
            self.log_message("✗ デバイス番号が不正です")
            return

        self.log_message(f"書き込み中: {device_addr} = {value}")

        def write_thread():
            command = f"WR {device_addr} {value}\r"
            success, response = self.plc_command(command)
            if success:
                if response == "OK":
                    self.current_value.set(str(value))
                    self.log_message(f"✓ {device_addr} = {value} 書き込み成功")
                else:
                    self.log_message(f"✗ 書き込み応答エラー: {response}")
            else:
                self.log_message(f"✗ 書き込み失敗: {response}")

        threading.Thread(target=write_thread, daemon=True).start()

    def write_custom_value(self):
        try:
            value = int(self.custom_value.get())
            self.write_device(value)
            self.custom_value.set("")
        except ValueError:
            self.log_message("✗ カスタム値は数値で入力してください")

    def get_heartbeat_device_address(self):
        device_type = self.hb_device_type.get()
        device_num = self.hb_device_number.get()
        try:
            num = int(device_num)
            return f"{device_type}{num:04d}" if device_type in ["DM", "W"] else f"{device_type}{num}"
        except ValueError:
            return None

    def start_heartbeat(self):
        device_addr = self.get_heartbeat_device_address()
        if not device_addr:
            self.log_message("✗ ハートビート: デバイス番号が不正です")
            return
        try:
            interval = float(self.hb_interval.get())
            if interval <= 0:
                raise ValueError
        except ValueError:
            self.log_message("✗ ハートビート: 間隔は正の数値で入力してください")
            return
        if self.heartbeat_running:
            self.log_message("✗ ハートビートは既に動作中です")
            return

        self.heartbeat_running = True
        self.hb_counter = 0
        self.hb_current_value = 0
        self.hb_start_btn.config(state="disabled")
        self.hb_stop_btn.config(state="normal")
        self.hb_status.set("動作中")
        self.hb_status_label.config(foreground="green")
        self.heartbeat_thread = threading.Thread(target=self.heartbeat_worker, args=(device_addr, interval), daemon=True)
        self.heartbeat_thread.start()
        self.log_message(f"✓ 標準ハートビート開始: {device_addr}, 間隔 {interval}秒")

    def stop_heartbeat(self):
        if not self.heartbeat_running:
            return
        self.heartbeat_running = False
        self.hb_start_btn.config(state="normal")
        self.hb_stop_btn.config(state="disabled")
        self.hb_status.set("停止中")
        self.hb_status_label.config(foreground="red")
        self.log_message("✓ 標準ハートビート停止")

    def heartbeat_worker(self, device_addr, interval):
        while self.heartbeat_running:
            try:
                value = self.hb_current_value
                command = f"WR {device_addr} {value}\r"
                success, response = self.plc_command(command)
                if success and response == "OK":
                    self.hb_counter += 1
                    self.hb_count.set(f"送信回数: {self.hb_counter}")
                    self.hb_current_value = 1 - self.hb_current_value
                    if self.hb_counter % 5 == 0:
                        self.log_message(f"♥ 標準HB: {device_addr} = {value} (#{self.hb_counter})")
                else:
                    self.log_message(f"✗ 標準HBエラー: {device_addr} = {value}")
            except Exception as e:
                self.log_message(f"✗ 標準HB例外: {e}")
            time.sleep(interval)

def main():
    root = tk.Tk()
    app = PLCControlGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
