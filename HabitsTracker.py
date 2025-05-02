"""
HabitsTracker - 習慣追跡アプリケーション

このアプリケーションは、日々の習慣を追跡し視覚化するためのシンプルなカレンダーベースの
トラッキングツールです。ユーザーは習慣を定義し、各日にちごとに完了状態を
トグルすることができます。

主な機能:
- 月別カレンダービュー
- 最大10個の習慣を追跡可能
- データの自動保存と読み込み
- シンプルな視覚的フィードバック

作成者: CatCatDogDog3150
日付: 2025-05-02
"""

import tkinter as tk
from tkinter import messagebox
import calendar
import pickle
import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from functools import partial


# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler("habits_tracker.log"), logging.StreamHandler()]
)
logger = logging.getLogger("HabitsTracker")


class AppConfig:
    """アプリケーション全体の設定を管理するクラス"""
    
    # アプリの基本設定
    APP_TITLE = "HabitsTracker"
    WINDOW_SIZE = "1400x800"
    
    # カレンダー表示の設定
    MAX_HABIT_ROWS = 10
    START_ROW_INDEX = 2
    MAX_DAYS = 31
    YEAR_RANGE = range(2020, 2026)
    
    # UI関連の設定
    FONT_NORMAL = ("Arial", 12)
    FONT_HEADER = ("Arial", 16)
    ENTRY_WIDTH = 20
    CELL_WIDTH = 5
    CELL_HEIGHT = 2
    
    # 色の設定
    COLOR_COMPLETED = "light green"
    COLOR_DEFAULT = "white"
    
    # ステータスメッセージ
    STATUS_SAVED = "データを保存しました: {}年{}月"
    STATUS_SAVE_ERROR = "データ保存に失敗しました"
    STATUS_EMPTY_DATA = "保存データの収集に失敗しました"
    STATUS_NO_HABITS = "習慣が設定されていません。習慣名を入力してください。"
    STATUS_HABITS_LIST = "習慣一覧: {}"
    STATUS_DATE_FORMAT = "{}月{}日"
    STATUS_HABIT_DATE = "習慣: {} - {}"
    STATUS_HABIT_ONLY = "習慣: {}"
    STATUS_HABIT_HINT = "ここに習慣名を入力してください"
    STATUS_INVALID_DATE = "無効な日付です。再度選択してください。"
    STATUS_INVALID_INPUT = "入力値が無効です。数値を入力してください。"
    

class DataManager:
    """データの保存と読み込みを担当するクラス"""
    
    def __init__(self):
        """DataManagerの初期化"""
        # データ保存用ディレクトリの確認と作成
        os.makedirs("data", exist_ok=True)
    
    def save_data(self, year: int, month: int, data: List[List[Dict[str, Any]]]) -> bool:
        """
        カレンダーデータをファイルに保存する
        
        Args:
            year: 保存する年
            month: 保存する月
            data: 保存するカレンダーデータ
            
        Returns:
            bool: 保存が成功したかどうか
        """
        if not data:
            logger.warning("保存しようとしたデータが空です")
            return False
            
        filename = self._get_filename(year, month)
        try:
            with open(filename, "wb") as file:
                pickle.dump(data, file)
            logger.info(f"データを保存しました: {filename}")
            return True
        except Exception as e:
            logger.error(f"データ保存中にエラーが発生しました: {e}")
            return False
    
    def load_data(self, year: int, month: int) -> List[List[Dict[str, Any]]]:
        """
        指定された年月のカレンダーデータを読み込む
        
        Args:
            year: 読み込む年
            month: 読み込む月
            
        Returns:
            List: カレンダーデータのリスト、ファイルがない場合は空リスト
        """
        filename = self._get_filename(year, month)
        if os.path.exists(filename):
            try:
                with open(filename, "rb") as file:
                    data = pickle.load(file)
                logger.info(f"データを読み込みました: {filename}")
                return data
            except Exception as e:
                logger.error(f"データ読み込み中にエラーが発生しました: {e}", exc_info=True)
        else:
            logger.info(f"データファイルが存在しません: {filename}")
        return []
    
    def _get_filename(self, year: int, month: int) -> str:
        """
        保存ファイル名を生成する
        
        Args:
            year: 年
            month: 月
            
        Returns:
            str: ファイル名
        """
        return f"data/habits_{year}_{month}.pkl"


