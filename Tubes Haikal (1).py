# -*- coding: utf-8 -*-
"""
Aplikasi Turnamen Esports GUI
Rombakan dari versi Jupyter/IPython Display menjadi aplikasi desktop Tkinter + ttkbootstrap.

Library yang digunakan:
1. tkinter
2. ttkbootstrap
3. pandas

Cara menjalankan:
    pip install ttkbootstrap pandas openpyxl
    python aplikasi_turnamen_esports_gui.py
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from dataclasses import dataclass, field
from typing import Optional

import pandas as pd

try:
    import ttkbootstrap as tb
    from ttkbootstrap.constants import *
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Library ttkbootstrap belum terinstall. Jalankan: pip install ttkbootstrap"
    ) from exc


# ============================================================
# BACKEND / LOGIKA UTAMA
# ============================================================

@dataclass
class Pemain:
    nama: str
    nama_tim: str
    kill: int = 0
    assist: int = 0
    death: int = 0
    jumlah_match: int = 0

    @property
    def kda(self) -> float:
        """KDA = (Kill + Assist) / max(Death, 1)."""
        return round((self.kill + self.assist) / max(self.death, 1), 2)

    @property
    def rata_kill(self) -> float:
        return round(self.kill / max(self.jumlah_match, 1), 2)


@dataclass
class Tim:
    nama: str
    menang: int = 0
    kalah: int = 0
    seri: int = 0
    skor_pribadi: int = 0
    skor_musuh: int = 0
    daftar_pemain: list[Pemain] = field(default_factory=list)

    @property
    def selisih_skor(self) -> int:
        return self.skor_pribadi - self.skor_musuh

    @property
    def total_match(self) -> int:
        return self.menang + self.kalah + self.seri

    @property
    def win_rate(self) -> float:
        if self.total_match == 0:
            return 0.0
        return round((self.menang / self.total_match) * 100, 1)

    @property
    def rata_skor(self) -> float:
        if self.total_match == 0:
            return 0.0
        return round(self.skor_pribadi / self.total_match, 2)


class Turnamen:
    def __init__(self) -> None:
        self.daftar_tim: list[Tim] = []
        self.riwayat_pertandingan: list[dict] = []

    # ---------------------- CRUD TIM ----------------------
    def tambah_tim(self, nama: str) -> tuple[bool, str]:
        nama = nama.strip()
        if not nama:
            return False, "Nama tim tidak boleh kosong."
        if self._cari_tim_objek(nama):
            return False, f"Tim '{nama}' sudah terdaftar."
        self.daftar_tim.append(Tim(nama))
        return True, f"Tim '{nama}' berhasil ditambahkan."

    def ubah_tim(self, nama_lama: str, nama_baru: str) -> tuple[bool, str]:
        nama_lama = nama_lama.strip()
        nama_baru = nama_baru.strip()
        if not nama_lama or not nama_baru:
            return False, "Nama lama dan nama baru wajib diisi."

        tim = self._cari_tim_objek(nama_lama)
        if not tim:
            return False, f"Tim '{nama_lama}' tidak ditemukan."

        duplikat = self._cari_tim_objek(nama_baru)
        if duplikat and duplikat is not tim:
            return False, f"Tim '{nama_baru}' sudah terdaftar."

        for match in self.riwayat_pertandingan:
            if match["tim1"].lower() == nama_lama.lower():
                match["tim1"] = nama_baru
            if match["tim2"].lower() == nama_lama.lower():
                match["tim2"] = nama_baru

        for pemain in tim.daftar_pemain:
            pemain.nama_tim = nama_baru

        tim.nama = nama_baru
        self._update_klasemen()
        return True, f"Tim '{nama_lama}' berhasil diubah menjadi '{nama_baru}'."

    def hapus_tim(self, nama: str) -> tuple[bool, str]:
        nama = nama.strip()
        tim = self._cari_tim_objek(nama)
        if not tim:
            return False, f"Tim '{nama}' tidak ditemukan."

        self.daftar_tim.remove(tim)
        self.riwayat_pertandingan = [
            m for m in self.riwayat_pertandingan
            if m["tim1"].lower() != nama.lower() and m["tim2"].lower() != nama.lower()
        ]
        self._update_klasemen()
        return True, f"Tim '{nama}' dan riwayat pertandingannya berhasil dihapus."

    # ---------------------- CRUD PEMAIN ----------------------
    def tambah_pemain(self, nama_pemain: str, nama_tim: str) -> tuple[bool, str]:
        nama_pemain = nama_pemain.strip()
        nama_tim = nama_tim.strip()
        if not nama_pemain or not nama_tim:
            return False, "Nama pemain dan nama tim wajib diisi."

        tim = self._cari_tim_objek(nama_tim)
        if not tim:
            return False, f"Tim '{nama_tim}' belum terdaftar."

        if any(p.nama.lower() == nama_pemain.lower() for p in tim.daftar_pemain):
            return False, f"Pemain '{nama_pemain}' sudah terdaftar di tim '{nama_tim}'."

        tim.daftar_pemain.append(Pemain(nama_pemain, tim.nama))
        return True, f"Pemain '{nama_pemain}' berhasil ditambahkan ke tim '{tim.nama}'."

    def ubah_pemain(self, nama_lama: str, nama_baru: str, nama_tim: str) -> tuple[bool, str]:
        nama_lama = nama_lama.strip()
        nama_baru = nama_baru.strip()
        nama_tim = nama_tim.strip()

        if not nama_lama or not nama_baru or not nama_tim:
            return False, "Nama lama, nama baru, dan tim wajib diisi."

        tim = self._cari_tim_objek(nama_tim)
        if not tim:
            return False, f"Tim '{nama_tim}' tidak ditemukan."

        pemain = self._cari_pemain_objek(nama_lama, tim.nama)
        if not pemain:
            return False, f"Pemain '{nama_lama}' tidak ditemukan di tim '{tim.nama}'."

        duplikat = self._cari_pemain_objek(nama_baru, tim.nama)
        if duplikat and duplikat is not pemain:
            return False, f"Pemain '{nama_baru}' sudah ada di tim '{tim.nama}'."

        pemain.nama = nama_baru
        return True, f"Pemain '{nama_lama}' berhasil diubah menjadi '{nama_baru}'."

    def hapus_pemain(self, nama_pemain: str, nama_tim: str) -> tuple[bool, str]:
        nama_pemain = nama_pemain.strip()
        nama_tim = nama_tim.strip()
        tim = self._cari_tim_objek(nama_tim)
        if not tim:
            return False, f"Tim '{nama_tim}' belum terdaftar."

        pemain = self._cari_pemain_objek(nama_pemain, tim.nama)
        if not pemain:
            return False, f"Pemain '{nama_pemain}' tidak ditemukan di tim '{tim.nama}'."

        tim.daftar_pemain.remove(pemain)
        return True, f"Pemain '{nama_pemain}' berhasil dihapus dari tim '{tim.nama}'."

    def input_statistik_pemain(
        self,
        nama_pemain: str,
        nama_tim: str,
        kill: int,
        assist: int,
        death: int,
    ) -> tuple[bool, str]:
        if kill < 0 or assist < 0 or death < 0:
            return False, "Kill, assist, dan death tidak boleh bernilai negatif."

        tim = self._cari_tim_objek(nama_tim)
        if not tim:
            return False, f"Tim '{nama_tim}' tidak ditemukan."

        pemain = self._cari_pemain_objek(nama_pemain, tim.nama)
        if not pemain:
            return False, f"Pemain '{nama_pemain}' tidak ditemukan di tim '{tim.nama}'."

        pemain.kill += kill
        pemain.assist += assist
        pemain.death += death
        pemain.jumlah_match += 1
        return True, (
            f"Statistik '{pemain.nama}' diperbarui: "
            f"K:{pemain.kill} / A:{pemain.assist} / D:{pemain.death}."
        )

    # ---------------------- PERTANDINGAN ----------------------
    def tambah_pertandingan(self, nama_tim1: str, skor1: int, nama_tim2: str, skor2: int) -> tuple[bool, str]:
        if skor1 < 0 or skor2 < 0:
            return False, "Skor tidak boleh negatif."

        t1 = self._cari_tim_objek(nama_tim1)
        t2 = self._cari_tim_objek(nama_tim2)
        if not t1 or not t2:
            return False, "Salah satu atau kedua nama tim belum didaftarkan."
        if t1.nama.lower() == t2.nama.lower():
            return False, "Tim tidak bisa bertanding melawan dirinya sendiri."

        self.riwayat_pertandingan.append({
            "tim1": t1.nama,
            "skor1": int(skor1),
            "tim2": t2.nama,
            "skor2": int(skor2),
        })
        self._update_klasemen()
        return True, f"Pertandingan {t1.nama} ({skor1}) vs ({skor2}) {t2.nama} berhasil disimpan."

    def hapus_pertandingan(self, index: int) -> tuple[bool, str]:
        if index < 0 or index >= len(self.riwayat_pertandingan):
            return False, "Riwayat pertandingan tidak valid."
        match = self.riwayat_pertandingan.pop(index)
        self._update_klasemen()
        return True, f"Riwayat {match['tim1']} vs {match['tim2']} berhasil dihapus."

    def _update_klasemen(self) -> None:
        for tim in self.daftar_tim:
            tim.menang = 0
            tim.kalah = 0
            tim.seri = 0
            tim.skor_pribadi = 0
            tim.skor_musuh = 0

        for match in self.riwayat_pertandingan:
            t1 = self._cari_tim_objek(match["tim1"])
            t2 = self._cari_tim_objek(match["tim2"])
            if not t1 or not t2:
                continue

            skor1 = int(match["skor1"])
            skor2 = int(match["skor2"])

            t1.skor_pribadi += skor1
            t1.skor_musuh += skor2
            t2.skor_pribadi += skor2
            t2.skor_musuh += skor1

            if skor1 > skor2:
                t1.menang += 1
                t2.kalah += 1
            elif skor2 > skor1:
                t2.menang += 1
                t1.kalah += 1
            else:
                t1.seri += 1
                t2.seri += 1

    # ---------------------- SEARCHING ----------------------
    def sequential_search(self, nama_cari: str) -> Optional[Tim]:
        for tim in self.daftar_tim:
            if tim.nama.lower() == nama_cari.lower():
                return tim
        return None

    def binary_search(self, nama_cari: str) -> Optional[Tim]:
        tim_terurut = sorted(self.daftar_tim, key=lambda x: x.nama.lower())
        low, high = 0, len(tim_terurut) - 1
        nama_cari = nama_cari.lower()

        while low <= high:
            mid = (low + high) // 2
            nama_mid = tim_terurut[mid].nama.lower()
            if nama_mid == nama_cari:
                return tim_terurut[mid]
            if nama_mid < nama_cari:
                low = mid + 1
            else:
                high = mid - 1
        return None

    # ---------------------- SORTING ----------------------
    def selection_sort(self, berdasarkan: str = "menang") -> list[Tim]:
        arr = list(self.daftar_tim)
        n = len(arr)
        for i in range(n):
            max_idx = i
            for j in range(i + 1, n):
                val_j = self._nilai_sort(arr[j], berdasarkan)
                val_max = self._nilai_sort(arr[max_idx], berdasarkan)
                if val_j > val_max:
                    max_idx = j
            arr[i], arr[max_idx] = arr[max_idx], arr[i]
        return arr

    def insertion_sort(self, berdasarkan: str = "menang") -> list[Tim]:
        arr = list(self.daftar_tim)
        for i in range(1, len(arr)):
            key_item = arr[i]
            val_key = self._nilai_sort(key_item, berdasarkan)
            j = i - 1
            while j >= 0 and self._nilai_sort(arr[j], berdasarkan) < val_key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key_item
        return arr

    @staticmethod
    def _nilai_sort(tim: Tim, berdasarkan: str) -> float:
        if berdasarkan == "menang":
            return tim.menang
        if berdasarkan == "selisih":
            return tim.selisih_skor
        if berdasarkan == "winrate":
            return tim.win_rate
        if berdasarkan == "rata_skor":
            return tim.rata_skor
        return tim.menang

    # ---------------------- STATISTIK ----------------------
    def get_statistik_tim(self) -> list[Tim]:
        hasil = [tim for tim in self.daftar_tim if tim.total_match > 0]
        return sorted(hasil, key=lambda x: (x.win_rate, x.selisih_skor, x.menang), reverse=True)

    def get_tim_terbaik(self) -> Optional[Tim]:
        tim_aktif = [t for t in self.daftar_tim if t.total_match > 0]
        if not tim_aktif:
            return None
        return max(tim_aktif, key=lambda x: (x.win_rate, x.selisih_skor, x.menang))

    def get_semua_pemain(self) -> list[Pemain]:
        semua: list[Pemain] = []
        for tim in self.daftar_tim:
            semua.extend(tim.daftar_pemain)
        return semua

    def get_pemain_terbaik_kda(self) -> Optional[Pemain]:
        semua = [p for p in self.get_semua_pemain() if p.jumlah_match > 0]
        if not semua:
            return None
        return max(semua, key=lambda p: (p.kda, p.kill, p.assist))

    def get_pemain_top_kill(self) -> Optional[Pemain]:
        semua = [p for p in self.get_semua_pemain() if p.jumlah_match > 0]
        if not semua:
            return None
        return max(semua, key=lambda p: (p.kill, p.kda))

    # ---------------------- DATAFRAME / PANDAS ----------------------
    def df_klasemen(self, sumber: Optional[list[Tim]] = None) -> pd.DataFrame:
        data_tim = sumber if sumber is not None else sorted(
            self.daftar_tim,
            key=lambda t: (t.menang, t.win_rate, t.selisih_skor),
            reverse=True,
        )
        return pd.DataFrame([
            {
                "Nama Tim": t.nama,
                "Main": t.total_match,
                "Menang": t.menang,
                "Kalah": t.kalah,
                "Seri": t.seri,
                "Win Rate (%)": t.win_rate,
                "Skor Tim": t.skor_pribadi,
                "Skor Musuh": t.skor_musuh,
                "Selisih Skor": t.selisih_skor,
                "Rata-rata Skor": t.rata_skor,
                "Jumlah Pemain": len(t.daftar_pemain),
            }
            for t in data_tim
        ])

    def df_pemain(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "Nama Pemain": p.nama,
                "Tim": p.nama_tim,
                "Match": p.jumlah_match,
                "Kill": p.kill,
                "Assist": p.assist,
                "Death": p.death,
                "KDA": p.kda,
                "Rata-rata Kill": p.rata_kill,
            }
            for p in sorted(self.get_semua_pemain(), key=lambda x: (x.kda, x.kill), reverse=True)
        ])

    def df_riwayat(self) -> pd.DataFrame:
        return pd.DataFrame([
            {
                "No": i + 1,
                "Tim 1": m["tim1"],
                "Skor 1": m["skor1"],
                "Tim 2": m["tim2"],
                "Skor 2": m["skor2"],
                "Pemenang": self._pemenang_match(m),
            }
            for i, m in enumerate(self.riwayat_pertandingan)
        ])

    @staticmethod
    def _pemenang_match(match: dict) -> str:
        if match["skor1"] > match["skor2"]:
            return match["tim1"]
        if match["skor2"] > match["skor1"]:
            return match["tim2"]
        return "Seri"

    # ---------------------- HELPER ----------------------
    def _cari_tim_objek(self, nama: str) -> Optional[Tim]:
        nama = nama.strip().lower()
        for tim in self.daftar_tim:
            if tim.nama.lower() == nama:
                return tim
        return None

    def _cari_pemain_objek(self, nama_pemain: str, nama_tim: str) -> Optional[Pemain]:
        tim = self._cari_tim_objek(nama_tim)
        if not tim:
            return None
        nama_pemain = nama_pemain.strip().lower()
        for pemain in tim.daftar_pemain:
            if pemain.nama.lower() == nama_pemain:
                return pemain
        return None

    def reset(self) -> None:
        self.daftar_tim.clear()
        self.riwayat_pertandingan.clear()


# ============================================================
# FRONTEND / GUI TKINTER + TTKBOOTSTRAP
# ============================================================

class EsportsTournamentApp:
    def __init__(self, root: tb.Window) -> None:
        self.root = root
        self.root.title("Aplikasi Turnamen Esports - Tkinter & ttkbootstrap")
        self.root.geometry("1280x760")
        self.root.minsize(1100, 680)

        self.turnamen = Turnamen()
        self.style = tb.Style()
        self.style.configure("Treeview", rowheight=28)
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        self.status_var = tk.StringVar(value="Siap digunakan.")

        self._build_layout()
        self._refresh_all()

    # ---------------------- LAYOUT UTAMA ----------------------
    def _build_layout(self) -> None:
        main = tb.Frame(self.root, padding=12)
        main.pack(fill=BOTH, expand=True)

        header = tb.Frame(main)
        header.pack(fill=X, pady=(0, 10))

        title_box = tb.Frame(header)
        title_box.pack(side=LEFT, fill=X, expand=True)

        tb.Label(
            title_box,
            text="🏆 Aplikasi Manajemen Turnamen Esports",
            font=("Segoe UI", 18, "bold"),
            bootstyle="primary",
        ).pack(anchor=W)
        tb.Label(
            title_box,
            text="Versi desktop berbasis Tkinter, ttkbootstrap, dan pandas",
            font=("Segoe UI", 10),
        ).pack(anchor=W)

        tb.Button(header, text="Isi Data Contoh", bootstyle="secondary-outline", command=self._load_sample_data).pack(side=RIGHT, padx=(8, 0))
        tb.Button(header, text="Reset Semua", bootstyle="danger-outline", command=self._reset_data).pack(side=RIGHT)

        self.notebook = tb.Notebook(main, bootstyle="primary")
        self.notebook.pack(fill=BOTH, expand=True)

        self.tab_dashboard = tb.Frame(self.notebook, padding=10)
        self.tab_tim = tb.Frame(self.notebook, padding=10)
        self.tab_pemain = tb.Frame(self.notebook, padding=10)
        self.tab_match = tb.Frame(self.notebook, padding=10)
        self.tab_stat_pemain = tb.Frame(self.notebook, padding=10)
        self.tab_search_sort = tb.Frame(self.notebook, padding=10)
        self.tab_export = tb.Frame(self.notebook, padding=10)

        self.notebook.add(self.tab_dashboard, text="Dashboard")
        self.notebook.add(self.tab_tim, text="Data Tim")
        self.notebook.add(self.tab_pemain, text="Data Pemain")
        self.notebook.add(self.tab_match, text="Pertandingan")
        self.notebook.add(self.tab_stat_pemain, text="Statistik Pemain")
        self.notebook.add(self.tab_search_sort, text="Search & Sort")
        self.notebook.add(self.tab_export, text="Export")

        self._build_dashboard_tab()
        self._build_tim_tab()
        self._build_pemain_tab()
        self._build_match_tab()
        self._build_stat_pemain_tab()
        self._build_search_sort_tab()
        self._build_export_tab()

        status = tb.Label(
            main,
            textvariable=self.status_var,
            anchor=W,
            bootstyle="inverse-secondary",
            padding=(10, 5),
        )
        status.pack(fill=X, pady=(10, 0))

    def _build_dashboard_tab(self) -> None:
        cards = tb.Frame(self.tab_dashboard)
        cards.pack(fill=X, pady=(0, 10))

        self.card_total_tim = self._make_card(cards, "Total Tim", "0", "primary")
        self.card_total_pemain = self._make_card(cards, "Total Pemain", "0", "success")
        self.card_total_match = self._make_card(cards, "Total Match", "0", "warning")
        self.card_best_team = self._make_card(cards, "Tim Terbaik", "-", "info")

        body = tb.Panedwindow(self.tab_dashboard, orient=HORIZONTAL)
        body.pack(fill=BOTH, expand=True)

        left = tb.Labelframe(body, text="Papan Klasemen", padding=8, bootstyle="primary")
        right = tb.Labelframe(body, text="Ringkasan Performa Terbaik", padding=8, bootstyle="info")
        body.add(left, weight=3)
        body.add(right, weight=2)

        self.tree_dashboard = self._make_tree(
            left,
            columns=["Nama Tim", "Main", "Menang", "Kalah", "Seri", "Win Rate (%)", "Selisih Skor", "Jumlah Pemain"],
            height=18,
        )

        self.summary_text = tk.Text(right, height=18, wrap="word", font=("Segoe UI", 10))
        self.summary_text.pack(fill=BOTH, expand=True)
        self.summary_text.configure(state="disabled")

    def _build_tim_tab(self) -> None:
        left = tb.Labelframe(self.tab_tim, text="Form Data Tim", padding=10, bootstyle="primary")
        left.pack(side=LEFT, fill=Y, padx=(0, 10))

        right = tb.Labelframe(self.tab_tim, text="Tabel Data Tim", padding=8, bootstyle="secondary")
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.tim_nama_var = tk.StringVar()
        self.tim_nama_baru_var = tk.StringVar()

        tb.Label(left, text="Nama Tim").pack(anchor=W)
        self.entry_tim_nama = tb.Entry(left, textvariable=self.tim_nama_var, width=32)
        self.entry_tim_nama.pack(fill=X, pady=(3, 10))

        tb.Label(left, text="Nama Baru (untuk edit)").pack(anchor=W)
        tb.Entry(left, textvariable=self.tim_nama_baru_var, width=32).pack(fill=X, pady=(3, 10))

        tb.Button(left, text="Tambah Tim", bootstyle="success", command=self._aksi_tambah_tim).pack(fill=X, pady=3)
        tb.Button(left, text="Ubah Nama Tim", bootstyle="warning", command=self._aksi_ubah_tim).pack(fill=X, pady=3)
        tb.Button(left, text="Hapus Tim", bootstyle="danger", command=self._aksi_hapus_tim).pack(fill=X, pady=3)
        tb.Button(left, text="Kosongkan Form", bootstyle="secondary-outline", command=self._clear_tim_form).pack(fill=X, pady=(15, 3))

        tb.Separator(left).pack(fill=X, pady=12)
        tb.Label(
            left,
            text="Catatan: klik baris pada tabel untuk mengisi form otomatis.",
            wraplength=220,
            justify=LEFT,
        ).pack(anchor=W)

        self.tree_tim = self._make_tree(
            right,
            columns=["Nama Tim", "Main", "Menang", "Kalah", "Seri", "Win Rate (%)", "Skor Tim", "Skor Musuh", "Selisih Skor", "Jumlah Pemain"],
            height=20,
        )
        self.tree_tim.bind("<<TreeviewSelect>>", self._on_select_tim)

    def _build_pemain_tab(self) -> None:
        left = tb.Labelframe(self.tab_pemain, text="Form Data Pemain", padding=10, bootstyle="success")
        left.pack(side=LEFT, fill=Y, padx=(0, 10))

        right = tb.Labelframe(self.tab_pemain, text="Tabel Data Pemain", padding=8, bootstyle="secondary")
        right.pack(side=LEFT, fill=BOTH, expand=True)

        self.pemain_nama_var = tk.StringVar()
        self.pemain_nama_baru_var = tk.StringVar()
        self.pemain_tim_var = tk.StringVar()

        tb.Label(left, text="Tim Pemain").pack(anchor=W)
        self.combo_pemain_tim = tb.Combobox(left, textvariable=self.pemain_tim_var, state="readonly", width=30)
        self.combo_pemain_tim.pack(fill=X, pady=(3, 10))

        tb.Label(left, text="Nama Pemain").pack(anchor=W)
        tb.Entry(left, textvariable=self.pemain_nama_var, width=32).pack(fill=X, pady=(3, 10))

        tb.Label(left, text="Nama Baru (untuk edit)").pack(anchor=W)
        tb.Entry(left, textvariable=self.pemain_nama_baru_var, width=32).pack(fill=X, pady=(3, 10))

        tb.Button(left, text="Tambah Pemain", bootstyle="success", command=self._aksi_tambah_pemain).pack(fill=X, pady=3)
        tb.Button(left, text="Ubah Nama Pemain", bootstyle="warning", command=self._aksi_ubah_pemain).pack(fill=X, pady=3)
        tb.Button(left, text="Hapus Pemain", bootstyle="danger", command=self._aksi_hapus_pemain).pack(fill=X, pady=3)
        tb.Button(left, text="Kosongkan Form", bootstyle="secondary-outline", command=self._clear_pemain_form).pack(fill=X, pady=(15, 3))

        self.tree_pemain = self._make_tree(
            right,
            columns=["Nama Pemain", "Tim", "Match", "Kill", "Assist", "Death", "KDA", "Rata-rata Kill"],
            height=20,
        )
        self.tree_pemain.bind("<<TreeviewSelect>>", self._on_select_pemain)

    def _build_match_tab(self) -> None:
        form = tb.Labelframe(self.tab_match, text="Input Hasil Pertandingan", padding=10, bootstyle="warning")
        form.pack(fill=X, pady=(0, 10))

        table_box = tb.Labelframe(self.tab_match, text="Riwayat Pertandingan", padding=8, bootstyle="secondary")
        table_box.pack(fill=BOTH, expand=True)

        self.match_tim1_var = tk.StringVar()
        self.match_tim2_var = tk.StringVar()
        self.match_skor1_var = tk.StringVar(value="0")
        self.match_skor2_var = tk.StringVar(value="0")

        row = tb.Frame(form)
        row.pack(fill=X)

        tb.Label(row, text="Tim 1").grid(row=0, column=0, sticky=W, padx=(0, 6))
        self.combo_match_tim1 = tb.Combobox(row, textvariable=self.match_tim1_var, state="readonly", width=26)
        self.combo_match_tim1.grid(row=1, column=0, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Skor 1").grid(row=0, column=1, sticky=W, padx=(0, 6))
        tb.Spinbox(row, from_=0, to=999, textvariable=self.match_skor1_var, width=8).grid(row=1, column=1, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Tim 2").grid(row=0, column=2, sticky=W, padx=(0, 6))
        self.combo_match_tim2 = tb.Combobox(row, textvariable=self.match_tim2_var, state="readonly", width=26)
        self.combo_match_tim2.grid(row=1, column=2, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Skor 2").grid(row=0, column=3, sticky=W, padx=(0, 6))
        tb.Spinbox(row, from_=0, to=999, textvariable=self.match_skor2_var, width=8).grid(row=1, column=3, sticky=EW, padx=(0, 10), pady=4)

        tb.Button(row, text="Simpan Match", bootstyle="primary", command=self._aksi_tambah_match).grid(row=1, column=4, padx=(0, 8), pady=4)
        tb.Button(row, text="Hapus Match Terpilih", bootstyle="danger-outline", command=self._aksi_hapus_match).grid(row=1, column=5, pady=4)

        for col in range(6):
            row.columnconfigure(col, weight=1)

        self.tree_match = self._make_tree(
            table_box,
            columns=["No", "Tim 1", "Skor 1", "Tim 2", "Skor 2", "Pemenang"],
            height=18,
        )

    def _build_stat_pemain_tab(self) -> None:
        form = tb.Labelframe(self.tab_stat_pemain, text="Input Statistik Pemain per Match", padding=10, bootstyle="primary")
        form.pack(fill=X, pady=(0, 10))

        table_box = tb.Labelframe(self.tab_stat_pemain, text="Ranking Statistik Pemain", padding=8, bootstyle="secondary")
        table_box.pack(fill=BOTH, expand=True)

        self.stat_tim_var = tk.StringVar()
        self.stat_pemain_var = tk.StringVar()
        self.stat_kill_var = tk.StringVar(value="0")
        self.stat_assist_var = tk.StringVar(value="0")
        self.stat_death_var = tk.StringVar(value="0")

        row = tb.Frame(form)
        row.pack(fill=X)

        tb.Label(row, text="Tim").grid(row=0, column=0, sticky=W, padx=(0, 6))
        self.combo_stat_tim = tb.Combobox(row, textvariable=self.stat_tim_var, state="readonly", width=24)
        self.combo_stat_tim.grid(row=1, column=0, sticky=EW, padx=(0, 10), pady=4)
        self.combo_stat_tim.bind("<<ComboboxSelected>>", lambda _e: self._update_player_comboboxes())

        tb.Label(row, text="Pemain").grid(row=0, column=1, sticky=W, padx=(0, 6))
        self.combo_stat_pemain = tb.Combobox(row, textvariable=self.stat_pemain_var, state="readonly", width=24)
        self.combo_stat_pemain.grid(row=1, column=1, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Kill").grid(row=0, column=2, sticky=W, padx=(0, 6))
        tb.Spinbox(row, from_=0, to=999, textvariable=self.stat_kill_var, width=8).grid(row=1, column=2, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Assist").grid(row=0, column=3, sticky=W, padx=(0, 6))
        tb.Spinbox(row, from_=0, to=999, textvariable=self.stat_assist_var, width=8).grid(row=1, column=3, sticky=EW, padx=(0, 10), pady=4)

        tb.Label(row, text="Death").grid(row=0, column=4, sticky=W, padx=(0, 6))
        tb.Spinbox(row, from_=0, to=999, textvariable=self.stat_death_var, width=8).grid(row=1, column=4, sticky=EW, padx=(0, 10), pady=4)

        tb.Button(row, text="Input Statistik", bootstyle="success", command=self._aksi_input_statistik).grid(row=1, column=5, padx=(0, 8), pady=4)
        tb.Button(row, text="Reset Input", bootstyle="secondary-outline", command=self._clear_stat_form).grid(row=1, column=6, pady=4)

        for col in range(7):
            row.columnconfigure(col, weight=1)

        self.tree_stat_pemain = self._make_tree(
            table_box,
            columns=["Nama Pemain", "Tim", "Match", "Kill", "Assist", "Death", "KDA", "Rata-rata Kill"],
            height=18,
        )

    def _build_search_sort_tab(self) -> None:
        top = tb.Panedwindow(self.tab_search_sort, orient=VERTICAL)
        top.pack(fill=BOTH, expand=True)

        search_box = tb.Labelframe(top, text="Pencarian Tim", padding=10, bootstyle="info")
        sort_box = tb.Labelframe(top, text="Pengurutan Tim", padding=10, bootstyle="warning")
        top.add(search_box, weight=1)
        top.add(sort_box, weight=2)

        self.search_nama_var = tk.StringVar()
        self.search_metode_var = tk.StringVar(value="Sequential Search")

        row_search = tb.Frame(search_box)
        row_search.pack(fill=X, pady=(0, 8))

        tb.Label(row_search, text="Nama Tim").pack(side=LEFT, padx=(0, 5))
        tb.Entry(row_search, textvariable=self.search_nama_var, width=32).pack(side=LEFT, padx=(0, 10))
        tb.Combobox(
            row_search,
            textvariable=self.search_metode_var,
            values=["Sequential Search", "Binary Search"],
            state="readonly",
            width=24,
        ).pack(side=LEFT, padx=(0, 10))
        tb.Button(row_search, text="Cari", bootstyle="info", command=self._aksi_cari_tim).pack(side=LEFT)

        self.tree_search = self._make_tree(
            search_box,
            columns=["Nama Tim", "Main", "Menang", "Kalah", "Seri", "Win Rate (%)", "Selisih Skor", "Jumlah Pemain"],
            height=4,
        )

        self.sort_metode_var = tk.StringVar(value="Selection Sort")
        self.sort_acuan_var = tk.StringVar(value="Jumlah Kemenangan")

        row_sort = tb.Frame(sort_box)
        row_sort.pack(fill=X, pady=(0, 8))

        tb.Label(row_sort, text="Algoritma").pack(side=LEFT, padx=(0, 5))
        tb.Combobox(
            row_sort,
            textvariable=self.sort_metode_var,
            values=["Selection Sort", "Insertion Sort"],
            state="readonly",
            width=20,
        ).pack(side=LEFT, padx=(0, 10))

        tb.Label(row_sort, text="Acuan").pack(side=LEFT, padx=(0, 5))
        tb.Combobox(
            row_sort,
            textvariable=self.sort_acuan_var,
            values=["Jumlah Kemenangan", "Selisih Skor", "Win Rate", "Rata-rata Skor"],
            state="readonly",
            width=20,
        ).pack(side=LEFT, padx=(0, 10))

        tb.Button(row_sort, text="Urutkan", bootstyle="warning", command=self._aksi_sort_tim).pack(side=LEFT)

        self.tree_sort = self._make_tree(
            sort_box,
            columns=["Nama Tim", "Main", "Menang", "Kalah", "Seri", "Win Rate (%)", "Skor Tim", "Skor Musuh", "Selisih Skor", "Rata-rata Skor", "Jumlah Pemain"],
            height=10,
        )

    def _build_export_tab(self) -> None:
        box = tb.Labelframe(self.tab_export, text="Export Laporan dengan pandas", padding=14, bootstyle="success")
        box.pack(fill=X, anchor=N)

        tb.Label(
            box,
            text="Gunakan menu ini untuk menyimpan data klasemen, pemain, dan riwayat pertandingan.",
            font=("Segoe UI", 10),
        ).pack(anchor=W, pady=(0, 10))

        tb.Button(
            box,
            text="Export ke Excel (.xlsx)",
            bootstyle="success",
            command=self._export_excel,
            width=28,
        ).pack(anchor=W, pady=4)

        tb.Button(
            box,
            text="Export ke Folder CSV",
            bootstyle="primary-outline",
            command=self._export_csv_folder,
            width=28,
        ).pack(anchor=W, pady=4)

        tb.Button(
            box,
            text="Preview Data di Terminal",
            bootstyle="secondary-outline",
            command=self._preview_terminal,
            width=28,
        ).pack(anchor=W, pady=4)

    # ---------------------- WIDGET HELPER ----------------------
    def _make_card(self, parent: tk.Widget, title: str, value: str, style_name: str) -> tk.StringVar:
        frame = tb.Frame(parent, padding=12)
        frame.pack(side=LEFT, fill=X, expand=True, padx=(0, 8))

        value_var = tk.StringVar(value=value)
        tb.Label(frame, text=title, font=("Segoe UI", 9), bootstyle=style_name).pack(anchor=W)
        tb.Label(frame, textvariable=value_var, font=("Segoe UI", 18, "bold"), bootstyle=style_name).pack(anchor=W)
        return value_var

    def _make_tree(self, parent: tk.Widget, columns: list[str], height: int = 10) -> ttk.Treeview:
        frame = tb.Frame(parent)
        frame.pack(fill=BOTH, expand=True)

        tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
        y_scroll = tb.Scrollbar(frame, orient=VERTICAL, command=tree.yview)
        x_scroll = tb.Scrollbar(frame, orient=HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

        for col in columns:
            tree.heading(col, text=col)
            width = self._guess_column_width(col)
            anchor = CENTER if col not in {"Nama Tim", "Nama Pemain", "Tim", "Tim 1", "Tim 2", "Pemenang"} else W
            tree.column(col, width=width, minwidth=80, anchor=anchor, stretch=True)

        tree.grid(row=0, column=0, sticky=NSEW)
        y_scroll.grid(row=0, column=1, sticky=NS)
        x_scroll.grid(row=1, column=0, sticky=EW)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    @staticmethod
    def _guess_column_width(col: str) -> int:
        widths = {
            "Nama Tim": 170,
            "Nama Pemain": 170,
            "Tim": 140,
            "Tim 1": 150,
            "Tim 2": 150,
            "Pemenang": 150,
            "Rata-rata Kill": 120,
            "Rata-rata Skor": 120,
            "Jumlah Pemain": 120,
            "Win Rate (%)": 120,
            "Selisih Skor": 120,
        }
        return widths.get(col, 95)

    def _set_tree_data(self, tree: ttk.Treeview, df: pd.DataFrame) -> None:
        tree.delete(*tree.get_children())
        columns = list(tree["columns"])
        if df.empty:
            return

        for _, row in df.iterrows():
            values = [row[col] if col in df.columns else "" for col in columns]
            tree.insert("", tk.END, values=values)

    def _tim_to_df(self, tim: Tim) -> pd.DataFrame:
        return pd.DataFrame([{
            "Nama Tim": tim.nama,
            "Main": tim.total_match,
            "Menang": tim.menang,
            "Kalah": tim.kalah,
            "Seri": tim.seri,
            "Win Rate (%)": tim.win_rate,
            "Skor Tim": tim.skor_pribadi,
            "Skor Musuh": tim.skor_musuh,
            "Selisih Skor": tim.selisih_skor,
            "Rata-rata Skor": tim.rata_skor,
            "Jumlah Pemain": len(tim.daftar_pemain),
        }])

    @staticmethod
    def _to_int(value: str, field_name: str) -> int:
        try:
            angka = int(str(value).strip())
        except ValueError as exc:
            raise ValueError(f"{field_name} harus berupa angka bulat.") from exc
        if angka < 0:
            raise ValueError(f"{field_name} tidak boleh negatif.")
        return angka

    # ---------------------- REFRESH ----------------------
    def _refresh_all(self) -> None:
        self._refresh_dashboard()
        self._refresh_tables()
        self._refresh_comboboxes()

    def _refresh_dashboard(self) -> None:
        total_tim = len(self.turnamen.daftar_tim)
        total_pemain = len(self.turnamen.get_semua_pemain())
        total_match = len(self.turnamen.riwayat_pertandingan)
        tim_terbaik = self.turnamen.get_tim_terbaik()
        pemain_kda = self.turnamen.get_pemain_terbaik_kda()
        pemain_kill = self.turnamen.get_pemain_top_kill()

        self.card_total_tim.set(str(total_tim))
        self.card_total_pemain.set(str(total_pemain))
        self.card_total_match.set(str(total_match))
        self.card_best_team.set(tim_terbaik.nama if tim_terbaik else "-")

        self._set_tree_data(self.tree_dashboard, self.turnamen.df_klasemen())

        lines = []
        if tim_terbaik:
            lines.append("🥇 TIM TERBAIK")
            lines.append(f"Nama       : {tim_terbaik.nama}")
            lines.append(f"Win Rate   : {tim_terbaik.win_rate}%")
            lines.append(f"Rekor      : {tim_terbaik.menang}M / {tim_terbaik.kalah}K / {tim_terbaik.seri}S")
            lines.append(f"Skor       : {tim_terbaik.skor_pribadi} - {tim_terbaik.skor_musuh}")
            lines.append(f"Selisih    : {tim_terbaik.selisih_skor}")
        else:
            lines.append("🥇 TIM TERBAIK")
            lines.append("Belum ada data pertandingan.")

        lines.append("")
        if pemain_kda:
            lines.append("🎖️ PEMAIN KDA TERBAIK")
            lines.append(f"Nama       : {pemain_kda.nama} [{pemain_kda.nama_tim}]")
            lines.append(f"KDA        : {pemain_kda.kda}")
            lines.append(f"K/A/D      : {pemain_kda.kill}/{pemain_kda.assist}/{pemain_kda.death}")
            lines.append(f"Match      : {pemain_kda.jumlah_match}")
        else:
            lines.append("🎖️ PEMAIN KDA TERBAIK")
            lines.append("Belum ada statistik pemain.")

        lines.append("")
        if pemain_kill:
            lines.append("💀 TOP FRAGGER")
            lines.append(f"Nama       : {pemain_kill.nama} [{pemain_kill.nama_tim}]")
            lines.append(f"Total Kill : {pemain_kill.kill}")
            lines.append(f"Avg Kill   : {pemain_kill.rata_kill}")
        else:
            lines.append("💀 TOP FRAGGER")
            lines.append("Belum ada statistik pemain.")

        self.summary_text.configure(state="normal")
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert(tk.END, "\n".join(lines))
        self.summary_text.configure(state="disabled")

    def _refresh_tables(self) -> None:
        df_klasemen = self.turnamen.df_klasemen()
        df_pemain = self.turnamen.df_pemain()
        df_match = self.turnamen.df_riwayat()

        self._set_tree_data(self.tree_tim, df_klasemen)
        self._set_tree_data(self.tree_pemain, df_pemain)
        self._set_tree_data(self.tree_match, df_match)
        self._set_tree_data(self.tree_stat_pemain, df_pemain)

    def _refresh_comboboxes(self) -> None:
        nama_tim = [tim.nama for tim in self.turnamen.daftar_tim]
        combo_tim = [
            self.combo_pemain_tim,
            self.combo_match_tim1,
            self.combo_match_tim2,
            self.combo_stat_tim,
        ]
        for combo in combo_tim:
            combo["values"] = nama_tim

        for var in [self.pemain_tim_var, self.match_tim1_var, self.match_tim2_var, self.stat_tim_var]:
            if var.get() and var.get() not in nama_tim:
                var.set("")

        self._update_player_comboboxes()

    def _update_player_comboboxes(self) -> None:
        nama_tim = self.stat_tim_var.get().strip()
        tim = self.turnamen._cari_tim_objek(nama_tim) if nama_tim else None
        daftar_pemain = [p.nama for p in tim.daftar_pemain] if tim else []
        self.combo_stat_pemain["values"] = daftar_pemain
        if self.stat_pemain_var.get() not in daftar_pemain:
            self.stat_pemain_var.set("")

    def _notify(self, sukses: bool, pesan: str, popup_error: bool = True) -> None:
        prefix = "✅" if sukses else "❌"
        self.status_var.set(f"{prefix} {pesan}")
        if not sukses and popup_error:
            messagebox.showerror("Gagal", pesan)

    # ---------------------- EVENT TIM ----------------------
    def _aksi_tambah_tim(self) -> None:
        sukses, pesan = self.turnamen.tambah_tim(self.tim_nama_var.get())
        if sukses:
            self._clear_tim_form()
        self._refresh_all()
        self._notify(sukses, pesan)

    def _aksi_ubah_tim(self) -> None:
        sukses, pesan = self.turnamen.ubah_tim(self.tim_nama_var.get(), self.tim_nama_baru_var.get())
        if sukses:
            self._clear_tim_form()
        self._refresh_all()
        self._notify(sukses, pesan)

    def _aksi_hapus_tim(self) -> None:
        nama = self.tim_nama_var.get().strip()
        if not nama:
            nama = self._get_selected_value(self.tree_tim, "Nama Tim")
        if not nama:
            self._notify(False, "Pilih atau isi nama tim yang ingin dihapus.")
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus tim '{nama}' beserta riwayat pertandingannya?"):
            return
        sukses, pesan = self.turnamen.hapus_tim(nama)
        if sukses:
            self._clear_tim_form()
        self._refresh_all()
        self._notify(sukses, pesan)

    def _on_select_tim(self, _event=None) -> None:
        nama = self._get_selected_value(self.tree_tim, "Nama Tim")
        if nama:
            self.tim_nama_var.set(nama)
            self.tim_nama_baru_var.set(nama)

    def _clear_tim_form(self) -> None:
        self.tim_nama_var.set("")
        self.tim_nama_baru_var.set("")
        self.entry_tim_nama.focus_set()

    # ---------------------- EVENT PEMAIN ----------------------
    def _aksi_tambah_pemain(self) -> None:
        sukses, pesan = self.turnamen.tambah_pemain(self.pemain_nama_var.get(), self.pemain_tim_var.get())
        if sukses:
            self.pemain_nama_var.set("")
            self.pemain_nama_baru_var.set("")
        self._refresh_all()
        self._notify(sukses, pesan)

    def _aksi_ubah_pemain(self) -> None:
        sukses, pesan = self.turnamen.ubah_pemain(
            self.pemain_nama_var.get(),
            self.pemain_nama_baru_var.get(),
            self.pemain_tim_var.get(),
        )
        if sukses:
            self._clear_pemain_form()
        self._refresh_all()
        self._notify(sukses, pesan)

    def _aksi_hapus_pemain(self) -> None:
        nama = self.pemain_nama_var.get().strip()
        tim = self.pemain_tim_var.get().strip()
        if not nama:
            nama = self._get_selected_value(self.tree_pemain, "Nama Pemain")
        if not tim:
            tim = self._get_selected_value(self.tree_pemain, "Tim")
        if not nama or not tim:
            self._notify(False, "Pilih atau isi data pemain yang ingin dihapus.")
            return
        if not messagebox.askyesno("Konfirmasi", f"Hapus pemain '{nama}' dari tim '{tim}'?"):
            return
        sukses, pesan = self.turnamen.hapus_pemain(nama, tim)
        if sukses:
            self._clear_pemain_form()
        self._refresh_all()
        self._notify(sukses, pesan)

    def _on_select_pemain(self, _event=None) -> None:
        nama = self._get_selected_value(self.tree_pemain, "Nama Pemain")
        tim = self._get_selected_value(self.tree_pemain, "Tim")
        if nama and tim:
            self.pemain_nama_var.set(nama)
            self.pemain_nama_baru_var.set(nama)
            self.pemain_tim_var.set(tim)

    def _clear_pemain_form(self) -> None:
        self.pemain_nama_var.set("")
        self.pemain_nama_baru_var.set("")
        self.pemain_tim_var.set("")

    # ---------------------- EVENT MATCH ----------------------
    def _aksi_tambah_match(self) -> None:
        try:
            skor1 = self._to_int(self.match_skor1_var.get(), "Skor 1")
            skor2 = self._to_int(self.match_skor2_var.get(), "Skor 2")
        except ValueError as exc:
            self._notify(False, str(exc))
            return

        sukses, pesan = self.turnamen.tambah_pertandingan(
            self.match_tim1_var.get(),
            skor1,
            self.match_tim2_var.get(),
            skor2,
        )
        if sukses:
            self.match_skor1_var.set("0")
            self.match_skor2_var.set("0")
        self._refresh_all()
        self._notify(sukses, pesan)

    def _aksi_hapus_match(self) -> None:
        selected = self.tree_match.selection()
        if not selected:
            self._notify(False, "Pilih riwayat pertandingan yang ingin dihapus.")
            return

        no_match = self._get_selected_value(self.tree_match, "No")
        try:
            index = int(no_match) - 1
        except (TypeError, ValueError):
            self._notify(False, "Nomor pertandingan tidak valid.")
            return

        if not messagebox.askyesno("Konfirmasi", f"Hapus pertandingan nomor {no_match}?"):
            return

        sukses, pesan = self.turnamen.hapus_pertandingan(index)
        self._refresh_all()
        self._notify(sukses, pesan)

    # ---------------------- EVENT STATISTIK PEMAIN ----------------------
    def _aksi_input_statistik(self) -> None:
        try:
            kill = self._to_int(self.stat_kill_var.get(), "Kill")
            assist = self._to_int(self.stat_assist_var.get(), "Assist")
            death = self._to_int(self.stat_death_var.get(), "Death")
        except ValueError as exc:
            self._notify(False, str(exc))
            return

        sukses, pesan = self.turnamen.input_statistik_pemain(
            self.stat_pemain_var.get(),
            self.stat_tim_var.get(),
            kill,
            assist,
            death,
        )
        if sukses:
            self.stat_kill_var.set("0")
            self.stat_assist_var.set("0")
            self.stat_death_var.set("0")
        self._refresh_all()
        self._notify(sukses, pesan)

    def _clear_stat_form(self) -> None:
        self.stat_pemain_var.set("")
        self.stat_kill_var.set("0")
        self.stat_assist_var.set("0")
        self.stat_death_var.set("0")

    # ---------------------- EVENT SEARCH & SORT ----------------------
    def _aksi_cari_tim(self) -> None:
        nama = self.search_nama_var.get().strip()
        if not nama:
            self._notify(False, "Masukkan nama tim yang ingin dicari.")
            return

        if self.search_metode_var.get() == "Sequential Search":
            hasil = self.turnamen.sequential_search(nama)
        else:
            hasil = self.turnamen.binary_search(nama)

        if hasil:
            self._set_tree_data(self.tree_search, self._tim_to_df(hasil))
            self._notify(True, f"Tim '{hasil.nama}' ditemukan menggunakan {self.search_metode_var.get()}.", popup_error=False)
        else:
            self._set_tree_data(self.tree_search, pd.DataFrame())
            self._notify(False, f"Tim '{nama}' tidak ditemukan.", popup_error=False)

    def _aksi_sort_tim(self) -> None:
        if not self.turnamen.daftar_tim:
            self._notify(False, "Belum ada data tim untuk diurutkan.")
            return

        mapping_acuan = {
            "Jumlah Kemenangan": "menang",
            "Selisih Skor": "selisih",
            "Win Rate": "winrate",
            "Rata-rata Skor": "rata_skor",
        }
        acuan = mapping_acuan.get(self.sort_acuan_var.get(), "menang")

        if self.sort_metode_var.get() == "Selection Sort":
            hasil = self.turnamen.selection_sort(acuan)
        else:
            hasil = self.turnamen.insertion_sort(acuan)

        self._set_tree_data(self.tree_sort, self.turnamen.df_klasemen(hasil))
        self._notify(True, f"Data berhasil diurutkan dengan {self.sort_metode_var.get()} berdasarkan {self.sort_acuan_var.get()}.", popup_error=False)

    # ---------------------- EXPORT ----------------------
    def _export_excel(self) -> None:
        path = filedialog.asksaveasfilename(
            title="Simpan laporan Excel",
            defaultextension=".xlsx",
            filetypes=[("Excel Workbook", "*.xlsx")],
        )
        if not path:
            return

        try:
            with pd.ExcelWriter(path, engine="openpyxl") as writer:
                self.turnamen.df_klasemen().to_excel(writer, sheet_name="Klasemen", index=False)
                self.turnamen.df_pemain().to_excel(writer, sheet_name="Pemain", index=False)
                self.turnamen.df_riwayat().to_excel(writer, sheet_name="Riwayat Match", index=False)
            self._notify(True, f"Laporan Excel berhasil disimpan: {path}", popup_error=False)
            messagebox.showinfo("Sukses", "Laporan Excel berhasil disimpan.")
        except Exception as exc:  # noqa: BLE001 - pesan error perlu ditampilkan ke user GUI
            self._notify(False, f"Gagal export Excel: {exc}")

    def _export_csv_folder(self) -> None:
        folder = filedialog.askdirectory(title="Pilih folder export CSV")
        if not folder:
            return

        try:
            self.turnamen.df_klasemen().to_csv(os.path.join(folder, "klasemen.csv"), index=False)
            self.turnamen.df_pemain().to_csv(os.path.join(folder, "pemain.csv"), index=False)
            self.turnamen.df_riwayat().to_csv(os.path.join(folder, "riwayat_pertandingan.csv"), index=False)
            self._notify(True, f"File CSV berhasil disimpan di folder: {folder}", popup_error=False)
            messagebox.showinfo("Sukses", "CSV berhasil diexport.")
        except Exception as exc:  # noqa: BLE001
            self._notify(False, f"Gagal export CSV: {exc}")

    def _preview_terminal(self) -> None:
        print("\n=== KLASEMEN ===")
        print(self.turnamen.df_klasemen())
        print("\n=== PEMAIN ===")
        print(self.turnamen.df_pemain())
        print("\n=== RIWAYAT PERTANDINGAN ===")
        print(self.turnamen.df_riwayat())
        self._notify(True, "Preview data dikirim ke terminal.", popup_error=False)

    # ---------------------- DATA CONTOH / RESET ----------------------
    def _load_sample_data(self) -> None:
        if self.turnamen.daftar_tim:
            if not messagebox.askyesno("Konfirmasi", "Data saat ini akan diganti dengan data contoh. Lanjutkan?"):
                return
        self.turnamen.reset()

        for tim in ["EVOS", "RRQ", "ONIC", "BTR", "Alter Ego"]:
            self.turnamen.tambah_tim(tim)

        contoh_pemain = [
            ("Dreams", "EVOS"), ("Branz", "EVOS"),
            ("Lemon", "RRQ"), ("Skylar", "RRQ"),
            ("Kairi", "ONIC"), ("Butsss", "ONIC"),
            ("Moreno", "BTR"), ("Kenn", "BTR"),
            ("Nino", "Alter Ego"), ("Udil", "Alter Ego"),
        ]
        for nama, tim in contoh_pemain:
            self.turnamen.tambah_pemain(nama, tim)

        match_data = [
            ("EVOS", 2, "RRQ", 1),
            ("ONIC", 2, "BTR", 0),
            ("Alter Ego", 1, "EVOS", 2),
            ("RRQ", 2, "BTR", 0),
            ("ONIC", 2, "Alter Ego", 1),
        ]
        for t1, s1, t2, s2 in match_data:
            self.turnamen.tambah_pertandingan(t1, s1, t2, s2)

        stat_data = [
            ("Dreams", "EVOS", 12, 18, 6),
            ("Branz", "EVOS", 25, 9, 8),
            ("Lemon", "RRQ", 18, 11, 7),
            ("Skylar", "RRQ", 23, 7, 9),
            ("Kairi", "ONIC", 30, 12, 5),
            ("Butsss", "ONIC", 14, 16, 6),
            ("Moreno", "BTR", 10, 9, 12),
            ("Kenn", "BTR", 16, 5, 11),
            ("Nino", "Alter Ego", 13, 8, 10),
            ("Udil", "Alter Ego", 11, 19, 9),
        ]
        for nama, tim, kill, assist, death in stat_data:
            self.turnamen.input_statistik_pemain(nama, tim, kill, assist, death)

        self._refresh_all()
        self._notify(True, "Data contoh berhasil dimuat.", popup_error=False)

    def _reset_data(self) -> None:
        if not messagebox.askyesno("Konfirmasi", "Hapus semua data turnamen?"):
            return
        self.turnamen.reset()
        self._clear_tim_form()
        self._clear_pemain_form()
        self._clear_stat_form()
        self.match_tim1_var.set("")
        self.match_tim2_var.set("")
        self.match_skor1_var.set("0")
        self.match_skor2_var.set("0")
        self.search_nama_var.set("")
        self._set_tree_data(self.tree_search, pd.DataFrame())
        self._set_tree_data(self.tree_sort, pd.DataFrame())
        self._refresh_all()
        self._notify(True, "Semua data berhasil direset.", popup_error=False)

    # ---------------------- TREE HELPER ----------------------
    def _get_selected_value(self, tree: ttk.Treeview, column_name: str) -> str:
        selected = tree.selection()
        if not selected:
            return ""
        values = tree.item(selected[0], "values")
        columns = list(tree["columns"])
        if column_name not in columns:
            return ""
        index = columns.index(column_name)
        if index >= len(values):
            return ""
        return str(values[index])


# ============================================================
# MAIN PROGRAM
# ============================================================

def main() -> None:
    root = tb.Window(themename="flatly")
    EsportsTournamentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
