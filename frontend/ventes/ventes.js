/**
 * Page Ventes & Stock — enregistrement d'une nouvelle vente
 * @author Saint Chalbhery (Dev FS5)
 *
 * main.js ne câble aucun POST vers /api/ventes-stock : ce script complète la
 * page sans le modifier. Il réutilise API_URL, formaterMontant() et
 * initVentesStock(), déjà exposés globalement par main.js et functions.js.
 */

/* Stock connu de la page : sert à ne proposer que les cultures vendables
   et à refuser une quantité trop élevée avant même d'appeler l'API. */
let stockVente = {};

function remplirSelect(select, options) {
  const invite = select.options[0];
  select.replaceChildren(invite, ...options.map(([valeur, libelle]) => new Option(libelle, valeur)));
}

function remplirCultures(select) {
  const cultures = Object.entries(stockVente)
    .filter(([, quantite]) => quantite > 0)
    .map(([culture, quantite]) => [culture, `${culture} — ${quantite} kg`]);
  remplirSelect(select, cultures);
}

/** Renvoie le message d'anomalie à afficher, ou null si la vente est valide. */
function validerVente(vente) {
  if (!vente.acheteur_id) return "Choisissez un acheteur.";
  if (!vente.culture) return "Choisissez une culture.";
  if (!(vente.quantite > 0)) return "La quantité doit être supérieure à 0 kg.";
  if (!(vente.prix_kg > 0)) return "Le prix au kilo doit être supérieur à 0.";

  const disponible = stockVente[vente.culture] ?? 0;
  if (vente.quantite > disponible) {
    return `Stock insuffisant : ${disponible} kg disponibles en ${vente.culture}.`;
  }
  return null;
}

async function initFormVente() {
  const form = document.getElementById("form-vente");
  if (!form) return;

  const champAcheteur = document.getElementById("v-acheteur");
  const champCulture = document.getElementById("v-culture");
  const champQuantite = document.getElementById("v-quantite");
  const champPrix = document.getElementById("v-prix");
  const messageErreur = document.getElementById("message-erreur-vente");
  const messageSucces = document.getElementById("message-succes-vente");

  try {
    const reponse = await fetch(`${API_URL}/ventes-stock`);
    const data = await reponse.json();
    if (!reponse.ok) throw new Error(data.erreur);

    stockVente = data.stock_disponible;
    remplirSelect(champAcheteur, data.acheteurs.map((a) => [a.id, a.nom]));
    remplirCultures(champCulture);
  } catch (e) {
    messageErreur.textContent = "Impossible de charger les acheteurs et le stock. Vérifiez que le backend est démarré (python app.py).";
    messageErreur.hidden = false;
    console.error(e);
    return;
  }

  form.addEventListener("submit", async (evt) => {
    evt.preventDefault();
    const vente = {
      acheteur_id: Number(champAcheteur.value),
      culture: champCulture.value,
      quantite: Number(champQuantite.value),
      prix_kg: Number(champPrix.value),
    };

    const anomalie = validerVente(vente);
    if (anomalie) {
      messageErreur.textContent = anomalie;
      messageErreur.hidden = false;
      messageSucces.hidden = true;
      return;
    }
    messageErreur.hidden = true;

    try {
      const reponse = await fetch(`${API_URL}/ventes-stock`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(vente),
      });
      const resultat = await reponse.json();

      if (!resultat.succes) {
        messageErreur.textContent = resultat.erreur;
        messageErreur.hidden = false;
        messageSucces.hidden = true;
        return;
      }

      const total = vente.quantite * vente.prix_kg;
      messageSucces.textContent = `Vente enregistrée : ${vente.culture}, ${vente.quantite} kg pour ${formaterMontant(total)}.`;
      messageSucces.hidden = false;
      form.reset();

      stockVente = resultat.stock_disponible;
      remplirCultures(champCulture);
      initVentesStock();
    } catch (e) {
      messageErreur.textContent = "Impossible de contacter le serveur.";
      messageErreur.hidden = false;
      console.error(e);
    }
  });
}

window.addEventListener("DOMContentLoaded", initFormVente);
