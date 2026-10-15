"""초코송이 카드용 배경음악을 직접 합성한다(저작권 걱정 없는 자체 음원).

C - Am - F - G 진행에 부드러운 패드 + 오르골 멜로디. 길이는 영상과 같은 7초, 끝은 페이드아웃.
사용: .venv\\Scripts\\python.exe make_music.py [출력.wav] [초]  (초를 늘리면 진행이 그만큼 느리게 펼쳐진다)
"""
import math
import struct
import sys
import wave
from pathlib import Path

SR = 44100
SECONDS = 7.0
N = int(SR * SECONDS)


def freq(midi):
    return 440.0 * 2 ** ((midi - 69) / 12)


CHORDS = [[48, 55, 60, 64], [45, 52, 57, 60], [41, 48, 53, 57], [43, 50, 55, 59]]  # C Am F G
MELODY = [72, 76, 79, 76, 74, 72, 69, 72, 77, 76, 74, 72, 74, 71, 67, 71]


def pad(t, notes, start, length):
    if not start <= t < start + length:
        return 0.0
    local = t - start
    env = min(1.0, local / 0.25) * min(1.0, (start + length - t) / 0.3)
    return env * sum(math.sin(2 * math.pi * freq(n) * t) for n in notes) / len(notes)


def bell(t, note, start):
    local = t - start
    if local < 0 or local > 1.2:
        return 0.0
    f = freq(note)
    env = math.exp(-local * 4.0) * min(1.0, local / 0.005)
    return env * (math.sin(2 * math.pi * f * local) + 0.3 * math.sin(2 * math.pi * 2 * f * local))


def render():
    bar = SECONDS / 4
    step = SECONDS / len(MELODY)
    out = []
    for i in range(N):
        t = i / SR
        s = 0.18 * pad(t, CHORDS[min(3, int(t // bar))], int(t // bar) * bar, bar)
        k = int(t // step)
        for j in (k - 1, k):
            if 0 <= j < len(MELODY):
                s += 0.22 * bell(t, MELODY[j], j * step)
        fade = min(1.0, t / 0.3) * min(1.0, (SECONDS - t) / 1.0)
        out.append(max(-1.0, min(1.0, s * fade)))
    # 아주 짧은 에코로 공간감
    d = int(0.18 * SR)
    for i in range(d, N):
        out[i] = max(-1.0, min(1.0, out[i] + 0.25 * out[i - d]))
    return out


def main():
    global SECONDS, N
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent / "music" / "calm-cdfg.wav"
    if len(sys.argv) > 2:
        SECONDS = float(sys.argv[2])
        N = int(SR * SECONDS)
    path.parent.mkdir(parents=True, exist_ok=True)
    samples = render()
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(b"".join(struct.pack("<h", int(x * 32000)) for x in samples))
    print("ok", path)


if __name__ == "__main__":
    main()
