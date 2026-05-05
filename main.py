# Python env   : MicroPython v1.25.0 + LVGL 9.3.0
# @File        : main.py
# @Description : Danke AI voice chatbot with LVGL GUI — Waveshare ESP32-S3-Touch-LCD-2

# ── Imports ───────────────────────────────────────────────────────────────────

import lcd_bus
import lvgl as lv
import st7789
import cst816s
import i2c
import task_handler
import machine
import gc
from micropython import const

from machine import I2S, Pin
import asyncio
import time
import ntptime
import network
import urandom
import os

from async_mic_recorder import AsyncMicRecorder
from xfyun_asr import XfyunASR
from xfyun_tts import XfyunTTS
from uopenai import OpenAI

# ── Config ────────────────────────────────────────────────────────────────────

WIFI_SSID     = "CU_kM7v"
WIFI_PASSWORD = "a7tmyakw"

ASR_APPID  = "b1f37776"
ASR_KEY    = "9a60e825762db08d941b4f1b21cb988e"
ASR_SECRET = "OGE1ZjJlYTdhNzFlMmYzYmMxYTMyMTk3"

TTS_APPID  = "85ca87b7"
TTS_KEY    = "a64add4b50e1df51f2b31ed8ba086722"
TTS_SECRET = "YWE2Y2MwYWEzZGQ1OGM4Yjg2NDkxYTFm"

LLM_KEY    = "7e549988-07d8-40b7-b6d4-09e4e7c04656"
LLM_URL    = "https://ark.cn-beijing.volces.com/api/v3"
LLM_MODEL  = "deepseek-v3-2-251201"
LLM_SYSTEM = "你是蛋壳,一个AI电子宠物,请可爱的回复我"

MAX_ROUNDS = 3
MIC_PCM    = "mic.pcm"

THINKING_PHRASES = [
    "好的，蛋壳知道了，让蛋壳仔细想想，蛋壳脑袋有点慢慢的哦",
    "嗯嗯，蛋壳听到啦，稍等一下下，蛋壳在认真想呢",
    "收到收到，蛋壳的小脑袋瓜转起来啦，马上马上",
    "哦哦哦，蛋壳明白了，让蛋壳想一想，别着急哟",
    "好哒，蛋壳在想了，脑袋瓜有点小，请稍等一秒秒",
]
THINKING_PCMS = ["thinking_{}.pcm".format(i) for i in range(len(THINKING_PHRASES))]

# ── Display constants ─────────────────────────────────────────────────────────

SPI_BUS     = 2
SPI_FREQ    = 40000000
LCD_SCLK    = 39
LCD_MOSI    = 38
LCD_MISO    = 40
LCD_DC      = 42
LCD_CS      = 45
LCD_BL      = 1
I2C_BUS     = 0
I2C_FREQ    = 400000
TP_SDA      = 48
TP_SCL      = 47
TP_ADDR     = 0x15
TP_REGBITS  = 8
TFT_W       = 320
TFT_H       = 240
BUFFER_SIZE = const(28800)

# ── I2S / amp pins ────────────────────────────────────────────────────────────

MIC_SCK, MIC_WS, MIC_SD  = 11, 12, 13
SPK_SCK, SPK_WS, SPK_SD  = 14, 15, 16
AMP_SD_PIN   = 17
AMP_GAIN_PIN = 18

# ── State machine ─────────────────────────────────────────────────────────────

_IDLE      = 0
_LISTENING = 1
_THINKING  = 2
_SPEAKING  = 3
_ERROR     = 4

# Per-state solid background color (vivid, no gradient to avoid GC issues)
_STATE_BG = {
    _IDLE:      0x4dd0e1,   # cyan
    _LISTENING: 0x42a5f5,   # blue
    _THINKING:  0xffa726,   # orange
    _SPEAKING:  0xab47bc,   # purple
    _ERROR:     0xef5350,   # red
}
_STATE_COLOR = _STATE_BG  # dot fallback

_STATE_LABEL = {
    _IDLE:      "Ready",
    _LISTENING: "Listening...",
    _THINKING:  "Thinking...",
    _SPEAKING:  "Speaking...",
    _ERROR:     "Error",
}

