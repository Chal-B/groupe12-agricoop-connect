(function () {
  const liste = document.getElementById("liste-ventes");
  const selectCulture = document.getElementById("filtre-culture");
  const champAcheteur = document.getElementById("filtre-acheteur");
  const messageVide = document.getElementById("filtre-vide");
  if (!liste || !selectCulture || !champAcheteur) return;

  function appliquerFiltres() {
    const culture = selectCulture.value.trim().toLowerCase();
    const acheteur = champAcheteur.value.trim().toLowerCase();
    const lignes = liste.querySelectorAll("tr");
    let visibles = 0;

    for (const ligne of lignes) {
      const cellules = ligne.querySelectorAll("td");
      // main.js : [0] acheteur, [1] culture (N° via CSS ::before)
      if (cellules.length < 2) continue;

      const okCulture =
        !culture || cellules[1].textContent.trim().toLowerCase() === culture;
      const okAcheteur =
        !acheteur || cellules[0].textContent.toLowerCase().includes(acheteur);

      ligne.hidden = !(okCulture && okAcheteur);
      if (!ligne.hidden) visibles += 1;
    }

    if (messageVide) {
      messageVide.hidden = !(lignes.length > 0 && visibles === 0);
    }
  }

  selectCulture.addEventListener("change", appliquerFiltres);
  champAcheteur.addEventListener("input", appliquerFiltres);
  new MutationObserver(appliquerFiltres).observe(liste, { childList: true });

  const cartesStock = document.getElementById("cartes-stock");
  if (!cartesStock) return;

  function styliserBadgesStock() {
    for (const badge of cartesStock.querySelectorAll(".badge")) {
      const ok = badge.textContent.trim() === "Disponible";
      badge.classList.toggle("ok", ok);
      badge.classList.toggle("alerte", !ok);
    }
  }

  styliserBadgesStock();
  new MutationObserver(styliserBadgesStock).observe(cartesStock, {
    childList: true,
  });
})();
