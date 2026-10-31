"""[Robô do GitHub Actions — roda a cada ~5 min, sem gastar crédito do Claude]
Responde quem comentou CLAUDIN: mensagem privada (direct) com o link + resposta pública curta.

Uso: python3 responder.py           (processa todos os posts de estado/posts.json)
     python3 responder.py --teste   (só lista o que faria, sem enviar)
Regras do Instagram: 1 resposta privada por comentário, até 7 dias depois do comentário.
Estado: direct/respondidos.json; posts com CTA em direct/ctas.json (ids de comentários já tratados) — commitar depois de rodar.
"""
import json, os, re, sys, time, unicodedata
from datetime import datetime, timezone, timedelta
import urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://graph.instagram.com/v21.0'
EST = HERE
TESTE = '--teste' in sys.argv


def token():
    t = os.environ.get('IG_TOKEN', '').strip()
    if not t:
        raise SystemExit('ERRO: segredo IG_TOKEN não configurado no GitHub')
    return t


def req(method, path, params=None, body=None):
    params = dict(params or {})
    params['access_token'] = token()
    url = f'{API}/{path}?{urllib.parse.urlencode(params)}'
    data = json.dumps(body).encode() if body is not None else (b'' if method == 'POST' else None)
    r = urllib.request.Request(url, data=data, method=method,
                               headers={'Content-Type': 'application/json'} if body is not None else {})
    try:
        with urllib.request.urlopen(r, timeout=60) as f:
            return json.loads(f.read())
    except urllib.error.HTTPError as e:
        return {'_erro': e.code, '_msg': e.read().decode()[:400]}


def norm(s):
    s = unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()
    return s


def pediu(texto):
    return re.search(r'\bclaud[ií]n\w*|\bclaudim\b', norm(texto)) is not None


def main():
    os.makedirs(EST, exist_ok=True)
    posts = json.load(open(os.path.join(EST, 'ctas.json')))
    rp = os.path.join(EST, 'respondidos.json')
    feitos = json.load(open(rp)) if os.path.exists(rp) else {}
    me = req('GET', 'me', {'fields': 'user_id,username'})
    if '_erro' in me:
        raise SystemExit(f'ERRO token/API: {me}')
    ig, eu = me['user_id'], me['username']
    limite = datetime.now(timezone.utc) - timedelta(days=6, hours=20)
    enviados, erros = 0, []
    for mid, info in posts.items():
        if not info.get('cta'):
            continue
        after = None
        while True:
            p = {'fields': 'id,text,username,timestamp', 'limit': 50}
            if after:
                p['after'] = after
            res = req('GET', f'{mid}/comments', p)
            if '_erro' in res:
                erros.append(f'comentarios {mid}: {res}')
                break
            for c in res.get('data', []):
                cid = c['id']
                if cid in feitos or c.get('username') == eu or not pediu(c.get('text', '')):
                    continue
                ts = datetime.strptime(c['timestamp'], '%Y-%m-%dT%H:%M:%S%z')
                if ts < limite:
                    feitos[cid] = 'expirado'
                    continue
                texto = info['mensagem']
                if TESTE:
                    print('[teste] responderia', c.get('username'), '→', texto[:60])
                    continue
                r1 = req('POST', f'{ig}/messages', body={'recipient': {'comment_id': cid}, 'message': {'text': texto}})
                if '_erro' in r1:
                    erros.append(f'direct {cid}: {r1}')
                    continue
                req('POST', f'{cid}/replies', {'message': info.get('resposta_publica', 'Te mandei no direct! 🧡')})
                feitos[cid] = datetime.now(timezone.utc).isoformat()
                enviados += 1
                time.sleep(2)
            after = res.get('paging', {}).get('cursors', {}).get('after') if res.get('paging', {}).get('next') else None
            if not after:
                break
    if not TESTE:
        json.dump(feitos, open(rp, 'w'), ensure_ascii=False, indent=1)
    print(f'ENVIADOS {enviados}')
    for e in erros:
        print('ERRO', e)
    return enviados, erros


if __name__ == '__main__':
    main()