# ── Animation motion tables (y/x pixel offsets, applied via align) ────────────
# Idle: slow gentle vertical bob (~1.7 s / cycle at 120 ms/step)
_BOB_IDLE   = [0, 1, 2, 3, 4, 5, 4, 3, 2, 1, 0, -1, -2, -1]
# Listen: excited bounce (~1 s / cycle at 80 ms/step)
_BOB_LISTEN = [0, 3, 6, 9, 10, 9, 6, 3, 0, -2, -4, -2]
# Think: slow left-right sway (x offset, ~4 s / cycle at 350 ms/step)
_SWAY_THINK = [0, 1, 2, 3, 2, 1, 0, -1, -2, -3, -2, -1]
# Error: nervous small tremble (x offset, ~1.2 s / cycle at 150 ms/step)
_TREMBLE    = [-2, 0, 2, 0, -2, 0, 2, 0]

_CHICK_BASE_Y = const(-20)   # base vertical offset from screen center

# ── Display + touch init ──────────────────────────────────────────────────────
# NOTE: framebuffers must be allocated BEFORE ST7789 init
# NOTE: set_rotation() must be called AFTER both display AND touch are inited
# NOTE: do NOT call lv.init() — ST7789() does it automatically

print("[Display] init SPI bus...")
spi_bus = machine.SPI.Bus(host=SPI_BUS, mosi=LCD_MOSI, miso=LCD_MISO, sck=LCD_SCLK)
display_bus = lcd_bus.SPIBus(spi_bus=spi_bus, freq=SPI_FREQ, dc=LCD_DC, cs=LCD_CS)

fb1 = display_bus.allocate_framebuffer(BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)
fb2 = display_bus.allocate_framebuffer(BUFFER_SIZE, lcd_bus.MEMORY_INTERNAL | lcd_bus.MEMORY_DMA)

main_display = st7789.ST7789(
    data_bus=display_bus,
    frame_buffer1=fb1,
    frame_buffer2=fb2,
    display_width=TFT_H,
    display_height=TFT_W,
    color_space=lv.COLOR_FORMAT.RGB565,
    color_byte_order=st7789.BYTE_ORDER_BGR,
    rgb565_byte_swap=True,
    backlight_pin=LCD_BL,
    backlight_on_state=st7789.STATE_PWM,
)
main_display.init()
main_display.set_power(True)
main_display.set_backlight(100)

print("[Touch] init I2C...")
i2c_bus = i2c.I2C.Bus(host=I2C_BUS, scl=TP_SCL, sda=TP_SDA, freq=I2C_FREQ, use_locks=False)
touch_dev = i2c.I2C.Device(bus=i2c_bus, dev_id=TP_ADDR, reg_bits=TP_REGBITS)
indev = cst816s.CST816S(touch_dev, startup_rotation=lv.DISPLAY_ROTATION._180)

main_display.set_rotation(lv.DISPLAY_ROTATION._90)
print("[Display] ready 320x240")

# ── Image assets ──────────────────────────────────────────────────────────────

IMG_W = const(160)
IMG_H = const(160)

_FRAME_FILES = {
    'idle':   ('assets/chick_idle_0.bin',   'assets/chick_idle_1.bin'),
    'listen': ('assets/chick_listen_0.bin', 'assets/chick_listen_1.bin'),
    'think':  ('assets/chick_think_0.bin',  'assets/chick_think_1.bin',
               'assets/chick_think_2.bin'),
    'speak':  ('assets/chick_speak_0.bin',  'assets/chick_speak_1.bin'),
    'error':  ('assets/chick_error_0.bin',),
}

_frame_data  = []  # keep raw bytes alive to prevent GC

def _load_frame(path):
    try:
        with open(path, 'rb') as f:
            raw = f.read()
        _frame_data.append(raw)
        mv = memoryview(raw)
        return lv.image_dsc_t({
            'header': {
                'magic':  0x19,
                'cf':     lv.COLOR_FORMAT.ARGB8888,
                'w':      IMG_W,
                'h':      IMG_H,
                'stride': IMG_W * 4,
            },
            'data_size': len(raw),
            'data':      mv,
        })
    except Exception as e:
        print("[Assets] load failed:", path, e)
        return None

print("[Assets] loading chick frames...")
_frames    = {}
_HAS_IMG   = True
for _k, _paths in _FRAME_FILES.items():
    _lst = []
    for _p in _paths:
        _d = _load_frame(_p)
        if _d:
            _lst.append(_d)
        else:
            _HAS_IMG = False
    _frames[_k] = _lst
print("[Assets]", "OK" if _HAS_IMG else "some frames missing — dot fallback")

# ── Build UI ──────────────────────────────────────────────────────────────────

