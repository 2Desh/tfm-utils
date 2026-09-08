import keyboard
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw, ImageFont
import threading
import time
from pathlib import Path


class ArrowUtility:

    ARROW_MAP = {
        'w': '↑',
        'a': '←',
        's': '↓',
        'd': '→',
        'up': '↑',
        'left': '←',
        'down': '↓',
        'right': '→',
    }

    LANGUAGE_MAP = {
        # Directly supported languages
        'en': 'en',
        'pt': 'pt',
        'es': 'es',
        'fr': 'fr',
        'pl': 'pl',
        'tr': 'tr',
        'ro': 'ro',
        'ar': 'ar',
        'zh': 'zh',

        # Unsupported locales mapped to an available fallback language
        'uk': 'ru',
        'be': 'ru',
        'ru': 'ru',
    }

    def __init__(self):
        # Core states
        self.is_active = False
        self.use_wasd = True
        self.use_combo = False

        # Application paths
        self.base_dir = Path(__file__).resolve().parent

        # OS language detection
        self.current_lang = self.detect_language()

        # Threading and hooks
        self.icon = None
        self.hotkey_hooks = []
        self.key_hook = None
        self.f3_hook = None
        self.esc_hook = None

        self.lock = threading.Lock()
        self.is_typing = False

        self.timer_thread = None
        self.timer_generation = 0
        self.time_left = 0

        # Combo tracking
        self.last_key = None
        self.combo_count = 0

        # Translations
        # English and Russian are maintained manually.
        # Other translations were AI-assisted and may need community corrections.
        self.translations = {
            'en': {
                'active': 'OFF',
                'inactive': 'ON',
                'mode_wasd': 'Arrows instead of [W A S D]',
                'mode_arrows': 'Arrows instead of [↑ ← ↓ →] keys',
                'combo': 'Combo Mode [↑ x3]',
                'lang_menu': 'Language...',
                'author': 'Author: Deshofor',
                'exit': 'Exit',
                'notify_combo_title': 'Combo Mode enabled!',
                'notify_combo_msg': 'Made a mistake? Press [Backspace] to decrease count.',
                'notify_timeout_title': 'Timeout',
                'notify_timeout_msg': 'Utility automatically disabled.'
            },

            'pt': {
                'active': 'Desligado',
                'inactive': 'Ligado',
                'mode_wasd': 'Setas em vez de [W A S D]',
                'mode_arrows': 'Setas em vez de [↑ ← ↓ →]',
                'combo': 'Modo Combo [↑ x3]',
                'lang_menu': 'Idioma...',
                'author': 'Autor: Deshofor',
                'exit': 'Sair',
                'notify_combo_title': 'Modo Combo ativado!',
                'notify_combo_msg': 'Errou? Pressione [Backspace] para diminuir a contagem.',
                'notify_timeout_title': 'Tempo Esgotado',
                'notify_timeout_msg': 'Utilitário desativado automaticamente.'
            },

            'tr': {
                'active': 'Kapalı',
                'inactive': 'Açık',
                'mode_wasd': '[W A S D] yerine Oklar',
                'mode_arrows': '[↑ ← ↓ →] yerine Oklar',
                'combo': 'Kombo Modu [↑ x3]',
                'lang_menu': 'Dil...',
                'author': 'Yazar: Deshofor',
                'exit': 'Çıkış',
                'notify_combo_title': 'Kombo Modu etkin!',
                'notify_combo_msg': 'Hata mı yaptınız? Sayıyı azaltmak için [Backspace]\'e basın.',
                'notify_timeout_title': 'Zaman Aşımı',
                'notify_timeout_msg': 'Araç otomatik olarak devre dışı bırakıldı.'
            },

            'pl': {
                'active': 'Wyłączony',
                'inactive': 'Włączony',
                'mode_wasd': 'Strzałki zamiast [W A S D]',
                'mode_arrows': 'Strzałki zamiast [↑ ← ↓ →]',
                'combo': 'Tryb Combo [↑ x3]',
                'lang_menu': 'Język...',
                'author': 'Autor: Deshofor',
                'exit': 'Wyjście',
                'notify_combo_title': 'Tryb Combo włączony!',
                'notify_combo_msg': 'Pomyłka? Naciśnij [Backspace], aby zmniejszyć licznik.',
                'notify_timeout_title': 'Limit czasu',
                'notify_timeout_msg': 'Narzędzie zostało automatycznie wyłączone.'
            },

            'es': {
                'active': 'Apagado',
                'inactive': 'Encendido',
                'mode_wasd': 'Flechas en lugar de [W A S D]',
                'mode_arrows': 'Flechas en lugar de [↑ ← ↓ →]',
                'combo': 'Modo Combo [↑ x3]',
                'lang_menu': 'Idioma...',
                'author': 'Autor: Deshofor',
                'exit': 'Salir',
                'notify_combo_title': '¡Modo Combo activado!',
                'notify_combo_msg': '¿Te equivocaste? Presiona [Backspace] para reducir.',
                'notify_timeout_title': 'Tiempo Agotado',
                'notify_timeout_msg': 'Utilidad desactivada automáticamente.'
            },

            'ar': {
                'active': 'متوقف',
                'inactive': 'شغال',
                'mode_wasd': 'أسهم بدلاً من [W A S D]',
                'mode_arrows': 'أسهم بدلاً من [↑ ← ↓ →]',
                'combo': 'وضع الكومبو [↑ x3]',
                'lang_menu': 'اللغة...',
                'author': 'المؤلف: Deshofor',
                'exit': 'خروج',
                'notify_combo_title': 'تم تفعيل وضع الكومبو!',
                'notify_combo_msg': 'هل أخطأت؟ اضغط [Backspace] لتقليل العدد.',
                'notify_timeout_title': 'انتهى الوقت',
                'notify_timeout_msg': 'تم تعطيل الأداة تلقائيًا.'
            },

            'ru': {
                'active': 'Выключить',
                'inactive': 'Включить',
                'mode_wasd': 'Стрелочки вместо [W A S D]',
                'mode_arrows': 'Стрелочки вместо [↑ ← ↓ →]',
                'combo': 'Режим комбо [↑ x3]',
                'lang_menu': 'Язык...',
                'author': 'Автор: Deshofor',
                'exit': 'Закрыть',
                'notify_combo_title': 'Режим комбо включен!',
                'notify_combo_msg': 'Ошиблись? Нажмите [Стереть], чтобы уменьшить счётчик.',
                'notify_timeout_title': 'Таймер',
                'notify_timeout_msg': 'Утилита выключена (прошла 1 минута).'
            },

            'fr': {
                'active': 'Désactivé',
                'inactive': 'Activé',
                'mode_wasd': 'Flèches au lieu de [W A S D]',
                'mode_arrows': 'Flèches au lieu de [↑ ← ↓ →]',
                'combo': 'Mode Combo [↑ x3]',
                'lang_menu': 'Langue...',
                'author': 'Auteur : Deshofor',
                'exit': 'Quitter',
                'notify_combo_title': 'Mode Combo activé !',
                'notify_combo_msg': 'Une erreur ? Appuyez sur [Backspace] pour réduire.',
                'notify_timeout_title': 'Délai écoulé',
                'notify_timeout_msg': 'Utilitaire désactivé automatiquement.'
            },

            'ro': {
                'active': 'Oprit',
                'inactive': 'Pornit',
                'mode_wasd': 'Săgeți în loc de [W A S D]',
                'mode_arrows': 'Săgeți în loc de [↑ ← ↓ →]',
                'combo': 'Mod Combo [↑ x3]',
                'lang_menu': 'Limbă...',
                'author': 'Autor: Deshofor',
                'exit': 'Ieșire',
                'notify_combo_title': 'Mod Combo activat!',
                'notify_combo_msg': 'Ai greșit? Apasă [Backspace] pentru a scădea numărul.',
                'notify_timeout_title': 'Timp expirat',
                'notify_timeout_msg': 'Utilitar dezactivat automat.'
            },

            'zh': {
                'active': '已关闭',
                'inactive': '已开启',
                'mode_wasd': '使用方向键代替 [W A S D]',
                'mode_arrows': '使用方向键代替 [↑ ← ↓ →]',
                'combo': '连击模式 [↑ x3]',
                'lang_menu': '语言...',
                'author': '作者: Deshofor',
                'exit': '退出',
                'notify_combo_title': '连击模式已启用！',
                'notify_combo_msg': '按错了？按 [Backspace] 键减少次数。',
                'notify_timeout_title': '超时',
                'notify_timeout_msg': '实用程序已自动禁用。'
            }
        }

    # Detect the Windows user locale and map it to a supported application language.
    @classmethod
    def detect_language(cls):
        try:
            import ctypes

            kernel32 = ctypes.windll.kernel32

            kernel32.GetUserDefaultLocaleName.argtypes = [
                ctypes.c_wchar_p,
                ctypes.c_int
            ]
            kernel32.GetUserDefaultLocaleName.restype = ctypes.c_int

            buffer = ctypes.create_unicode_buffer(85)

            result = kernel32.GetUserDefaultLocaleName(
                buffer,
                len(buffer)
            )

            if result <= 0:
                return 'en'

            locale_name = buffer.value.lower()
            language_code = locale_name.split('-')[0]

            return cls.LANGUAGE_MAP.get(language_code, 'en')

        except (AttributeError, OSError):
            return 'en'

    # Icon rendering
    def create_image(self, active, time_left=0):
        # Windows system tray icons are displayed at a small system-defined size.
        # A 64x64 source image provides better quality when the icon is scaled down.
        if not active:
            try:
                image_path = self.base_dir / "ic_arrow.png"

                img = Image.open(image_path).convert("RGBA")
                return img.resize(
                    (64, 64),
                    Image.Resampling.LANCZOS
                )

            except (FileNotFoundError, OSError):
                image = Image.new(
                    'RGBA',
                    (64, 64),
                    color=(0, 0, 0, 0)
                )

                draw = ImageDraw.Draw(image)

                draw.ellipse(
                    (8, 8, 56, 56),
                    fill=(255, 0, 0, 255)
                )

                return image

        # Active timer icon
        image = Image.new(
            'RGBA',
            (64, 64),
            color=(0, 0, 0, 0)
        )

        draw = ImageDraw.Draw(image)
        text = str(time_left)

        try:
            font_path = self.base_dir / "Verdana.ttf"

            font = ImageFont.truetype(
                font_path,
                48
            )

        except OSError:
            try:
                font = ImageFont.truetype(
                    "arial.ttf",
                    48
                )
            except OSError:
                font = ImageFont.load_default()

        x, y = 32, 32

        # Subtle black outline
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                if dx != 0 or dy != 0:
                    draw.text(
                        (x + dx, y + dy),
                        text,
                        font=font,
                        fill=(0, 0, 0, 255),
                        anchor="mm"
                    )

        # Green timer number
        draw.text(
            (x, y),
            text,
            font=font,
            fill=(0, 255, 0, 255),
            anchor="mm"
        )

        return image

    # Input handling
    def send_arrow(self, key_name, arrow_char):
        with self.lock:
            # Prevent generated keyboard events from affecting combo tracking
            self.is_typing = True

            try:
                # Normal mode
                if not self.use_combo:
                    keyboard.write(f'{arrow_char} ')

                    self.last_key = None
                    self.combo_count = 0

                    return

                # If the same key is pressed again
                if key_name == self.last_key:
                    self.combo_count += 1

                    # Second press:
                    # ↑ ↑
                    if self.combo_count == 2:
                        keyboard.write(f'{arrow_char} ')
                        return

                    # Third press replaces the two existing tfm-utils with combo notation:
                    # ↑ ↑ → [↑ x3]
                    if self.combo_count == 3:
                        to_erase = (
                            f'{arrow_char} '
                            f'{arrow_char} '
                        )

                    # Fourth and subsequent presses update the existing combo
                    # [↑ x3] → [↑ x4] → [↑ x5] → ...
                    else:
                        to_erase = (
                            f'[{arrow_char} '
                            f'x{self.combo_count - 1}] '
                        )

                    for _ in range(len(to_erase)):
                        keyboard.send('backspace')
                        time.sleep(0.015)

                    keyboard.write(
                        f'[{arrow_char} x{self.combo_count}] '
                    )

                # A different key starts a new combo
                else:
                    self.last_key = key_name
                    self.combo_count = 1

                    keyboard.write(f'{arrow_char} ')

            finally:
                self.is_typing = False

    def handle_backspace(self):
        with self.lock:
            if (
                not self.use_combo
                or self.combo_count <= 0
                or not self.last_key
            ):
                return

            arrow_char = self.ARROW_MAP.get(self.last_key)

            if not arrow_char:
                return

            self.is_typing = True

            try:
                # For 1 or 2 tfm-utils, remove only the last arrow
                if self.combo_count <= 2:
                    keyboard.send('backspace')
                    time.sleep(0.015)

                    self.combo_count -= 1

                    if self.combo_count == 0:
                        self.last_key = None

                    return

                # Remove the current combo and rebuild it with one fewer arrow
                combo_text = (
                    f'[{arrow_char} '
                    f'x{self.combo_count}] '
                )

                # Delete the entire combo text
                for _ in range(len(combo_text)):
                    keyboard.send('backspace')
                    time.sleep(0.015)

                self.combo_count -= 1

                # [← x3] -> ← ← (remove the combo)
                if self.combo_count == 2:
                    keyboard.write(
                        f'{arrow_char} '
                        f'{arrow_char} '
                    )

                # [← x4] -> [← x3]
                else:
                    keyboard.write(
                        f'[{arrow_char} '
                        f'x{self.combo_count}] '
                    )

            finally:
                self.is_typing = False

    def on_any_key(self, event):
        if not self.use_combo:
            return

        if event.event_type != 'down':
            return

        if self.is_typing:
            return

        allowed_keys = [
            'backspace',
            'shift',
            'right shift',
            'left shift'
        ]

        if self.use_wasd:
            allowed_keys.extend([
                'w',
                'a',
                's',
                'd',

                # Russian keyboard layout equivalents
                'ц',
                'ф',
                'ы',
                'в'
            ])

        else:
            allowed_keys.extend([
                'up',
                'left',
                'down',
                'right'
            ])

        # Any unrelated key interrupts the current combo sequence
        if event.name not in allowed_keys:
            self.combo_count = 0
            self.last_key = None

    # Keyboard hook management
    def apply_state(self):
        # Remove previous hotkeys
        for hook in self.hotkey_hooks:
            try:
                keyboard.remove_hotkey(hook)
            except Exception:
                pass

        self.hotkey_hooks.clear()

        # Remove global key hook
        if self.key_hook is not None:
            try:
                keyboard.unhook(self.key_hook)
            except Exception:
                pass

            self.key_hook = None

        # If utility is disabled, there is nothing else to do
        if not self.is_active:
            return

        # Reset combo state when applying a new input configuration
        self.last_key = None
        self.combo_count = 0

        # Combo-specific hooks
        if self.use_combo:
            self.hotkey_hooks.append(
                keyboard.add_hotkey(
                    'backspace',
                    self.handle_backspace,
                    suppress=True
                )
            )

            self.key_hook = keyboard.on_press(
                self.on_any_key
            )

        # WASD mode
        if self.use_wasd:
            self.hotkey_hooks.extend([
                keyboard.add_hotkey(
                    'w',
                    lambda: self.send_arrow('w', '↑'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    'a',
                    lambda: self.send_arrow('a', '←'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    's',
                    lambda: self.send_arrow('s', '↓'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    'd',
                    lambda: self.send_arrow('d', '→'),
                    suppress=True
                ),
            ])

        # [Arrow keys] mode
        else:
            self.hotkey_hooks.extend([
                keyboard.add_hotkey(
                    'up',
                    lambda: self.send_arrow('up', '↑'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    'left',
                    lambda: self.send_arrow('left', '←'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    'down',
                    lambda: self.send_arrow('down', '↓'),
                    suppress=True
                ),

                keyboard.add_hotkey(
                    'right',
                    lambda: self.send_arrow('right', '→'),
                    suppress=True
                ),
            ])

    # Background timer
    def timer_worker(self, generation):
        while (
                self.is_active
                and self.time_left > 0
                and generation == self.timer_generation
        ):
            time.sleep(1)

            if (
                    not self.is_active
                    or generation != self.timer_generation
            ):
                return

            self.time_left -= 1

            # Update tray icon every second
            if self.icon:
                self.icon.icon = self.create_image(
                    True,
                    self.time_left
                )

        # Timeout
        if (
                self.is_active
                and self.time_left <= 0
                and generation == self.timer_generation
        ):
            self.turn_off()

            if self.icon:
                t = self.translations[self.current_lang]

                self.icon.notify(
                    t['notify_timeout_msg'],
                    t['notify_timeout_title']
                )

    # State management
    def toggle_state(self, *args):
        self.is_active = not self.is_active

        self.timer_generation += 1

        if self.is_active:
            # Start with 60 seconds
            self.time_left = 60

            # Install keyboard hooks
            self.apply_state()

            # Immediately display the timer
            if self.icon:
                self.icon.icon = self.create_image(
                    True,
                    self.time_left
                )
                self.icon.update_menu()

            generation = self.timer_generation

            self.timer_thread = threading.Thread(
                target=self.timer_worker,
                args=(generation,),
                daemon=True
            )

            self.timer_thread.start()

        else:
            # Disable keyboard hooks
            self.apply_state()

            # Reset timer
            self.time_left = 0

            # Restore inactive icon
            if self.icon:
                self.icon.icon = self.create_image(
                    False,
                    0
                )
                self.icon.update_menu()

    def turn_off(self, *args):
        if self.is_active:
            self.is_active = False
            self.timer_generation += 1

            self.apply_state()
            self.update_icon()

    def update_icon(self):
        if not self.icon:
            return

        if self.is_active:
            self.icon.icon = self.create_image(
                True,
                self.time_left
            )
        else:
            self.icon.icon = self.create_image(
                False,
                0
            )

        self.icon.update_menu()

    # Tray menu
    def set_mode_wasd(self, icon, item):
        self.use_wasd = True

        self.last_key = None
        self.combo_count = 0

        self.apply_state()
        self.update_icon()

    def set_mode_arrows(self, icon, item):
        self.use_wasd = False

        self.last_key = None
        self.combo_count = 0

        self.apply_state()
        self.update_icon()

    def toggle_combo(self, icon, item):
        self.use_combo = not self.use_combo

        self.last_key = None
        self.combo_count = 0

        self.apply_state()
        self.update_icon()

        if self.use_combo and self.icon:
            t = self.translations[self.current_lang]

            self.icon.notify(
                t['notify_combo_msg'],
                t['notify_combo_title']
            )

    def set_lang(self, lang_code):
        if lang_code not in self.translations:
            return

        self.current_lang = lang_code
        self.update_icon()

    def on_exit(self, icon, item):
        self.turn_off()

        for hook in (
            self.f3_hook,
            self.esc_hook
        ):
            if hook is not None:
                try:
                    keyboard.remove_hotkey(hook)
                except Exception:
                    pass

        if self.icon:
            self.icon.stop()

    def get_toggle_text(self):
        t = self.translations[self.current_lang]

        if self.is_active:
            return f"{t['active']} ⬇️"

        return f"{t['inactive']} ⬆️"

    # Startup
    def run(self):
        # F3 toggle
        self.f3_hook = keyboard.add_hotkey(
            'f3',
            self.toggle_state
        )

        # ESC to disable
        self.esc_hook = keyboard.add_hotkey(
            'esc',
            self.turn_off
        )

        # Language submenu
        lang_submenu = pystray.Menu(
            item(
                'English',
                lambda: self.set_lang('en'),
                checked=lambda i: self.current_lang == 'en',
                radio=True
            ),

            item(
                'Português (BR)',
                lambda: self.set_lang('pt'),
                checked=lambda i: self.current_lang == 'pt',
                radio=True
            ),

            item(
                'Türkçe',
                lambda: self.set_lang('tr'),
                checked=lambda i: self.current_lang == 'tr',
                radio=True
            ),

            item(
                'Polski',
                lambda: self.set_lang('pl'),
                checked=lambda i: self.current_lang == 'pl',
                radio=True
            ),

            item(
                'Español',
                lambda: self.set_lang('es'),
                checked=lambda i: self.current_lang == 'es',
                radio=True
            ),

            item(
                'العربية',
                lambda: self.set_lang('ar'),
                checked=lambda i: self.current_lang == 'ar',
                radio=True
            ),

            item(
                'Русский',
                lambda: self.set_lang('ru'),
                checked=lambda i: self.current_lang == 'ru',
                radio=True
            ),

            item(
                'Français',
                lambda: self.set_lang('fr'),
                checked=lambda i: self.current_lang == 'fr',
                radio=True
            ),

            item(
                'Română',
                lambda: self.set_lang('ro'),
                checked=lambda i: self.current_lang == 'ro',
                radio=True
            ),

            item(
                '中文',
                lambda: self.set_lang('zh'),
                checked=lambda i: self.current_lang == 'zh',
                radio=True
            )
        )

        # Main tray menu
        menu = pystray.Menu(
            item(
                lambda text: self.get_toggle_text(),
                self.toggle_state
            ),

            pystray.Menu.SEPARATOR,

            item(
                lambda text:
                    self.translations[self.current_lang]['mode_wasd'],
                self.set_mode_wasd,
                checked=lambda menu_item: self.use_wasd,
                radio=True
            ),

            item(
                lambda text:
                    self.translations[self.current_lang]['mode_arrows'],
                self.set_mode_arrows,
                checked=lambda menu_item: not self.use_wasd,
                radio=True
            ),

            pystray.Menu.SEPARATOR,

            item(
                lambda text:
                    self.translations[self.current_lang]['combo'],
                self.toggle_combo,
                checked=lambda menu_item: self.use_combo
            ),

            pystray.Menu.SEPARATOR,

            item(
                lambda text:
                    self.translations[self.current_lang]['lang_menu'],
                lang_submenu
            ),

            item(
                lambda text:
                    self.translations[self.current_lang]['author'],
                lambda: None,
                enabled=False
            ),

            item(
                lambda text:
                    self.translations[self.current_lang]['exit'],
                self.on_exit
            )
        )

        # Create tray icon
        self.icon = pystray.Icon(
            "WASD_Arrows",
            self.create_image(
                self.is_active,
                self.time_left
            ),
            "Arrows",
            menu
        )

        self.icon.run()


if __name__ == "__main__":
    app = ArrowUtility()
    app.run()
