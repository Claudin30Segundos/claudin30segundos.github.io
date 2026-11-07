#!/usr/bin/env bash
# Plantão do robô do direct: fica ~55 min checando os comentários a cada 45 s (o cron do GitHub atrasa muito).
set -u
git config user.name "claudin-bot"
git config user.email "bot@users.noreply.github.com"
fim=$(( $(date +%s) + ${PLANTAO_SEG:-3300} ))
while [ "$(date +%s)" -lt "$fim" ]; do
  git pull -q --rebase origin main || true            # pega CTAs novos registrados na hora do post
  python3 direct/responder.py || echo "falha nesta rodada"
  # renova a validade do token 1x por semana (marca a data no arquivo)
  ult=$(cat direct/token_renovado.txt 2>/dev/null || echo 0)
  if [ $(( $(date +%s) - ult )) -gt 518400 ]; then
    if curl -sf -o /dev/null "https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=$IG_TOKEN"; then
      date +%s > direct/token_renovado.txt; echo "token renovado"
    fi
  fi
  if ! git diff --quiet direct/respondidos.json direct/token_renovado.txt 2>/dev/null || [ -n "$(git status --porcelain direct/token_renovado.txt)" ]; then
    git add direct/respondidos.json direct/token_renovado.txt 2>/dev/null
    git commit -q -m "direct: respostas [skip ci]" && (git pull -q --rebase origin main; git push -q || true)
  fi
  sleep 45
done