scrn = lv.screen_active()
scrn.set_style_bg_color(lv.color_hex(_STATE_BG[_IDLE]), lv.PART.MAIN)
scrn.set_style_bg_opa(lv.OPA.COVER, lv.PART.MAIN)

def _apply_grad(top_hex, bot_hex):
    pass  # unused, kept for compatibility

# Chick image — centered, transparent ARGB8888, on top of background
if _HAS_IMG and _frames['idle']:
    _chick = lv.image(scrn)
    _chick.set_src(_frames['idle'][0])
    _chick.align(lv.ALIGN.CENTER, 0, -20)
    _dot = None
    print("[UI] chick image widget created")
else:
    _dot = lv.obj(scrn)
    _dot.set_size(80, 80)
    _dot.set_style_radius(40, lv.PART.MAIN)
    _dot.set_style_border_width(0, lv.PART.MAIN)
    _dot.set_style_bg_color(lv.color_hex(_STATE_COLOR[_IDLE]), lv.PART.MAIN)
    _dot.set_style_shadow_width(0, lv.PART.MAIN)
    _dot.center()
    _chick = None
    print("[UI] dot fallback widget created")

status_label = lv.label(scrn)
status_label.set_text("Starting...")
status_label.set_style_text_color(lv.color_hex(0xffffff), lv.PART.MAIN)
status_label.set_style_text_font(lv.font_montserrat_16, lv.PART.MAIN)
status_label.align(lv.ALIGN.BOTTOM_MID, 0, -50)

# Sound bars (visible only in LISTENING state)
_BAR_N   = 5
_BAR_W   = 10
_BAR_GAP = 6
_BAR_X0  = (TFT_W - _BAR_N * _BAR_W - (_BAR_N - 1) * _BAR_GAP) // 2
_BAR_BOT = 234

_bars = []
for _i in range(_BAR_N):
    _b = lv.obj(scrn)
    _b.set_size(_BAR_W, 4)
    _b.set_pos(_BAR_X0 + _i * (_BAR_W + _BAR_GAP), _BAR_BOT - 4)
    _b.set_style_radius(5,  lv.PART.MAIN)
    _b.set_style_border_width(0, lv.PART.MAIN)
    _b.set_style_bg_color(lv.color_hex(0xffffff), lv.PART.MAIN)
    _b.set_style_shadow_width(0, lv.PART.MAIN)
    _b.set_style_opa(lv.OPA.TRANSP, lv.PART.MAIN)
    _bars.append(_b)

# ── Animation state ───────────────────────────────────────────────────────────

_anim_state = _IDLE


def set_state(state):
    global _anim_state
    _anim_state = state
    gc.collect()
    status_label.set_text(_STATE_LABEL[state])
    if not _HAS_IMG and _dot:
        _dot.set_style_bg_color(lv.color_hex(_STATE_COLOR[state]), lv.PART.MAIN)