class CalendarApp:
    """習慣追跡カレンダーアプリケーションのメインクラス"""
    
    def __init__(self, root: tk.Tk):
        """
        CalendarAppの初期化
        
        Args:
            root: Tkinterのルートウィンドウ
        """
        self.root = root
        self.config = AppConfig()
        self.data_manager = DataManager()
        
        # ウィンドウ設定
        self.root.title(self.config.APP_TITLE)
        self.root.geometry(self.config.WINDOW_SIZE)
        
        # ショートカットキーの設定
        self._setup_shortcuts()
        
        # ステータスバーのテキスト変数
        self.status_text = tk.StringVar()
        
        # 現在表示している年月
        self.current_year = datetime.now().year
        self.current_month = datetime.now().month
        
        # 初期化フラグ（初回表示時の保存を防ぐため）
        self.initialized = False
        
        # 習慣名を保持する辞書
        self.habit_entries = {}
        
        # UIの構築
        self._build_ui()
        
        # 初期カレンダー表示（データを読み込む）
        self._update_calendar(self.current_year, self.current_month, is_initial_load=True)
        
        # 初期化完了
        self.initialized = True
        
        # ウィンドウ閉じる時の処理を設定
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        # 常に習慣名を表示するために、習慣をステータスバーに表示
        self._display_all_habits()
        
        logger.info(f"アプリケーションを起動しました。初期表示: {self.current_year}年{self.current_month}月")
    
    def _setup_shortcuts(self) -> None:
        """キーボードショートカットを設定する"""
        # Ctrl+Sで保存
        self.root.bind("<Control-s>", lambda e: self._save_current_data())
        # 左右矢印キーで月の移動
        self.root.bind("<Left>", lambda e: self._change_month(-1))
        self.root.bind("<Right>", lambda e: self._change_month(1))
        # 上下矢印キーで年の移動
        self.root.bind("<Up>", lambda e: self._change_year(1))
        self.root.bind("<Down>", lambda e: self._change_year(-1))
    
    def _change_month(self, delta: int) -> None:
        """
        月を変更する
        
        Args:
            delta: 変更量（±1）
        """
        new_month = self.current_month + delta
        new_year = self.current_year
        
        # 年をまたぐ場合の処理
        if new_month < 1:
            new_month = 12
            new_year -= 1
        elif new_month > 12:
            new_month = 1
            new_year += 1
            
        # 年の範囲チェック
        if new_year not in self.config.YEAR_RANGE:
            return
            
        # 月の更新
        self.month_var.set(str(new_month))
        self.year_var.set(str(new_year))
        self._update_calendar(new_year, new_month)
    
    def _change_year(self, delta: int) -> None:
        """
        年を変更する
        
        Args:
            delta: 変更量（±1）
        """
        new_year = self.current_year + delta
        
        # 年の範囲チェック
        if new_year in self.config.YEAR_RANGE:
            self.year_var.set(str(new_year))
            self._update_calendar(new_year, self.current_month)
    
    def _build_ui(self) -> None:
        """UIの各コンポーネントを構築する"""
        self._build_control_frame()
        self._build_status_bar()
        self._build_calendar_frame()
    
    def _build_control_frame(self) -> None:
        """コントロールパネル（年月選択部分）を構築する"""
        self.control_frame = tk.Frame(self.root)
        self.control_frame.pack(side=tk.TOP, anchor="nw", padx=10, pady=5)
        
        # 年の選択
        tk.Label(
            self.control_frame, 
            text="年", 
            font=self.config.FONT_NORMAL
        ).grid(row=0, column=0, padx=10, pady=10)
        
        self.year_var = tk.StringVar()
        self.year_var.set(str(self.current_year))
        year_dropdown = tk.OptionMenu(
            self.control_frame, 
            self.year_var, 
            *map(str, self.config.YEAR_RANGE)
        )
        year_dropdown.grid(row=0, column=1, padx=10, pady=10)
        
        # 月の選択
        tk.Label(
            self.control_frame, 
            text="月", 
            font=self.config.FONT_NORMAL
        ).grid(row=0, column=2, padx=10, pady=10)
        
        self.month_var = tk.StringVar()
        self.month_var.set(str(self.current_month))
        month_dropdown = tk.OptionMenu(
            self.control_frame, 
            self.month_var, 
            *map(str, range(1, 13))
        )
        month_dropdown.grid(row=0, column=3, padx=10, pady=10)
        
        # 更新ボタン
        update_button = tk.Button(
            self.control_frame, 
            text="更新", 
            #command=self._on_update_button_click,
            padx=10
        )
        update_button.grid(row=0, column=4, padx=10, pady=10)
        
        # ショートカットキー情報ラベル
        shortcuts_label = tk.Label(
            self.control_frame,
            text="ショートカット: ←→(月移動) ↑↓(年移動) Ctrl+S(保存)",
            font=("Arial", 10),
            fg="gray"
        )
        shortcuts_label.grid(row=0, column=5, padx=10, pady=10, sticky="e")
    
    def _build_status_bar(self) -> None:
        """ステータスバーを構築する"""
        status_bar_frame = tk.Label(self.root, bd=1, relief="sunken", anchor="w")
        status_bar_frame.pack(side=tk.TOP, fill=tk.X)
        
        self.status_label = tk.Label(
            status_bar_frame, 
            textvariable=self.status_text, 
            anchor="w",
            padx=5,
            font=self.config.FONT_NORMAL,
            wraplength=1300  # ステータスバーのテキストが長い場合に折り返すよう設定
        )
        self.status_label.pack(fill=tk.X)
    
    def _build_calendar_frame(self) -> None:
        """カレンダー表示部分のフレームを構築する"""
        self.calendar_frame = tk.Frame(self.root)
        self.calendar_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def _toggle_cell_status(self, event: tk.Event) -> None:
        """
        セルのステータスをトグルする（完了/未完了）
        
        Args:
            event: クリックイベント
        """
        widget = event.widget
        current_color = widget.cget("background")
        
        # 色を切り替え
        new_color = (
            self.config.COLOR_COMPLETED 
            if current_color == self.config.COLOR_DEFAULT 
            else self.config.COLOR_DEFAULT
        )
        widget.config(background=new_color)
        
        # 状態の変更をログに記録
        state = "完了" if new_color == self.config.COLOR_COMPLETED else "未完了"
        row, col = self._get_widget_position(widget)
        logger.debug(f"セルの状態を変更: {row}行 {col}列 -> {state}")
        
        # 変更後自動保存
        self._save_current_data()
    
    def _show_status(self, event: tk.Event, widget: Union[tk.Entry, tk.Label]) -> None:
        """
        ステータスバーにテキストを表示する
        
        Args:
            event: マウスオーバーイベント
            widget: マウスオーバーされたウィジェット
        """
        # 習慣名入力欄の場合
        if isinstance(widget, tk.Entry):
            habit_text = widget.get()
            if habit_text:
                self.status_text.set(self.config.STATUS_HABIT_ONLY.format(habit_text))
            else:
                self.status_text.set(self.config.STATUS_HABIT_HINT)
            return
            
        # 日付セルの場合
        row, col = self._get_widget_position(widget)
        if row is not None and col is not None and col > 0:
            date_text = self.config.STATUS_DATE_FORMAT.format(self.current_month, col)
            
            # その行の習慣名も表示
            habit_entry = self.habit_entries.get(row)
            if habit_entry and habit_entry.get().strip():
                habit_text = habit_entry.get()
                self.status_text.set(self.config.STATUS_HABIT_DATE.format(habit_text, date_text))
                return
            
            self.status_text.set(date_text)
    
    def _hide_status(self, event: tk.Event) -> None:
        """
        ステータスバーのテキストをクリアする代わりに全習慣を表示する
        
        Args:
            event: マウスアウトイベント
        """
        # マウスが外れた時、すべての習慣名を表示
        self._display_all_habits()
    
    def _display_all_habits(self) -> None:
        """すべての習慣名をステータスバーに表示する"""
        habit_texts = []
        
        for row_idx, entry in sorted(self.habit_entries.items()):
            habit_text = entry.get().strip()
            if habit_text:
                row_num = row_idx - self.config.START_ROW_INDEX + 1
                habit_texts.append(f"{row_num}: {habit_text}")
        
        if habit_texts:
            habits_str = " | ".join(habit_texts)
            self.status_text.set(self.config.STATUS_HABITS_LIST.format(habits_str))
        else:
            self.status_text.set(self.config.STATUS_NO_HABITS)
    
    def _get_widget_position(self, widget: tk.Widget) -> Tuple[Optional[int], Optional[int]]:
        """
        ウィジェットのグリッド位置を取得する
        
        Args:
            widget: 位置を取得するウィジェット
            
        Returns:
            Tuple[Optional[int], Optional[int]]: (行, 列)のタプル、取得できない場合は(None, None)
        """
        try:
            info = widget.grid_info()
            return info['row'], info['column']
        except (KeyError, AttributeError):
            return None, None
    
    def _collect_current_data(self) -> List[List[Dict[str, Any]]]:
        """
        現在のカレンダーデータを収集する
        
        Returns:
            List: カレンダーデータのリスト
        """
        data = []
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        for i in range(self.config.MAX_HABIT_ROWS):
            row_index = self.config.START_ROW_INDEX + i
            row_data = []
            
            # 習慣名の取得
            entry = self.habit_entries.get(row_index)
            if entry:
                row_data.append({'text': entry.get(), 'bg': entry.cget('background')})
            else:
                # 習慣名が見つからない場合は空のデータを追加
                row_data.append({'text': '', 'bg': self.config.COLOR_DEFAULT})
            
            # 各日のセルステータスの取得
            for j in range(1, days_in_month + 1):
                cells = self.calendar_frame.grid_slaves(row=row_index, column=j)
                if cells:
                    cell = cells[0]
                    row_data.append({'bg': cell.cget('background')})
                else:
                    # セルが見つからない場合はデフォルト値を追加
                    row_data.append({'bg': self.config.COLOR_DEFAULT})
            
            data.append(row_data)
        
        return data
    
    def _create_habit_entry(self, row_index: int, loaded_data: List) -> tk.Entry:
        """
        習慣名入力用のEntryウィジェットを作成する
        
        Args:
            row_index: 行インデックス
            loaded_data: 読み込まれたデータ
            
        Returns:
            tk.Entry: 作成されたEntryウィジェット
        """
        entry = tk.Entry(
            self.calendar_frame, 
            width=self.config.ENTRY_WIDTH, 
            font=self.config.FONT_NORMAL
        )
        entry.grid(row=row_index, column=0, padx=1, pady=1, sticky="ew")
        
        # 保存データがあれば復元
        row_offset = row_index - self.config.START_ROW_INDEX
        if loaded_data and 0 <= row_offset < len(loaded_data) and loaded_data[row_offset]:
            if loaded_data[row_offset] and loaded_data[row_offset][0].get('text'):
                habit_text = loaded_data[row_offset][0]['text']
                entry.delete(0, tk.END)
                entry.insert(0, habit_text)
                logger.debug(f"行 {row_index} に習慣データを復元: {habit_text}")
        
        # イベントバインド
        entry.bind("<Enter>", lambda e, widget=entry: self._show_status(e, widget))
        entry.bind("<Leave>", self._hide_status)
        entry.bind("<FocusOut>", self._on_habit_update)
        
        # 習慣名の辞書に追加
        self.habit_entries[row_index] = entry
        
        return entry
    
    def _on_habit_update(self, event: tk.Event) -> None:
        """
        習慣名が更新されたときの処理
        
        Args:
            event: イベントオブジェクト
        """
        # データを保存
        self._save_current_data()
        # 習慣名一覧を更新表示
        self._display_all_habits()
    
    def _create_day_cell(self, row_index: int, col_index: int, loaded_data: List) -> tk.Label:
        """
        日付セルを作成する
        
        Args:
            row_index: 行インデックス
            col_index: 列インデックス
            loaded_data: 読み込まれたデータ
            
        Returns:
            tk.Label: 作成されたLabelウィジェット
        """
        # ベースとなるセルラベルを作成
        label = tk.Label(
            self.calendar_frame, 
            text="", 
            width=self.config.CELL_WIDTH, 
            height=self.config.CELL_HEIGHT, 
            relief="solid", 
            background=self.config.COLOR_DEFAULT
        )
        label.grid(row=row_index, column=col_index, padx=1, pady=1, sticky="nsew")
        
        # 保存データがあれば背景色を復元
        self._restore_cell_background(label, row_index, col_index, loaded_data)
        
        # イベントバインド
        label.bind("<Button-1>", self._toggle_cell_status)
        label.bind("<Enter>", lambda e, widget=label: self._show_status(e, widget))
        label.bind("<Leave>", self._hide_status)
        
        return label
    
    def _restore_cell_background(self, label: tk.Label, row_index: int, col_index: int, loaded_data: List) -> None:
        """
        セルの背景色を保存データから復元する
        
        Args:
            label: 対象のラベル
            row_index: 行インデックス
            col_index: 列インデックス
            loaded_data: 読み込まれたデータ
        """
        row_offset = row_index - self.config.START_ROW_INDEX
        if not loaded_data or row_offset >= len(loaded_data):
            return
            
        if loaded_data[row_offset] and col_index < len(loaded_data[row_offset]):
            cell_data = loaded_data[row_offset][col_index]
            if isinstance(cell_data, dict) and 'bg' in cell_data:
                label.config(background=cell_data['bg'])
    
    def _update_calendar(self, year: int, month: int, is_initial_load: bool = False) -> None:
        """
        カレンダー表示を更新する
        
        Args:
            year: 表示する年
            month: 表示する月
            is_initial_load: 初回読み込み時かどうか
        """
        # 前の表示を保存（初期化済みで初回ロードでない場合のみ）
        if self.initialized and not is_initial_load:
            self._save_current_data()
        
        # 現在の表示年月を更新
        self.current_year = year
        self.current_month = month
        
        # 習慣名の辞書をクリア
        self.habit_entries.clear()
        
        # カレンダー表示をクリアして再構築
        self._clear_calendar()
        
        # データを読み込み
        loaded_data = self.data_manager.load_data(year, month)
        
        # カレンダーを描画
        self._render_calendar_header()
        self._render_calendar_body(loaded_data)
        
        # すべての習慣名をステータスバーに表示
        self._display_all_habits()
        
        logger.info(f"カレンダーを更新しました: {year}年{month}月")
    
    def _clear_calendar(self) -> None:
        """カレンダー表示をクリアする"""
        for widget in self.calendar_frame.winfo_children():
            widget.destroy()
    
    def _render_calendar_header(self) -> None:
        """カレンダーのヘッダー部分を描画する"""
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        # 年月表示
        header = tk.Label(
            self.calendar_frame, 
            text=f"{self.current_year}年{self.current_month}月", 
            font=self.config.FONT_HEADER, 
            relief="solid",
            padx=10,
            pady=5
        )
        header.grid(row=0, column=0, columnspan=days_in_month + 1, padx=5, pady=10, sticky="ew")
        
        # 日付ヘッダー
        for j in range(days_in_month + 1):
            text = "習慣" if j == 0 else str(j)
            label = tk.Label(
                self.calendar_frame, 
                text=text, 
                width=self.config.CELL_WIDTH, 
                height=1, 
                relief="solid", 
                anchor="center",
                font=("Arial", 10, "bold") if j == 0 else ("Arial", 10)
            )
            label.grid(row=1, column=j, padx=1, pady=1, sticky="nsew")
            
            # 土日の背景色を変更
            if j > 0:
                day_of_week = calendar.weekday(self.current_year, self.current_month, j)
                if day_of_week == 5:  # 土曜日
                    label.config(background="light blue")
                elif day_of_week == 6:  # 日曜日
                    label.config(background="light pink")
        
        # グリッドの設定
        self._configure_grid(days_in_month)
    
    def _configure_grid(self, days_in_month: int) -> None:
        """
        グリッドの列と行の設定を行う
        
        Args:
            days_in_month: 月の日数
        """
        # 列の設定
        self.calendar_frame.grid_columnconfigure(0, weight=3, uniform="first")  # 習慣名列は広め
        for col in range(1, days_in_month + 1):
            self.calendar_frame.grid_columnconfigure(col, weight=1, uniform="equal")
        
        # 行の設定
        for row in range(self.config.START_ROW_INDEX + self.config.MAX_HABIT_ROWS):
            self.calendar_frame.grid_rowconfigure(row, weight=1, uniform="equal")
    
    def _render_calendar_body(self, loaded_data: List = None) -> None:
        """
        カレンダーのボディ部分（習慣と日付のマトリックス）を描画する
        
        Args:
            loaded_data: 読み込まれたデータ（指定されない場合は読み込む）
        """
        days_in_month = calendar.monthrange(self.current_year, self.current_month)[1]
        
        # データが指定されていなければ読み込む
        if loaded_data is None:
            loaded_data = self.data_manager.load_data(self.current_year, self.current_month)
        
        # データ内容をログ出力
        logger.info(f"読み込まれたデータ行数: {len(loaded_data) if loaded_data else 0}")
        
        # 各習慣行の描画
        for i in range(self.config.MAX_HABIT_ROWS):
            row_index = self.config.START_ROW_INDEX + i
            
            # 習慣名入力欄
            self._create_habit_entry(row_index, loaded_data)
            
            # 各日のセル
            for j in range(1, days_in_month + 1):
                self._create_day_cell(row_index, j, loaded_data)
    
    def _save_current_data(self) -> None:
        """現在表示中のカレンダーデータを保存する"""
        # 初期化前は保存しない
        if not self.initialized:
            return
            
        data = self._collect_current_data()
        
        # データが空でないことを確認
        if not data:
            logger.warning("保存データが空です")
            self.status_text.set(self.config.STATUS_EMPTY_DATA)
            return
            
        # データの内容をログに出力
        logger.info(f"保存データ行数: {len(data)}")
        
        # データを保存
        success = self.data_manager.save_data(self.current_year, self.current_month, data)
        if success:
            status_msg = self.config.STATUS_SAVED.format(self.current_year, self.current_month)
            self.status_text.set(status_msg)
            # 少し待ってから習慣名一覧を表示
            self.root.after(1000, self._display_all_habits)
        else:
            self.status_text.set(self.config.STATUS_SAVE_ERROR)
    
    def _on_update_button_click(self) -> None:
        """更新ボタンがクリックされた時の処理"""
        try:
            selected_year = int(self.year_var.get())
            selected_month = int(self.month_var.get())
            
            # 入力値の検証
            if selected_year not in self.config.YEAR_RANGE or not (1 <= selected_month <= 12):
                logger.warning(f"無効な日付が選択されました: {selected_year}年{selected_month}月")
                self.status_text.set(self.config.STATUS_INVALID_DATE)
                return
            
            # 更新処理
            self._update_calendar(selected_year, selected_month)
            
            # 明示的に習慣名一覧を表示
            self.root.after(100, self._display_all_habits)
        except ValueError as e:
            logger.error(f"値の変換中にエラーが発生しました: {e}")
            self.status_text.set(self.config.STATUS_INVALID_INPUT)
    
    def _on_close(self) -> None:
        """アプリケーションが閉じられるときの処理"""
        logger.info("アプリケーションを終了します")
        try:
            self._save_current_data()
        except Exception as e:
            logger.error(f"終了時の保存処理でエラーが発生しました: {e}")
            messagebox.showwarning("保存エラー", "データの保存中にエラーが発生しました。\n一部のデータが保存されていない可能性があります。")
        self.root.destroy()


def main():
    """アプリケーションのエントリーポイント"""
    try:
        root = tk.Tk()
        app = CalendarApp(root)
        root.mainloop()
    except Exception as e:
        logger.critical(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        messagebox.showerror("エラー", f"アプリケーションで予期せぬエラーが発生しました。\n{str(e)}")
        raise


if __name__ == "__main__":
    main()