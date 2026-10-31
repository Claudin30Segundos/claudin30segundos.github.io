# Robô do direct (@30scomclaudin)
Roda sozinho no GitHub Actions a cada ~5 minutos (grátis, sem gastar Claude): quem comentar CLAUDIN num post com passo a passo recebe o link no direct.
- `ctas.json`: posts com "comenta CLAUDIN" (media_id → mensagem). A automação de vídeos acrescenta aqui quando posta um vídeo com CTA.
- `respondidos.json`: comentários já respondidos (cada pessoa recebe 1 vez).
- O token do Instagram fica no segredo `IG_TOKEN` (Settings → Secrets and variables → Actions). Nunca vai pro código.