async def animation_loop():
    _blink_t  = 0
    _think_fi = 0
    _speak_fi = 0
    _bob_i    = 0
    _sway_i   = 0
    _trem_i   = 0
    while True:
        s = _anim_state
        if not _HAS_IMG or not _chick:
            await asyncio.sleep_ms(200)
            continue

        if s == _IDLE:
            _blink_t += 1
            _bob_i = (_bob_i + 1) % len(_BOB_IDLE)
            _chick.align(lv.ALIGN.CENTER, 0, _CHICK_BASE_Y + _BOB_IDLE[_bob_i])
            if _blink_t >= 28:
                _chick.set_src(_frames['idle'][1])
                await asyncio.sleep_ms(110)
                _chick.set_src(_frames['idle'][0])
                _blink_t = 0
            await asyncio.sleep_ms(120)

        elif s == _LISTENING:
            fi = (time.ticks_ms() // 300) & 1
            _chick.set_src(_frames['listen'][fi])
            _bob_i = (_bob_i + 1) % len(_BOB_LISTEN)
            _chick.align(lv.ALIGN.CENTER, 0, _CHICK_BASE_Y + _BOB_LISTEN[_bob_i])
            await asyncio.sleep_ms(80)

        elif s == _THINKING:
            if _frames['think']:
                _think_fi = (_think_fi + 1) % len(_frames['think'])
                _chick.set_src(_frames['think'][_think_fi])
            _sway_i = (_sway_i + 1) % len(_SWAY_THINK)
            _chick.align(lv.ALIGN.CENTER, _SWAY_THINK[_sway_i], _CHICK_BASE_Y)
            await asyncio.sleep_ms(350)

        elif s == _SPEAKING:
            _speak_fi ^= 1
            if _frames['speak']:
                _chick.set_src(_frames['speak'][_speak_fi])
            _bob_i = (_bob_i + 1) % len(_BOB_IDLE)
            _chick.align(lv.ALIGN.CENTER, 0, _CHICK_BASE_Y + _BOB_IDLE[_bob_i])
            await asyncio.sleep_ms(210)

        elif s == _ERROR:
            if _frames['error']:
                _chick.set_src(_frames['error'][0])
            _trem_i = (_trem_i + 1) % len(_TREMBLE)
            _chick.align(lv.ALIGN.CENTER, _TREMBLE[_trem_i], _CHICK_BASE_Y)
            await asyncio.sleep_ms(150)

        else:
            await asyncio.sleep_ms(100)


async def bars_loop():
    while True:
        if _anim_state == _LISTENING:
            for i, bar in enumerate(_bars):
                h = urandom.randint(6, 28)
                bar.set_size(_BAR_W, h)
                bar.set_pos(_BAR_X0 + i * (_BAR_W + _BAR_GAP), _BAR_BOT - h)
                bar.set_style_opa(lv.OPA.COVER, lv.PART.MAIN)
        else:
            for bar in _bars:
                bar.set_style_opa(lv.OPA.TRANSP, lv.PART.MAIN)
        await asyncio.sleep_ms(120)


# ── LVGL task handler — integrates with asyncio event loop ───────────────────

th = task_handler.TaskHandler(duration=5)

# ── WiFi ──────────────────────────────────────────────────────────────────────

print("[WiFi] connecting to", WIFI_SSID)
status_label.set_text("WiFi connecting...")
sta = network.WLAN(network.STA_IF)
if not sta.isconnected():
    sta.active(True)
    sta.connect(WIFI_SSID, WIFI_PASSWORD)
    while not sta.isconnected():
        time.sleep(0.5)
print("[WiFi] connected, IP:", sta.ifconfig()[0])

# ── NTP ───────────────────────────────────────────────────────────────────────

print("[NTP] syncing time...")
status_label.set_text("Syncing time...")
for _host in ("ntp.aliyun.com", "pool.ntp.org", "time.cloudflare.com"):
    try:
        ntptime.host = _host
        ntptime.settime()
        print("[NTP] synced via", _host)
        break
    except Exception as _e:
        print("[NTP]", _host, "failed:", _e)
else:
    print("[NTP] all servers failed, continuing with local time")

# ── I2S + amp init ────────────────────────────────────────────────────────────

print("[I2S] init mic INMP441...")
audio_in = I2S(
    0,
    sck=Pin(MIC_SCK), ws=Pin(MIC_WS), sd=Pin(MIC_SD),
    mode=I2S.RX, bits=16, format=I2S.MONO,
    rate=16000, ibuf=40000,
)

print("[I2S] init speaker MAX98357A...")
audio_out = I2S(
    1,
    sck=Pin(SPK_SCK), ws=Pin(SPK_WS), sd=Pin(SPK_SD),
    mode=I2S.TX, bits=16, format=I2S.MONO,
    rate=16000, ibuf=40000,
)

amp_sd   = Pin(AMP_SD_PIN,   Pin.OUT, value=0)
amp_gain = Pin(AMP_GAIN_PIN, Pin.OUT, value=0)
print("[AMP] SD=GP{} GAIN=GP{}, default off".format(AMP_SD_PIN, AMP_GAIN_PIN))

# ── Drivers ───────────────────────────────────────────────────────────────────

print("[Drivers] init...")
recorder = AsyncMicRecorder(
    audio_in,
    rate=16000, threshold=350, silence_frames=10,
    min_voice_frames=5, frame_bytes=2048,
    max_seconds=30, warmup_frames=15,
)
asr = XfyunASR(ASR_APPID, ASR_KEY, ASR_SECRET, sample_rate=16000)
tts = XfyunTTS(TTS_APPID, TTS_KEY, TTS_SECRET, auf="audio/L16;rate=16000")
llm = OpenAI(api_key=LLM_KEY, base_url=LLM_URL)
print("[Drivers] ready")

# ── Helper: play PCM file ─────────────────────────────────────────────────────

async def play_pcm(filepath, rate=16000):
    amp_sd.value(1)
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(2048)
            if not chunk:
                break
            audio_out.write(chunk)
    ibuf_ms = 40000 * 1000 // (rate * 2)
    await asyncio.sleep_ms(ibuf_ms + 200)
    amp_sd.value(0)
    await asyncio.sleep_ms(300)


def trim_history(messages):
    system = [m for m in messages if m["role"] == "system"]
    dialog = [m for m in messages if m["role"] != "system"]
    if len(dialog) > MAX_ROUNDS * 2:
        dialog = dialog[-(MAX_ROUNDS * 2):]
    return system + dialog

# ── Chat loop ─────────────────────────────────────────────────────────────────

async def chat_loop():
    import json as _json

    asyncio.create_task(animation_loop())
    asyncio.create_task(bars_loop())

    # Pre-synthesize thinking prompts
    print("[Danke] pre-synthesizing thinking prompts...")
    status_label.set_text("Preparing...")
    for i, phrase in enumerate(THINKING_PHRASES):
        fname = THINKING_PCMS[i]
        try:
            os.stat(fname)
        except OSError:
            await tts.synthesize(phrase, fname)

    print("[Danke] warming up mic...")
    status_label.set_text("Warming up...")
    await recorder.start()

    # Greeting
    set_state(_SPEAKING)
    await tts.synthesize_and_play("你好，我是蛋壳，有什么可以帮你的？", audio_out, amp_sd)
    print("[Danke] ready")

    messages = [{"role": "system", "content": LLM_SYSTEM}]
    round_num = 0

    while True:
        try:
            round_num += 1
            print("\n[Danke] === round {} ===".format(round_num))

            # 1. Listen
            set_state(_LISTENING)
            t0 = time.ticks_us()
            await recorder.listen(MIC_PCM)
            print("[Danke] listen {}ms".format(time.ticks_diff(time.ticks_us(), t0) // 1000))

            # 2. Play thinking prompt while ASR runs
            set_state(_THINKING)
            thinking_pcm = THINKING_PCMS[urandom.randint(0, len(THINKING_PCMS) - 1)]
            await play_pcm(thinking_pcm)

            # 3. ASR
            t0 = time.ticks_us()
            text = await asr.recognize(MIC_PCM)
            print("[Danke] ASR {}ms: {}".format(time.ticks_diff(time.ticks_us(), t0) // 1000, text))

            if not text:
                set_state(_ERROR)
                await asyncio.sleep_ms(2000)
                round_num -= 1
                continue

            # 4. LLM stream + sentence-level TTS
            messages.append({"role": "user", "content": text})
            messages = trim_history(messages)

            t0 = time.ticks_us()
            resp = await llm.chat.completions.create(
                model=LLM_MODEL, messages=messages, stream=True
            )

            full_reply    = ""
            sentence_buf  = ""
            sentence_idx  = 0
            speaking_started = False
            SENT_ENDS = "。！？!?\n"
            MIN_LEN   = 5

            async for line in resp.iter_lines():
                line = line.strip()
                if not line:
                    continue
                if line == b"data: [DONE]":
                    break
                if line.startswith(b"data: "):
                    try:
                        chunk = _json.loads(line[6:])
                    except Exception:
                        continue
                    token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                    if not token:
                        continue
                    sentence_buf += token
                    full_reply   += token
                    if any(c in sentence_buf for c in SENT_ENDS) and len(sentence_buf) >= MIN_LEN:
                        sentence_idx += 1
                        if not speaking_started:
                            set_state(_SPEAKING)
                            speaking_started = True
                        print("[Danke] TTS {}: {}".format(sentence_idx, sentence_buf))
                        await tts.synthesize_and_play(sentence_buf, audio_out, amp_sd)
                        sentence_buf = ""

            if sentence_buf.strip():
                if not speaking_started:
                    set_state(_SPEAKING)
                print("[Danke] TTS tail:", sentence_buf)
                await tts.synthesize_and_play(sentence_buf, audio_out, amp_sd)

            messages.append({"role": "assistant", "content": full_reply})
            print("[Danke] round done {}ms".format(time.ticks_diff(time.ticks_us(), t0) // 1000))

        except Exception as e:
            import sys
            print("[Danke] error:")
            sys.print_exception(e)
            set_state(_ERROR)
            await asyncio.sleep_ms(1000)
            # watchdog: always continue to next round, never hang
            continue

# ── Entry ─────────────────────────────────────────────────────────────────────

print("[Danke] starting chat loop")
asyncio.run(chat_loop())
