"""Gera assets auto-suficientes do Remotion a partir da cena Cesium validada."""
from pathlib import Path
import json, subprocess
from PIL import Image, ImageDraw
import imageio_ffmpeg

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'entregas' / 'altamira'
DEST = ROOT / 'remotion' / 'public'
DEST.mkdir(parents=True, exist_ok=True)
scene = json.loads((SOURCE / 'cena.json').read_text(encoding='utf-8'))
projected = json.loads((SOURCE / 'projecao.json').read_text(encoding='utf-8'))
features = scene['focos']
assert len(features) == len(projected) == scene['auditoria']['total']

Image.open(SOURCE / 'paisagem.png').convert('RGB').save(DEST / 'paisagem.jpg', quality=94, subsampling=0)

def layer(name, indices, color, radius=3, risk=False):
    image = Image.new('RGBA', (1920, 1080))
    draw = ImageDraw.Draw(image)
    for i in indices:
        point = projected[i]
        if point is None:
            continue
        x, y = point
        if risk:
            v = features[i]['properties']['risco_fogo']
            if v is None:
                fill = (135, 150, 152, 225)
            else:
                fill = tuple(round(a + (b-a)*v) for a,b in zip((80, 194, 194), (255, 98, 66))) + (235,)
        else:
            fill = color
        draw.ellipse((x-radius,y-radius,x+radius,y+radius), fill=fill)
    image.save(DEST / name, optimize=True)

for day in scene['auditoria']['contagens']:
    indices = [i for i, f in enumerate(features) if f['properties']['dia'] == day]
    layer(f'focos-{day}.png', indices, (255, 115, 76, 255), 3)
    layer(f'anteriores-{day}.png', indices, (98, 131, 143, 190), 2)
layer('risco.png', range(len(features)), None, 3, risk=True)
layer('distribuicao.png', range(len(features)), (96, 218, 215, 235), 3)

west = sum(f['geometry']['coordinates'][0] < -54 for f in features) / len(features) * 100
meta = {
    'periodo': scene['auditoria']['periodo_brasilia'],
    'contagens': scene['auditoria']['contagens'],
    'total': scene['auditoria']['total'],
    'riscoCobertura': scene['auditoria']['cobertura']['risco_fogo']['percentual'],
    'oeste54': round(west, 1),
}
(ROOT / 'remotion' / 'src' / 'dados.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')

frames = SOURCE / 'intro_chaves'
assert len(list(frames.glob('*.png'))) == 48
ffmpeg = imageio_ffmpeg.get_ffmpeg_exe()
cmd = [ffmpeg, '-y', '-f', 'rawvideo', '-vcodec', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '1920x1080', '-r', '30', '-i', '-', '-an', '-c:v', 'libx264', '-preset', 'fast', '-crf', '20', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', str(DEST / 'sobrevoo.mp4')]
with subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE) as proc:
    for frame in range(240):
        position = frame / 239 * 47
        index = int(position)
        a = Image.open(frames / f'{index:04d}.png').convert('RGB')
        b = Image.open(frames / f'{min(index+1,47):04d}.png').convert('RGB')
        proc.stdin.write(Image.blend(a, b, position-index).tobytes())
    proc.stdin.close()
    err = proc.stderr.read()
    if proc.wait():
        raise RuntimeError(err.decode(errors='replace'))
print('Assets Remotion:', DEST)
