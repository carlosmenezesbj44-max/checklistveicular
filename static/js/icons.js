function normalizeItemName(text) {
  return (text || "")
    .toString()
    .toLowerCase()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .trim();
}

function getIconForItem(item) {
  const normalized = normalizeItemName(item);

  // Regras em ordem de prioridade para manter o icone semantico por item.
  const rules = [
    { test: /(farol|luz alta|luz baixa)/, icon: "bi-lightbulb-fill" },
    { test: /(pisca|seta)/, icon: "bi-arrow-left-right" },
    { test: /(lanterna|luz de re)/, icon: "bi-brightness-low-fill" },
    { test: /(luz de freio|freio dianteiro|freio traseiro)/, icon: "bi-stop-circle-fill" },
    { test: /(retrovisor|espelho)/, icon: "bi-eye-fill" },
    { test: /(pneu|pneus)/, icon: "bi-circle-fill" },
    { test: /(estepe)/, icon: "bi-life-preserver" },
    { test: /(triangulo)/, icon: "bi-exclamation-triangle-fill" },
    { test: /(macaco)/, icon: "bi-tools" },
    { test: /(chave de roda)/, icon: "bi-wrench" },
    { test: /(limpador|para-brisa|parabrisa)/, icon: "bi-wind" },
    { test: /(vidro|vidros)/, icon: "bi-window" },
    { test: /(lataria)/, icon: "bi-car-front-fill" },
    { test: /(interior|assento)/, icon: "bi-person-square" },
    { test: /(fluido de freio)/, icon: "bi-droplet-fill" },
    { test: /(agua|radiador|arrefecimento)/, icon: "bi-thermometer-half" },
    { test: /(oleo)/, icon: "bi-droplet-half" },
    { test: /(corrente)/, icon: "bi-link-45deg" },
    { test: /(manete|cambio)/, icon: "bi-gear-wide-connected" },
    { test: /(manopla|acelerador)/, icon: "bi-speedometer2" },
    { test: /(capacete)/, icon: "bi-shield-fill-check" },
    { test: /(luz)/, icon: "bi-lightbulb-fill" }
  ];

  for (const rule of rules) {
    if (rule.test.test(normalized)) return rule.icon;
  }

  return "bi-gear-fill";
}
