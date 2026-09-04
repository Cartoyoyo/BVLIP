<div align="center">

# BVLIP

<img src="icons/logo.png" width="80" alt="BVLIP icon"/>

**Cliquez un point sur un cours d'eau : le bassin versant qui l'alimente est délimité, caractérisé et mis en rapport — sans préparer la moindre donnée.**

[![QGIS](https://img.shields.io/badge/QGIS-3.40%2B-green?logo=qgis&logoColor=white)](https://qgis.org)
[![Version](https://img.shields.io/badge/version-0.9.2-blue)](metadata.txt)
[![License](https://img.shields.io/badge/license-GPL%20v3-orange)](LICENSE)
[![Données](https://img.shields.io/badge/données-IGN%20%7C%20Sandre-informational)](https://geoservices.ign.fr)
[![Interface](https://img.shields.io/badge/interface-FR%20%7C%20EN%20%7C%20ES%20%7C%20PT%20%7C%20DE-lightgrey)](i18n/__init__.py)

</div>

---

<div align="center">

## Aperçu rapide · Quick Overview

| 1 — Cliquer | 2 — Délimiter | 3 — Rapporter |
|:---:|:---:|:---:|
| ![Panneau](screenshot/02_panneau.png) | ![Carte](screenshot/01_carte.png) | ![Rapport](screenshot/03_rapport.png) |
| Un point sur la carte,<br>et le calcul part en tâche de fond | Le bassin, son chevelu<br>et les quatre états de l'exutoire | Une page A4 par bassin,<br>en PDF et en classeur Excel |

| Réglages | À propos |
|:---:|:---:|
| ![Réglages](screenshot/04_reglages.png) | ![À propos](screenshot/05_apropos.png) |
| Accrochage de l'exutoire,<br>dans le menu de l'extension | Version, licence et dépôt,<br>dans le menu de l'extension |

</div>

---

## Français

### Description

BVLIP délimite le bassin versant topographique drainé par un point choisi sur la carte, calcule ses caractéristiques morphométriques et hydrologiques, et produit un rapport cartographique A4. Le modèle numérique de terrain RGE ALTI et le réseau hydrographique BD TOPO sont téléchargés à la volée depuis la Géoplateforme de l'IGN.

Fini le MNT à récupérer, à mosaïquer, à reprojeter avant de pouvoir commencer : vous cliquez un exutoire, et le plugin s'occupe de trouver l'emprise utile, de télécharger ce qu'il faut, de délimiter, de mesurer et de mettre en page. Sur un bassin de quelques kilomètres carrés, comptez une vingtaine de secondes ; QGIS reste utilisable pendant tout le calcul.

### Fonctionnalités

- **Aucune donnée à préparer** : RGE ALTI, BD TOPO, masses d'eau Sandre et Corine Land Cover sont interrogés en ligne, sans clé d'API.
- **Aucune dépendance externe** : le calcul repose sur GRASS, livré d'origine avec QGIS. Ni TauDEM ni WhiteboxTools à installer.
- **Accrochage de l'exutoire en deux temps** : le point cliqué est d'abord ramené sur le tracé BD TOPO, puis recalé sur le chevelu déduit du modèle de terrain. Les deux ne se superposent pas : en fond de vallée, l'écart atteint couramment plusieurs dizaines de mètres.
- **Contrôle de cohérence** : le bassin obtenu doit contenir le réseau qu'il draine. En dessous de 60 % du linéaire strictement amont, le traitement s'arrête en disant pourquoi plutôt que de rendre un résultat faux.
- **Maille adaptée à la machine** : la résolution du MNT se déduit de la mémoire réellement libre au moment du calcul — 5 m sur un petit bassin, 10 ou 25 m sur plusieurs centaines de kilomètres carrés. Un poste modeste ne s'arrête plus sur un grand bassin.
- **Calcul en tâche de fond**, avec bouton d'annulation : la carte reste navigable, la progression s'affiche dans la barre de tâches de QGIS.
- **Caractéristiques complètes** : 62 champs, tous étiquetés avec leur unité — surface, périmètre, indice de compacité de Gravelius, rectangle équivalent, hypsométrie, pentes, indice de pente global, dénivelée spécifique, plus long cheminement hydraulique, densité de drainage, temps de concentration selon quatre formules.
- **Rattachement à la masse d'eau DCE** par le référentiel Sandre : code européen, dénomination, surface du bassin versant spécifique.
- **Occupation du sol** par Corine Land Cover 2018, complétée par le bâti de la BD TOPO — CLC efface les hameaux sous son unité minimale de 25 ha.
- **Rapport A4** en PDF et en classeur Excel : carte masquée en moitié haute, caractéristiques et graphiques ensuite, courbe hypsométrique, répartition de l'occupation du sol, comparaison des temps de concentration.
- **Cours d'eau nommés** : la couche des tronçons amont reprend le toponyme, le code hydrographique, la nature, la persistance et la classe de largeur de la BD TOPO. Les noms s'affichent le long des cours d'eau, et les écoulements intermittents se distinguent des permanents par un trait tireté.
- **Traitement par lot** via un algorithme Processing, intégrable dans un modèle graphique. Un point qui échoue n'interrompt pas le lot.
- **Interface en cinq langues**, commutable depuis le menu de l'extension : français, anglais, espagnol, portugais, allemand.

### Prérequis

- **QGIS 3.40** ou supérieur, avec le fournisseur GRASS activé dans les options de Processing.
- Un **accès à Internet** : toutes les données sont téléchargées à la demande.
- Le territoire couvert par le **RGE ALTI** en Lambert 93, c'est-à-dire la France métropolitaine et la Corse. Les DROM ne sont pas traités.

> **Recommandé** — `matplotlib` et `openpyxl`, tous deux livrés avec l'installation Windows de QGIS. Sans le premier, le rapport est produit sans ses graphiques ; sans le second, seul le PDF est produit. Le plugin le signale et poursuit.

### Installation

1. Récupérer le dépôt :

   ```bash
   git clone https://github.com/Cartoyoyo/BVLIP.git
   ```

2. Copier le dossier `BVLIP` dans le répertoire des extensions du profil QGIS :

   | Système | Chemin |
   |---------|--------|
   | Windows | `C:\Users\<utilisateur>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\` |
   | macOS   | `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/` |
   | Linux   | `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/` |

3. Activer **BVLIP** dans *Extensions → Installer/Gérer les extensions*.

Une icône est ajoutée à la barre d'outils, et un sous-menu **Extensions → BVLIP** donne accès au panneau, aux réglages, au choix de la langue et à la fiche du plugin.

### Utilisation

**1. Choisir un exutoire.** Ouvrez le panneau, cliquez sur *Cliquer un point sur la carte*, puis désignez un point sur le cours d'eau qui vous intéresse. Le point n'a pas à être précis : il est accroché au réseau, puis au chevelu.

![Panneau](screenshot/02_panneau.png)

**2. Lancer le calcul.** Trois options se décident d'un bassin à l'autre : les caractéristiques morphométriques, l'occupation du sol, et le recalcul à la maille la plus fine. Le calcul part en tâche de fond ; le bouton *Annuler* reste actif.

Trois couches sont créées **en mémoire** : le bassin, les cours d'eau amont — nommés, étiquetés, avec la longueur et la persistance de chaque tronçon — et l'exutoire sous ses quatre états — point cliqué, accroché sur la BD TOPO, recalé sur le chevelu, et point le plus éloigné hydrologiquement.

![Carte](screenshot/01_carte.png)

**3. Produire le rapport.** Le bouton dédié demande où enregistrer, puis écrit un PDF et un classeur Excel de même contenu, et propose d'ouvrir le dossier.

![Rapport](screenshot/03_rapport.png)

### Réglages

Le menu **Extensions → BVLIP → Réglages** porte les deux accrochages de l'exutoire, conservés d'une session à l'autre.

![Réglages](screenshot/04_reglages.png)

| Réglage | Défaut | Rôle |
|---|:---:|---|
| Rayon d'accrochage au réseau | 50 m | distance maximale entre le point cliqué et un tronçon BD TOPO |
| Recalage sur le chevelu | 50 m | distance à laquelle chercher un chenal du modèle de terrain |

Le panneau porte les trois options qui se décident d'un bassin à l'autre : les
caractéristiques morphométriques, l'occupation du sol et le recalcul à la maille
la plus fine. **Tout le reste n'est réglable que par l'algorithme Processing** —
résolution imposée du MNT, seuil d'ouverture des écoulements, tolérance de
simplification du contour, autorisation des bassins hors gabarit.

### Chaîne de calcul

```
Point cliqué
  → accrochage sur le tronçon BD TOPO le plus proche (50 m par défaut)
  → remontée du chevelu amont, dalle de 10 km par dalle de 10 km
      garde-fou : 80 000 tronçons, sinon refus motivé (ou reprise sur accord)
  → emprise de calcul = enveloppe du réseau amont + 2 km
  → téléchargement du MNT RGE ALTI en BIL 32 bits, maille ajustée à la mémoire
      contrôle et réparation des altitudes aberrantes du service
  → GRASS r.watershed (direction simple) : écoulement, accumulation, chevelu
  → recalage de l'exutoire sur le talweg le plus proche recevable
  → GRASS r.water.outlet : raster du bassin
  → polygonisation, plus grande pièce, trous comblés, contour simplifié
  → contrôle : le bassin contient-il 60 % de son réseau strictement amont ?
      sinon, seconde recherche de l'exutoire en suivant l'écoulement
  → option : recadrage sur le bassin et seconde passe à maille plus fine
  → caractéristiques, masse d'eau DCE, occupation du sol
  → couches en mémoire, puis rapport à la demande
```

### Sources de données

| Donnée | Source | Accès |
|---|---|---|
| Modèle numérique de terrain | RGE ALTI (IGN) | WMS Géoplateforme, format `image/x-bil;bits=32` |
| Réseau hydrographique | BD TOPO `troncon_hydrographique` | WFS Géoplateforme |
| Zones hydrographiques | BD TOPO `bassin_versant_topographique` | WFS — dimensionne l'emprise de calcul |
| Masses d'eau DCE | Référentiel Sandre | WFS `services.sandre.eaufrance.fr` |
| Occupation du sol | Corine Land Cover 2018 | WFS Géoplateforme |
| Bâti | BD TOPO `batiment`, `zone_d_habitation` | WFS Géoplateforme |
| Fond de plan du rapport | Plan IGN v2 | WMTS Géoplateforme |

### Limites connues

Elles se disent plutôt qu'elles ne se cachent. Le plugin est publié comme **expérimental** : la chaîne a été éprouvée sur l'Allier, la Besbre et leurs affluents, pas sur l'ensemble du territoire.

#### Domaine d'emploi

- **France métropolitaine et Corse seulement.** Toute la chaîne raisonne en Lambert 93 (EPSG:2154) : les coordonnées, les distances d'accrochage, l'emprise du MNT et les couches produites. Ce système ne couvre pas les départements et régions d'outre-mer, qui ne sont donc pas traités, même là où le RGE ALTI existe. Les seuils de plausibilité des altitudes — rien sous −10 m — sont eux aussi calés sur la métropole.
- **Un bassin transfrontalier est un minorant.** La BD TOPO et le RGE ALTI s'arrêtent à la frontière : un bassin dont la ligne de partage des eaux passe en Belgique, en Suisse, en Espagne, en Italie ou en Allemagne perd tout ce qui est de l'autre côté. Le plugin détecte que le contour vient toucher le bord du MNT et l'écrit en avertissement, mais il ne peut pas reconstituer le relief manquant.
- **Bassin topographique, et rien d'autre.** Le calcul suit le relief. Il ignore le karst, les drainages agricoles, les réseaux d'assainissement, les prises d'eau, les dérivations et les transferts inter-bassins. Le RGE ALTI étant un modèle de terrain, un remblai routier percé d'une buse barre l'écoulement dans le modèle alors que l'eau passe réellement dessous : en plaine, un ouvrage suffit à détourner un sous-bassin entier.
- **Rien ne fonctionne hors ligne.** Toutes les données sont téléchargées à chaque calcul, et rien n'est mis en cache d'un calcul à l'autre : deux exutoires voisins retéléchargent le même MNT. Le plugin dépend donc de la disponibilité de la Géoplateforme et du Sandre. Les téléchargements passent par le gestionnaire de réseau de QGIS, ce qui reprend les réglages de proxy du poste, avec trois tentatives et 60 s de délai par requête.

#### Taille des bassins et emprise de calcul

- **Un bassin de fleuve n'est pas calculable.** BVLIP remonte le réseau BD TOPO pour dimensionner l'emprise, et il faut avoir ce réseau en mémoire. La délimitation charge jusqu'à **80 000 tronçons** ; au-delà elle est refusée, avec la possibilité de pousser jusqu'à 200 000. Ces deux seuils sont ceux que le plugin se fixe pour tenir en mémoire, et non des limites de l'IGN : vérifié, le service pagine sans broncher jusqu'à 267 185 entités. Un affluent, ou le même cours d'eau plus haut, se calculent normalement.
- **Le garde-fou porte sur les tronçons lus, pas sur des kilomètres.** La densité du chevelu va du simple au double d'une région à l'autre : un seuil exprimé en largeur d'emprise se trompait dans les deux sens — il refusait l'Allier à Vichy, qui se charge en 56 726 tronçons, et aurait laissé passer une emprise plus petite mais bien plus dense.
- **Le chevelu se charge de proche en proche, par dalles de 10 km.** Le WFS ne filtre que par emprise : on ne peut pas lui demander « les tronçons à l'amont de celui-ci ». BVLIP charge donc la dalle de l'exutoire, remonte le graphe tant qu'il peut, et là où le parcours bute sur un nœud sans amont connu, il charge la dalle qui contient ce nœud — vague après vague, quatre requêtes de front, les dalles contiguës d'une même rangée regroupées en une seule. Mesuré sur l'Allier à Vichy : **125 dalles, 56 726 tronçons lus pour 38 013 utiles, en 77 s**, là où le rectangle englobant en demandait 267 185 et n'aboutissait pas.
- **Le refus tombe en cours de chargement, pas avant.** Le nombre de tronçons n'est connu qu'en avançant : il n'existe pas de décompte préalable dans cette chaîne. Un exutoire hors gabarit coûte donc l'attente déjà consommée. En contrepartie, si vous demandez de poursuivre, le calcul **repart de ce qui est déjà chargé** au lieu de tout refaire. Cette reprise n'existe que dans le panneau ; en traitement par lot, il faut cocher l'option des bassins hors gabarit dès le départ.
- **La remontée s'arrête au bout de 60 vagues.** Vingt-trois suffisent à remonter l'Allier de Vichy à sa source ; la borne n'existe que pour qu'une anomalie du graphe ne fasse pas tourner sans fin. Si elle est atteinte, le chevelu est incomplet et le calcul est refusé — ou, si vous avez demandé d'aller au bout, poursuivi avec un avertissement disant que le bassin est tronqué.
- **La maille du MNT est déduite de la mémoire réellement libre.** Le plugin s'autorise 35 % de la mémoire disponible, compte 40 octets par maille sur toute la chaîne et retient la maille la plus fine qui tienne — entre 2 et 60 millions de mailles. Si même 50 m ne suffit pas, le calcul s'arrête en le disant plutôt que de faire tomber QGIS sans message. La même emprise peut donc être calculée à 5 m sur un poste et à 25 m sur un autre.
- **Un refus vaut mieux qu'un bassin tronqué.** Un bassin coupé au bord de l'emprise garde l'allure d'un bassin juste : ni sa forme ni le contrôle de contenance du réseau ne le trahissent, puisque ce réseau est tronqué de la même façon et valide donc le faux résultat. C'est pourquoi le dépassement de seuil arrête le calcul au lieu de le laisser aboutir, et pourquoi le contour est vérifié contre les bords du MNT après coup.

#### Délimitation

- **L'exutoire est recalé sur le talweg, mais pas n'importe lequel.** Le tracé cartographique d'un cours d'eau et le talweg calculé depuis le MNT ne se superposent pas : mesuré à l'embouchure de deux affluents de l'Allier, l'écart va de 61 à 271 m. Le recalage suit trois règles. **Le plus proche**, et non le plus drainé, pour respecter le cours d'eau désigné — prendre le maximum ferait sauter l'exutoire sur la rivière voisine. **Parmi ceux qui peuvent être le bon** : sur le Gourcet, 625 mailles de chenal se trouvaient à moins de 60 m, la plus proche étant un ravin de 0,01 km² quand le talweg cherché en drainait 16,31 ; un cours d'eau portant 21,5 km d'affluents cartés ne peut pas drainer 90 ares, et le linéaire BD TOPO fournit cette borne — au plus 5 km de cours d'eau par km² de bassin. **Et dont le bassin tient dans le MNT** : GRASS compte négativement les mailles dont une partie du bassin sort de l'emprise calculée, ce qui désigne exactement les rivières venues d'ailleurs — l'Allier traversant l'emprise d'un de ses affluents. La recherche s'élargit tant qu'aucun chenal recevable n'est à portée, **jusqu'à 400 m** ; au-delà, ce n'est plus un écart de tracé, c'est le mauvais cours d'eau.
- **Si le bassin n'est pas confirmé, l'exutoire est cherché autrement.** La recherche par voisinage est aveugle : elle regarde autour du point cliqué et ne sait pas où va l'eau. Quand le bassin obtenu ne contient pas le réseau amont qu'il devrait, BVLIP reprend le problème par l'amont. Le terrain est dissymétrique : en tête de bassin la vallée est encaissée et le lit cartographié coïncide avec celui du MNT à quelques mètres près, alors qu'en plaine alluviale — là où tombent justement les exutoires — ils divergent de plusieurs centaines de mètres. On s'accroche donc là où la correspondance est franche, puis on **suit les flèches d'écoulement vers l'aval** jusqu'au point qui passe au plus près de l'exutoire demandé : c'est alors l'écoulement lui-même qui désigne la maille, et non un rayon de recherche. Sur le Darot, cette seconde approche rend 15,05 km² là où la première en rendait 0,04. Elle n'est tentée qu'en cas d'échec, ne coûte que l'extraction — les rasters GRASS sont déjà calculés — et ne remplace le premier résultat que si elle fait mieux.
- **Le contrôle de cohérence exige 60 % du linéaire strictement amont**, et le tronçon qui porte l'exutoire est écarté du décompte : il se prolonge vers l'aval au-delà du point de sortie, et cette partie-là est légitimement dehors — la compter faisait tomber un cas d'essai à 78 % au lieu de 100 %. En dessous de 60 %, le traitement s'arrête en disant pourquoi plutôt que de rendre un résultat faux. La part obtenue est conservée en attribut, pour que le lecteur du rapport en juge lui-même.
- **En tête de bassin, ce contrôle ne dit rien.** S'il n'existe aucun tronçon strictement à l'amont de l'exutoire, il n'y a rien à vérifier : le bassin n'est alors ni confirmé ni infirmé, et c'est précisément le cas où l'accrochage est le plus incertain. Regardez l'écart entre le point cliqué, le point accroché et le point recalé, tous trois conservés dans la couche des exutoires.
- **Le polygone est nettoyé, et ce nettoyage efface de l'information.** Seule la plus grande pièce est retenue et les trous internes sont comblés, un bassin versant étant d'un seul tenant. Une cuvette endoréique réelle à l'intérieur du bassin n'apparaîtra donc pas.
- **L'écoulement est routé en direction simple.** `r.water.outlet` ne connaît pas le chevelu : il ne lit que la carte des directions et remonte ses flèches depuis l'exutoire. En écoulement multiple, l'accumulation répartit le flux entre plusieurs voisines pendant que cette carte n'en retient qu'une, et les deux cessent de mesurer la même chose — à l'embouchure du Gourcet, 5,47 km² annoncés pour 1,02 ha extraits. En direction simple, les trois sorties viennent du même routage : 16,31 km² annoncés, 16,307 extraits. Le coût est négligeable : sur quatre bassins de 33 à 9 008 km², les surfaces bougent de 0,006 à 0,03 %.
- **Les canaux ne sont pas remontés.** Un canal n'est pas un chemin de drainage : l'eau du Canal de Roanne à Digoin vient de la Loire par dérivation, pas du ruissellement d'un bassin. La BD TOPO le relie pourtant au reste du réseau comme n'importe quel écoulement. Sur la Besbre à Diou, la remontée empruntait un chemin de 53 tronçons — Besbre → Canal Latéral à la Loire → Canal de Roanne à Digoin → la Loire — et ramenait **47 442 tronçons sur 16 100 km², l'Arroux, le Sornin, le Rhins et la Bourbince compris**, pour un bassin qui en fait un millier. Canaux, aqueducs et bassins portuaires sont donc infranchissables. Restent franchissables, et doivent le rester : les buses, sous lesquelles passent des ruisseaux ordinaires, les écoulements canalisés, qui sont des cours d'eau naturels dans un lit aménagé, et les retenues, qui sont sur le cours d'eau lui-même. En contrepartie, un bassin réellement alimenté par une dérivation est sous-estimé.
- **Le MNT est vérifié et réparé avant tout calcul.** Le service ne rend pas que du relief : sur un même kilomètre carré du bassin de l'Allier, il donne 371 à 536 m à 5 m et à 25 m de maille, mais **−97 m à 50 m**. Ces valeurs n'existent dans aucune donnée source, elles naissent du rééchantillonnage vers les mailles grossières — on ne les voyait pas tant que les petits bassins tournaient à 5 m. Non filtrées, elles ruinent tout ce qui en dépend : sur l'Allier à Vichy, une dénivelée de 6 535 m au lieu de 1 936. BVLIP repère les mailles impossibles — sous −10 m, ou plongeant de plus de 200 m sous la médiane d'un anneau à trois mailles — puis **redemande la portion fautive à une maille plus fine**, où la donnée est saine, et la ramène par moyenne de blocs. À défaut, la maille est comblée par interpolation depuis ses voisines : jamais laissée en trou, car ces mailles sont dans le fond de vallée, donc sur le lit du cours d'eau, et un trou posé là coupe l'écoulement et ampute le bassin — mesuré sur l'Allier, 8 394 km² au lieu de 9 008. Le nombre de mailles reprises est journalisé et conservé : un MNT très abîmé reste un MNT réparé, pas un MNT juste.
- **GRASS est obligatoire.** `r.watershed` et `r.water.outlet` viennent du fournisseur GRASS de QGIS. S'il est désactivé dans les options de Processing, le calcul s'arrête sur un message explicite — mais il s'arrête.

#### Précision des mesures

- **Sur un grand bassin, la maille est élargie.** Mesuré entre 5 m et 10 m sur un bassin de 146 km² : la surface et les altitudes ne bougent pas, le plus long cheminement et la pente varient de 1 à 2 %, le périmètre et l'indice de Gravelius de 2 à 3 %. Deux champs du rapport indiquent si la maille a été élargie et si un recalcul plus fin a eu lieu. L'option d'affinage recadre le calcul sur le bassin pour gagner un cran de maille ; elle allonge sensiblement le calcul et ne change pas la surface.
- **Le périmètre dépend de l'échelle de mesure.** Un contour issu d'une grille n'a pas de périmètre intrinsèque : le polygone brut suit les bords de maille en escalier, ce qui l'allonge d'environ 30 % et gonflerait l'indice de Gravelius d'autant — 1,73 au lieu de 1,30 sur un bassin d'essai. La tolérance de simplification, deux mailles par défaut, le fait encore varier de 6 % à maille constante, plus que la maille elle-même. Le périmètre avant simplification et la tolérance retenue sont conservés en attributs.
- **L'indice de Gravelius et le rectangle équivalent héritent de cette incertitude**, tous deux étant proportionnels au périmètre. Le rectangle équivalent n'existe mathématiquement que si l'indice dépasse 1,128, valeur du disque ; en dessous, le plugin renvoie un carré de même surface.
- **La pente moyenne est la moyenne des pentes en degrés**, calculée par l'algorithme de Horn sur les huit voisins, puis convertie en pourcentage par la tangente de cette moyenne. Ce n'est pas la moyenne des pentes exprimées en pourcentage : les deux diffèrent, faiblement sur un versant régulier, davantage sur un relief contrasté. La pente est en outre lissée par la maille : à 25 m, talus et ravines disparaissent.
- **Le plus long cheminement suit les huit directions de la grille**, et non une ligne libre : il est mesuré en marches d'escalier, ce qui l'allonge légèrement, et il dépend de la maille — 2,3 % d'écart entre 10 m et 5 m sur un bassin de 146 km².
- **Les temps de concentration sont quatre formules empiriques**, employées hors de leur domaine sur beaucoup de bassins : Kirpich vise les petits bassins ruraux pentus, Giandotti demande une dénivelée utile, Passini et Ventura combinent surface et pente. C'est leur **dispersion** qui renseigne, pas une valeur isolée — elles divergent volontiers d'un facteur deux. Une formule dont les conditions ne sont pas réunies rend une case vide plutôt qu'un nombre trompeur. Aucune ne remplace une étude hydrologique : ce sont des ordres de grandeur.
- **La densité de drainage mesure la BD TOPO, pas le terrain.** Elle rapporte le linéaire hydrographique cartographié contenu dans le bassin à sa surface : elle dépend donc de la finesse du levé, et elle inclut les écoulements intermittents, qui représentaient les deux tiers du linéaire sur un bassin d'essai.
- **La courbe hypsométrique tient en neuf points** — 0, 5, 10, 25, 50, 75, 90, 95 et 100 % : de quoi lire la forme du bassin, pas de quoi en tirer une intégrale hypsométrique fine.
- **Les altitudes sont celles du RGE ALTI**, en mètres NGF, sur un modèle de **terrain** : ni la végétation ni le bâti n'y figurent, et la précision altimétrique varie selon la source du levé — LiDAR, corrélation, radar — et selon le relief.

#### Données annexes

- **La masse d'eau DCE est rattachée par l'exutoire, pas par le bassin.** Le point est cherché dans les bassins versants spécifiques du Sandre, état des lieux 2019. S'il ne tombe dans aucun polygone, la masse d'eau la plus proche dans un rayon de 250 m est retenue et le champ *Exutoire situé dans le bassin de la masse d'eau* passe à « non » : la valeur n'est alors qu'indicative.
- **Le détail de la masse d'eau rivière n'est pas récupéré.** Nom, type, longueur totale, bassin DCE et ordre de Strahler restent vides : le service Sandre n'applique aucun filtre attributaire côté serveur, si bien qu'il faudrait rapatrier la couche nationale entière — une quarantaine de secondes — pour n'en retenir qu'une ligne. Seuls le code européen, la dénomination et la surface du bassin versant spécifique sont renseignés.
- **Corine Land Cover efface les hameaux** sous son unité minimale de collecte de 25 ha, et le millésime est celui de **2018**. C'est pourquoi le bâti de la BD TOPO est mesuré à part — emprise au sol des bâtiments, zones d'habitation — sans jamais être additionné à CLC, ce qui compterait deux fois les mêmes surfaces. Le taux de couverture réellement atteint par CLC est conservé.
- **Le bâti est l'étape la plus coûteuse** sur un grand bassin : la BD TOPO y compte des dizaines de milliers de polygones, lus page par page. Si le service refuse ou si le budget d'entités est atteint, les champs restent vides et le reste du rapport est produit.
- **Les trois enrichissements ne bloquent jamais le calcul.** Caractéristiques, masse d'eau et occupation du sol sont tentés après la délimitation : un service indisponible ajoute un avertissement dans le journal et laisse les champs correspondants vides, mais le bassin, lui, est produit.
- **Le SCAN 25 n'est pas en accès libre.** La Géoplateforme ne sert publiquement que le SCAN 1000, le SCAN Régional, le SCAN 50 de 1950, le Plan IGN v2 et les cartes d'État-Major. Le rapport utilise donc le Plan IGN v2 ; si le service de tuiles n'est pas joignable, la carte sort sans fond de plan.

#### Interface et sorties

- **Rien n'est écrit sur disque tant que vous ne le demandez pas.** Les trois couches sont créées en mémoire : fermer QGIS sans les exporter, ou sans enregistrer le projet, perd le résultat. C'est délibéré — un essai qui ne convient pas ne laisse aucun fichier derrière lui — mais il faut le savoir.
- **Le rapport ne porte que le dernier bassin calculé**, et seulement depuis le panneau. Le traitement par lot produit les couches, pas les rapports : il faut repasser par le panneau, un bassin à la fois.
- **La page A4 s'arrête quand elle est pleine.** Les sections de caractéristiques sont posées dans l'ordre et celles qui ne tiennent plus sont omises du PDF. Le classeur Excel, lui, porte le détail complet sur trois onglets : caractéristiques, occupation du sol, cours d'eau amont.
- **Dans le classeur, les graphiques sont sous le tableau** et non à sa droite comme sur la page A4 : côte à côte, la largeur dépasserait la feuille A4 portrait.
- **À l'export Shapefile**, 35 des 62 noms de champs sont tronqués à dix caractères et les intitulés avec unités sont perdus, ce format ne sachant pas les stocker. Aucun nom ne se télescope, c'est vérifié. Préférer le **GeoPackage**.
- **L'annulation est prise en compte entre deux étapes.** Un téléchargement engagé va à son terme — au plus 60 s par requête — avant que la demande d'arrêt ne soit vue : le bouton rend la main en quelques secondes, pas instantanément.
- **Seuls les deux rayons d'accrochage se règlent dans l'interface.** La résolution imposée du MNT, le seuil d'ouverture des écoulements et la tolérance de simplification du contour ne sont exposés que par l'algorithme Processing.
- **Sans `matplotlib`, le rapport sort sans ses graphiques ; sans `openpyxl`, sans son classeur.** Les deux sont livrés avec l'installation Windows de QGIS ; leur absence est signalée dans le journal et n'interrompt rien.
- **Rien n'est laissé dans le dossier temporaire.** Chaque calcul écrit 50 à 300 Mo de fichiers de travail — le MNT et les rasters d'écoulement de GRASS. Ils sont supprimés en sortant, que le calcul aboutisse ou échoue, et un balayage au démarrage ramasse ce qu'une session fermée brutalement aurait oublié, au-delà de six heures pour ne pas effacer le répertoire d'une autre instance de QGIS ouverte en même temps. C'est un défaut corrigé, pas une précaution théorique : relevé sur un poste, **116 dossiers et 6 Go**, jusqu'à saturer le disque — et le symptôme n'était pas « disque plein » mais un raster tronqué en plein calcul, `TIFFReadDirectory: Failed to read directory at offset 368`, que rien ne reliait à sa cause.

---

## English

### Description

BVLIP delineates the topographic watershed drained by a point picked on the map, computes its morphometric and hydrological characteristics, and produces an A4 map report. The RGE ALTI elevation model and the BD TOPO hydrographic network are downloaded on the fly from the French IGN Géoplateforme.

No more fetching, mosaicking and reprojecting a DEM before you can start: pick an outlet, and the plugin works out the useful extent, downloads what it needs, delineates, measures and lays out. Around twenty seconds for a catchment of a few square kilometres, and QGIS stays usable throughout.

### Features

- **No data preparation**: RGE ALTI, BD TOPO, Sandre water bodies and Corine Land Cover are queried online, with no API key.
- **No external dependency**: the computation relies on GRASS, shipped with QGIS. Neither TauDEM nor WhiteboxTools to install.
- **Two-stage outlet snapping**: the clicked point is first pulled onto the BD TOPO line, then re-snapped onto the channel network derived from the terrain model. The two do not coincide — in valley bottoms they commonly differ by tens of metres.
- **Consistency check**: the resulting catchment must contain the network it drains. Below 60 % of the strictly upstream length, processing stops and says why rather than returning a wrong answer.
- **Cell size matched to the machine**: DEM resolution is derived from the memory actually free at run time — 5 m on a small catchment, 10 or 25 m over several hundred square kilometres.
- **Background processing**, with a cancel button: the map stays navigable and progress shows in the QGIS task bar.
- **Full characterisation**: 62 fields, every one labelled with its unit — area, perimeter, Gravelius compactness index, equivalent rectangle, hypsometry, slopes, global slope index, specific relief, longest flow path, drainage density, time of concentration by four formulas.
- **Water Framework Directive water body** from the Sandre reference dataset.
- **Land cover** from Corine Land Cover 2018, complemented by BD TOPO buildings.
- **A4 report** as PDF and as an Excel workbook.
- **Batch processing** through a Processing algorithm. A point that fails does not stop the batch.
- **Interface in five languages**, switchable from the plugin menu.

### Requirements

- **QGIS 3.40** or later, with the GRASS provider enabled in the Processing options.
- **Internet access**: all data is downloaded on demand.
- Territory covered by **RGE ALTI** in Lambert 93, that is, mainland France and Corsica. The overseas departments are not handled.

> **Recommended** — `matplotlib` and `openpyxl`, both shipped with the Windows install of QGIS. Without the first, the report comes without its charts; without the second, only the PDF is produced.

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/Cartoyoyo/BVLIP.git
   ```

2. Copy the `BVLIP` folder into the plugins directory of your QGIS profile — see the paths table in the French section.

3. Enable **BVLIP** under *Plugins → Manage and Install Plugins*.

### Usage

Open the panel, click *Pick a point on the map*, designate a point on the watercourse, then run. Three memory layers are created: the catchment, the upstream reaches with their individual lengths, and the outlet in its four states. A dedicated button produces the report.

> Workflow screenshots are in the [Aperçu rapide](#aperçu-rapide--quick-overview) section at the top of this document.

### Known limitations

Stated rather than hidden. The plugin is published as **experimental**: the chain has been exercised on the Allier, the Besbre and their tributaries, not across the whole country.

#### Scope

- **Mainland France and Corsica only.** The whole chain works in Lambert 93 (EPSG:2154): coordinates, snapping distances, DEM extent and output layers. That system does not cover the French overseas departments, which are therefore not handled even where RGE ALTI exists. The elevation plausibility bounds — nothing below −10 m — are likewise set for mainland France.
- **A transboundary basin is a lower bound.** BD TOPO and RGE ALTI stop at the border: a basin whose divide runs through Belgium, Switzerland, Spain, Italy or Germany loses everything on the other side. The plugin detects that the outline touches the DEM edge and says so in a warning, but it cannot reconstruct the missing relief.
- **A topographic catchment, and nothing more.** The computation follows the terrain. It ignores karst, field drainage, sewer networks, water intakes, diversions and inter-basin transfers. RGE ALTI being a terrain model, a road embankment pierced by a culvert blocks the flow in the model although water really passes underneath: on flat ground, one structure is enough to divert a whole sub-catchment.
- **Nothing works offline.** All data is downloaded on every run and nothing is cached between runs: two neighbouring outlets re-download the same DEM. The plugin therefore depends on the availability of the Géoplateforme and of Sandre. Downloads go through the QGIS network manager, so the machine's proxy settings apply, with three attempts and a 60 s timeout per request.

#### Basin size and computation extent

- **A whole river basin cannot be computed.** BVLIP walks the BD TOPO network to size the extent, and that network has to be held in memory. Delineation loads up to **80,000 reaches**; beyond that it is refused, with an option to push to 200,000. Both thresholds are the plugin's own, set to stay within memory, not IGN limits: the service was verified to page through 267,185 features without complaint. A tributary, or the same river further upstream, computes normally.
- **The guard counts reaches actually read, not kilometres.** Network density varies twofold from one region to another: a threshold expressed as an extent width was wrong in both directions — it refused the Allier at Vichy, which loads in 56,726 reaches, and would have let through a smaller but far denser extent.
- **The network is loaded step by step, in 10 km tiles.** The WFS only filters by extent: it cannot be asked for "the reaches upstream of this one". So BVLIP loads the outlet's tile, walks the graph as far as it can, and wherever the walk stops at a node with no known upstream, loads the tile containing that node — wave after wave, four requests in parallel, contiguous tiles of one row merged into a single request. Measured on the Allier at Vichy: **125 tiles, 56,726 reaches read for 38,013 useful ones, in 77 s**, where the bounding rectangle asked for 267,185 and never completed.
- **The refusal comes mid-load, not before.** The reach count is only known as the walk advances: there is no prior count in this chain. An oversized outlet therefore costs the wait already spent. In exchange, if you ask to continue, the run **resumes from what is already loaded** instead of starting over. That resume exists only in the panel; in batch processing the oversize option must be ticked up front.
- **The walk stops after 60 waves.** Twenty-three are enough to climb the Allier from Vichy to its source; the bound only exists so a graph anomaly cannot loop forever. If it is reached the network is incomplete and the run is refused — or, if you asked to go all the way, continued with a warning that the basin is clipped.
- **DEM cell size is derived from the memory actually free.** The plugin allows itself 35 % of available memory, counts 40 bytes per cell across the whole chain and keeps the finest cell size that fits — between 2 and 60 million cells. If even 50 m does not fit, the run stops and says so rather than bringing QGIS down without a message. The same extent may therefore run at 5 m on one machine and 25 m on another.
- **A refusal beats a clipped basin.** A basin cut at the extent border still looks like a correct one: neither its shape nor the network-containment check gives it away, since that network is clipped the same way and therefore validates the wrong result. Hence the guard stops the run instead of letting it finish, and the outline is checked against the DEM borders afterwards.

#### Delineation

- **The outlet is snapped to a thalweg, but not just any.** A river's mapped line and the thalweg computed from the DEM do not coincide: measured at the mouth of two Allier tributaries, the gap runs from 61 to 271 m. The snap follows three rules. **Nearest**, not most drained, to respect the designated watercourse — taking the maximum would jump the outlet onto the neighbouring river. **Among those that can be the right one**: on the Gourcet, 625 channel cells lay within 60 m, the nearest a 0.01 km² gully while the sought thalweg drained 16.31; a river carrying 21.5 km of mapped tributaries cannot drain 90 ares, and the BD TOPO network length supplies that bound — at most 5 km of watercourse per km² of basin. **And whose basin fits inside the DEM**: GRASS counts negatively the cells whose basin partly leaves the computed extent, which names exactly the rivers coming from elsewhere — the Allier crossing the extent of one of its own tributaries. The search widens while no eligible channel is in range, **up to 400 m**; beyond that it is no longer a mapping offset, it is the wrong river.
- **If the basin is not confirmed, the outlet is sought another way.** The neighbourhood search is blind: it looks around the clicked point and does not know where the water goes. When the resulting basin fails to contain the upstream network it should, BVLIP takes the problem from upstream instead. The terrain is asymmetric: in the headwaters the valley is confined and the mapped bed matches the DEM's to within metres, whereas on the alluvial plain — exactly where outlets fall — the two diverge by hundreds of metres. So the anchor is placed where the match is unambiguous, then the **flow-direction arrows are followed downstream** to the point passing closest to the requested outlet. On the Darot this second approach returns 15.05 km² where the first returned 0.04. It is tried only on failure, costs no more than the extraction — the GRASS rasters are already computed — and replaces the first result only if it does better.
- **The consistency check requires 60 % of the strictly upstream length**, and the reach carrying the outlet is left out of the count: it continues downstream past the outlet point, and that part is legitimately outside — counting it dropped a test case to 78 % instead of 100 %. Below 60 % the run stops and says why rather than returning a wrong answer. The value obtained is kept as an attribute so the reader can judge for themselves.
- **In a headwater catchment that check says nothing.** If no reach lies strictly upstream of the outlet there is nothing to verify: the basin is then neither confirmed nor refuted — and that is precisely the case where snapping is least certain. Look at the gap between the clicked, snapped and re-snapped points, all three kept in the outlet layer.
- **The polygon is cleaned, and cleaning erases information.** Only the largest piece is kept and interior holes are filled, a catchment being a single body. A genuine endorheic depression inside the basin will therefore not show.
- **Flow is routed single-direction.** `r.water.outlet` knows nothing of the stream network: it only reads the flow-direction map and walks its arrows back from the outlet. Under multiple-flow routing, accumulation spreads across several neighbours while that map keeps only one, and the two stop measuring the same thing — at the Gourcet's mouth, 5.47 km² announced against 1.02 ha extracted. Single-direction makes all three outputs come from one routing: 16.31 km² announced, 16.307 extracted. The cost is negligible: over four basins from 33 to 9,008 km², areas move by 0.006 to 0.03 %.
- **Canals are not walked up.** A canal is not a drainage path: water in the Canal de Roanne à Digoin comes from the Loire by diversion, not from a catchment's runoff. BD TOPO nonetheless links it to the rest of the network like any watercourse. On the Besbre at Diou the walk took a 53-reach path — Besbre → Canal Latéral à la Loire → Canal de Roanne à Digoin → the Loire — and brought back **47,442 reaches over 16,100 km², the Arroux, Sornin, Rhins and Bourbince included**, for a basin of about a thousand. Canals, aqueducts and port basins are therefore impassable. Still passable, and must remain so: culverts, under which ordinary streams pass, canalised watercourses, which are natural rivers in an engineered bed, and reservoirs, which sit on the river itself. In exchange, a basin genuinely fed by a diversion is underestimated.
- **The DEM is checked and repaired before any computation.** The service does not only return terrain: over one square kilometre of the Allier basin it gives 371 to 536 m at 5 m and at 25 m cell size, but **−97 m at 50 m**. Those values exist in no source data; they are born of resampling to coarse cells, and went unseen while small catchments ran at 5 m. Unfiltered they wreck everything downstream: on the Allier at Vichy, a 6,535 m relief instead of 1,936. BVLIP flags impossible cells — below −10 m, or more than 200 m under the median of a three-cell ring — then **re-requests the offending patch at a finer cell size**, where the data is sound, and averages it back down. Failing that, a cell is filled by interpolation from its neighbours: never left as a hole, since these cells lie on the valley floor, hence on the river bed, and a hole there severs the flow and truncates the basin — measured on the Allier, 8,394 km² instead of 9,008. The number of repaired cells is logged and kept: a badly damaged DEM stays a repaired DEM, not a correct one.
- **GRASS is required.** `r.watershed` and `r.water.outlet` come from the QGIS GRASS provider. If it is disabled in the Processing options the run stops with an explicit message — but it stops.

#### Measurement accuracy

- **On a large catchment the cell size is enlarged.** Measured between 5 m and 10 m over 146 km²: area and elevations do not move, longest flow path and slope vary by 1 to 2 %, perimeter and Gravelius by 2 to 3 %. Two report fields state whether the cell size was enlarged and whether a finer recomputation took place. The refine option re-frames the computation on the basin to gain one cell-size step; it lengthens the run appreciably and does not change the area.
- **A raster-derived perimeter has no intrinsic value.** The raw polygon follows cell edges in a staircase, which lengthens it by about 30 % and would inflate the Gravelius index as much — 1.73 instead of 1.30 on a test basin. The simplification tolerance, two cells by default, then moves it by a further 6 % at constant cell size, more than the cell size itself. The pre-simplification perimeter and the tolerance used are kept as attributes.
- **The Gravelius index and the equivalent rectangle inherit that uncertainty**, both being proportional to the perimeter. The equivalent rectangle only exists mathematically if the index exceeds 1.128, the value for a disc; below that the plugin returns a square of the same area.
- **Mean slope is the mean of slopes in degrees**, computed by Horn's algorithm over the eight neighbours, then converted to a percentage by the tangent of that mean. It is not the mean of the percentage slopes: the two differ, slightly on a regular hillside, more on broken relief. Slope is also smoothed by the cell size: at 25 m, banks and gullies vanish.
- **The longest flow path follows the eight grid directions**, not a free line: it is measured as a staircase, which lengthens it slightly, and it depends on cell size — 2.3 % between 10 m and 5 m on a 146 km² basin.
- **Times of concentration are four empirical formulas**, used outside their domain on many basins: Kirpich targets small steep rural catchments, Giandotti needs a useful relief, Passini and Ventura combine area and slope. It is their **spread** that informs, not any single value — they readily differ by a factor of two. A formula whose conditions are not met returns an empty cell rather than a misleading number. None replaces a hydrological study: these are orders of magnitude.
- **Drainage density measures BD TOPO, not the terrain.** It divides the mapped stream length contained in the basin by its area: it therefore depends on survey detail, and it includes intermittent streams, which were two thirds of the length on a test basin.
- **The hypsometric curve holds nine points** — 0, 5, 10, 25, 50, 75, 90, 95 and 100 %: enough to read the shape of the basin, not to derive a fine hypsometric integral.
- **Elevations are RGE ALTI's**, in metres NGF, on a **terrain** model: neither vegetation nor buildings are included, and vertical accuracy varies with the survey source — LiDAR, correlation, radar — and with relief.

#### Ancillary data

- **The WFD water body is attached through the outlet, not the basin.** The point is looked up in the Sandre specific catchments (2019 assessment). If it falls in no polygon, the nearest water body within 250 m is used and the *outlet inside the water body catchment* field turns to "no": the value is then indicative only.
- **River water body details are not fetched.** Name, type, total length, RBD basin and Strahler order stay empty: the Sandre service applies no server-side attribute filter, so the entire national layer would have to be downloaded — some forty seconds — to keep a single row. Only the European code, the designation and the specific catchment area are filled in.
- **Corine Land Cover erases hamlets** below its 25 ha minimum mapping unit, and the vintage is **2018**. That is why BD TOPO buildings are measured separately — building footprints and settlement areas — and never added to CLC, which would count the same surfaces twice. The coverage actually reached by CLC is kept.
- **Buildings are the costliest step** on a large basin: BD TOPO holds tens of thousands of polygons there, read page by page. If the service refuses or the feature budget is reached, the fields stay empty and the rest of the report is produced.
- **The three enrichment steps never block the run.** Metrics, water body and land cover are attempted after delineation: an unavailable service adds a warning to the log and leaves the matching fields empty, but the basin itself is produced.
- **SCAN 25 is not freely available**; the Géoplateforme only serves SCAN 1000, Régional, the 1950 SCAN 50, Plan IGN v2 and the État-Major maps openly. The report therefore uses Plan IGN v2, and comes without a basemap if the tile service cannot be reached.

#### Interface and outputs

- **Nothing is written to disk until you ask.** The three layers are created in memory: closing QGIS without exporting them, or without saving the project, loses the result. This is deliberate — a trial run that does not suit leaves no file behind — but it must be known.
- **The report covers the last computed basin only**, and only from the panel. Batch processing produces layers, not reports: you must come back through the panel, one basin at a time.
- **The A4 page stops when it is full.** Characteristic sections are laid out in order and those that no longer fit are omitted from the PDF. The Excel workbook carries the complete detail over three sheets: characteristics, land cover, upstream reaches.
- **In the workbook the charts sit below the table**, not beside it: side by side they would not fit an A4 portrait page.
- **On Shapefile export**, 35 of the 62 field names are truncated to ten characters and the unit-bearing labels are lost. No two names collide, that is verified. Prefer **GeoPackage**.
- **Cancellation is honoured between steps.** A download already under way runs to completion — at most 60 s per request — before the stop request is seen: the button gives back control in seconds, not instantly.
- **Only the two snapping radii are exposed in the interface.** A forced DEM resolution, the stream-opening threshold and the outline simplification tolerance are available through the Processing algorithm only.
- **Without `matplotlib` the report comes without its charts; without `openpyxl`, without its workbook.** Both ship with the Windows install of QGIS; their absence is logged and stops nothing.
- **Nothing is left in the temporary folder.** Each run writes 50 to 300 MB of working files — the DEM and GRASS's flow rasters. They are removed on the way out, whether the run succeeds or fails, and a sweep at start-up picks up whatever a brutally closed session forgot, after six hours so as not to delete the folder of another QGIS instance running at the same time. This is a fixed defect, not a theoretical precaution: observed on one machine, **116 folders and 6 GB**, until the disk filled — and the symptom was not "disk full" but a truncated raster mid-run, `TIFFReadDirectory: Failed to read directory at offset 368`, with nothing tying it to its cause.

---

## Español

### Descripción

BVLIP delimita la cuenca hidrográfica topográfica drenada por un punto elegido en el mapa, calcula sus características morfométricas e hidrológicas y genera un informe cartográfico A4. El modelo digital del terreno RGE ALTI y la red hidrográfica BD TOPO se descargan al vuelo desde la Géoplateforme del IGN francés.

### Funcionalidades

- Ninguna preparación de datos, ninguna dependencia externa : el cálculo se apoya en GRASS, incluido en QGIS.
- Ajuste del punto de salida en dos etapas : primero a la red BD TOPO, después a la red de cauces deducida del modelo del terreno.
- Control de coherencia : la cuenca debe contener la red que drena.
- Malla adaptada a la memoria disponible del equipo.
- Cálculo en segundo plano, con botón de cancelación.
- 62 campos, todos con su unidad ; masa de agua DMA, ocupación del suelo.
- Informe A4 en PDF y en libro de Excel ; tratamiento por lotes mediante Processing.
- Interfaz en cinco idiomas.

### Instalación

Copiar la carpeta `BVLIP` en el directorio de complementos del perfil de QGIS, después activar **BVLIP** en *Complementos → Administrar e instalar complementos*. Requiere QGIS 3.40 o superior y acceso a Internet.

> Las capturas de pantalla del flujo de trabajo se encuentran en la sección [Aperçu rapide](#aperçu-rapide--quick-overview) al inicio de este documento.

### Limitaciones conocidas

- **Solo Francia metropolitana y Córcega** : toda la cadena trabaja en Lambert 93 (EPSG:2154). Una cuenca transfronteriza queda truncada, ya que la BD TOPO y el RGE ALTI se detienen en la frontera.
- **Cuenca topográfica únicamente** : no se tienen en cuenta el karst, los drenajes agrícolas, las redes de saneamiento ni las derivaciones. Los canales y acueductos no se remontan, por lo que una cuenca alimentada por una derivación queda subestimada.
- **No se calcula la cuenca de un río principal** : la delimitación carga hasta 80 000 tramos, con la posibilidad de llegar a 200 000. El rechazo se produce durante la carga, no antes ; continuar reanuda lo ya descargado.
- **Un rechazo es preferible a una cuenca truncada** : una cuenca cortada en el borde de la extensión conserva el aspecto de una cuenca correcta y ninguna comprobación posterior la delata.
- **La malla se adapta a la memoria libre** : de 5 m en una cuenca pequeña a 25 o 50 m en varios cientos de km². El perímetro y el índice de Gravelius dependen además de la tolerancia de simplificación.
- **Los tiempos de concentración son cuatro fórmulas empíricas** : lo que informa es su dispersión, no un valor aislado. No sustituyen a un estudio hidrológico.
- **Corine Land Cover 2018 borra las aldeas** por debajo de su unidad mínima de 25 ha ; por eso la edificación de la BD TOPO se mide aparte, sin sumarse.
- **Nada se escribe en disco** : las tres capas se crean en memoria. Cerrar QGIS sin exportarlas pierde el resultado. Se requiere conexión a Internet y el proveedor GRASS activado.

> El detalle completo, con las mediciones que lo respaldan, está en la sección francesa [Limites connues](#limites-connues).

---

## Português

### Descrição

O BVLIP delimita a bacia hidrográfica topográfica drenada por um ponto escolhido no mapa, calcula as suas características morfométricas e hidrológicas e produz um relatório cartográfico A4. O modelo digital do terreno RGE ALTI e a rede hidrográfica BD TOPO são descarregados no momento a partir da Géoplateforme do IGN francês.

### Funcionalidades

- Nenhuma preparação de dados, nenhuma dependência externa : o cálculo assenta no GRASS, incluído no QGIS.
- Ajuste do exutório em duas etapas : primeiro à rede BD TOPO, depois à rede de canais deduzida do modelo do terreno.
- Controlo de coerência : a bacia tem de conter a rede que drena.
- Malha ajustada à memória disponível na máquina.
- Cálculo em segundo plano, com botão de cancelamento.
- 62 campos, todos com a respetiva unidade ; massa de água DQA, ocupação do solo.
- Relatório A4 em PDF e em livro Excel ; processamento em lote através do Processing.
- Interface em cinco idiomas.

### Instalação

Copiar a pasta `BVLIP` para o diretório de módulos do perfil QGIS, depois ativar **BVLIP** em *Módulos → Gerir e instalar módulos*. Requer QGIS 3.40 ou superior e acesso à Internet.

> As capturas de ecrã do fluxo de trabalho encontram-se na secção [Aperçu rapide](#aperçu-rapide--quick-overview) no início deste documento.

### Limitações conhecidas

- **Apenas França metropolitana e Córsega** : toda a cadeia trabalha em Lambert 93 (EPSG:2154). Uma bacia transfronteiriça fica truncada, pois a BD TOPO e o RGE ALTI param na fronteira.
- **Bacia topográfica apenas** : cársico, drenagens agrícolas, redes de saneamento e derivações não são tidos em conta. Canais e aquedutos não são percorridos a montante, pelo que uma bacia alimentada por derivação é subestimada.
- **A bacia de um rio principal não é calculável** : a delimitação carrega até 80 000 troços, com a possibilidade de ir até 200 000. A recusa ocorre durante o carregamento, não antes ; continuar retoma o que já foi descarregado.
- **Uma recusa é melhor do que uma bacia truncada** : uma bacia cortada no limite da extensão mantém o aspeto de uma bacia correta e nenhuma verificação posterior a denuncia.
- **A malha ajusta-se à memória livre** : de 5 m numa bacia pequena a 25 ou 50 m em várias centenas de km². O perímetro e o índice de Gravelius dependem ainda da tolerância de simplificação.
- **Os tempos de concentração são quatro fórmulas empíricas** : o que informa é a sua dispersão, não um valor isolado. Não substituem um estudo hidrológico.
- **O Corine Land Cover 2018 apaga os lugarejos** abaixo da sua unidade mínima de 25 ha ; por isso o edificado da BD TOPO é medido à parte, sem ser somado.
- **Nada é escrito em disco** : as três camadas são criadas em memória. Fechar o QGIS sem as exportar perde o resultado. É necessária ligação à Internet e o fornecedor GRASS ativado.

> O detalhe completo, com as medições que o fundamentam, está na secção francesa [Limites connues](#limites-connues).

---

## Deutsch

### Beschreibung

BVLIP grenzt das topografische Einzugsgebiet ab, das von einem auf der Karte gewählten Punkt entwässert wird, berechnet dessen morphometrische und hydrologische Kennwerte und erzeugt einen A4-Kartenbericht. Das Geländemodell RGE ALTI und das Gewässernetz BD TOPO werden zur Laufzeit von der Géoplateforme des französischen IGN geladen.

### Funktionen

- Keine Datenvorbereitung, keine externe Abhängigkeit : die Berechnung stützt sich auf GRASS, das QGIS beiliegt.
- Zweistufiger Fang des Auslasses : zuerst auf das BD-TOPO-Netz, dann auf das aus dem Geländemodell abgeleitete Gerinnenetz.
- Konsistenzprüfung : das Einzugsgebiet muss das Netz enthalten, das es entwässert.
- Zellgröße an den verfügbaren Arbeitsspeicher angepasst.
- Berechnung im Hintergrund, mit Abbrechen-Schaltfläche.
- 62 Felder, alle mit ihrer Einheit ; WRRL-Wasserkörper, Landbedeckung.
- A4-Bericht als PDF und als Excel-Arbeitsmappe ; Stapelverarbeitung über Processing.
- Oberfläche in fünf Sprachen.

### Installation

Den Ordner `BVLIP` in das Erweiterungsverzeichnis des QGIS-Profils kopieren, dann **BVLIP** unter *Erweiterungen → Erweiterungen verwalten und installieren* aktivieren. Erfordert QGIS 3.40 oder neuer und Internetzugang.

> Die Screenshots des Arbeitsablaufs finden sich im Abschnitt [Aperçu rapide](#aperçu-rapide--quick-overview) am Anfang dieses Dokuments.

### Bekannte Grenzen

- **Nur Festlandfrankreich und Korsika** : die gesamte Kette rechnet in Lambert 93 (EPSG:2154). Ein grenzüberschreitendes Einzugsgebiet wird abgeschnitten, da BD TOPO und RGE ALTI an der Grenze enden.
- **Ausschließlich topografisches Einzugsgebiet** : Karst, landwirtschaftliche Dränagen, Kanalnetze und Ableitungen bleiben unberücksichtigt. Kanäle und Aquädukte werden nicht flussaufwärts verfolgt, weshalb ein durch Ableitung gespeistes Gebiet unterschätzt wird.
- **Das Einzugsgebiet eines Hauptflusses ist nicht berechenbar** : die Abgrenzung lädt bis zu 80 000 Gewässerabschnitte, auf Wunsch bis 200 000. Die Ablehnung erfolgt während des Ladens, nicht davor ; beim Fortsetzen wird das bereits Geladene weiterverwendet.
- **Eine Ablehnung ist besser als ein abgeschnittenes Gebiet** : ein am Rand des Ausschnitts gekapptes Einzugsgebiet sieht weiterhin plausibel aus, und keine nachgelagerte Prüfung entlarvt es.
- **Die Zellgröße richtet sich nach dem freien Arbeitsspeicher** : 5 m bei kleinen Gebieten, 25 oder 50 m bei mehreren hundert km². Umfang und Gravelius-Index hängen zusätzlich von der Vereinfachungstoleranz ab.
- **Die Konzentrationszeiten sind vier empirische Formeln** : aussagekräftig ist ihre Streuung, nicht ein Einzelwert. Sie ersetzen keine hydrologische Studie.
- **Corine Land Cover 2018 löscht Weiler** unterhalb seiner Mindestkartierfläche von 25 ha ; deshalb wird die Bebauung der BD TOPO getrennt erfasst und nicht addiert.
- **Nichts wird auf die Festplatte geschrieben** : die drei Layer entstehen im Speicher. Wer QGIS ohne Export schließt, verliert das Ergebnis. Internetzugang und aktivierter GRASS-Anbieter sind erforderlich.

> Die vollständigen Angaben mit den zugrunde liegenden Messungen stehen im französischen Abschnitt [Limites connues](#limites-connues).

---

## Architecture

Le plugin sépare le calcul de l'interface : `core/` ne dépend ni du panneau ni de Qt au-delà des classes de géométrie, ce qui permet aux deux points d'entrée — le panneau et l'algorithme Processing — d'appeler la même chaîne sans jamais diverger.

| Paquet | Rôle |
|---|---|
| `core/` | géoservices, réseau hydrographique, MNT, délimitation, caractéristiques, masse d'eau, occupation du sol, orchestration |
| `gui/` | panneau, tâche de fond, outil de carte, réglages, fiche du plugin |
| `processing/` | fournisseur et algorithme de traitement par lot |
| `report/` | graphiques, mise en page A4, PDF, classeur Excel |
| `i18n/` | traductions embarquées, cinq langues |
| `tools/` | contrôles avant publication et fabrication de l'archive |

Trois contrôles s'exécutent avant chaque publication :

```bash
python tools/check_i18n.py      # aucune clé manquante ni orpheline
python tools/check_fields.py    # unités, unicité, longueur des intitulés
python tools/build_zip.py       # archive prête pour plugins.qgis.org
```

Le dépôt sur plugins.qgis.org se fait ensuite par `tools/publish.py`, qui lit
les identifiants OSGeo dans l'environnement ou les demande au clavier — jamais
en argument de ligne de commande, où ils resteraient dans l'historique du shell.

## Changelog

Le détail complet, avec les mesures qui ont motivé chaque correction, est dans [`CHANGELOG.md`](CHANGELOG.md).

| Version | Notes |
|---------|-------|
| **0.9.2** | Chevelu chargé par dalles — bassins hors gabarit refusés, avec reprise — canaux non remontés — altitudes aberrantes du MNT réparées |
| **0.9.1** | Nouveau logo : ligne de partage, chevelu et exutoire |
| **0.9.0** | Cours d'eau amont nommés et étiquetés — trait tireté pour les écoulements intermittents |
| **0.8.3** | README de présentation avec captures — contrôle de la longueur des intitulés |
| **0.8.2** | Téléchargements par le gestionnaire réseau de QGIS, proxy pris en compte — 43 énumérations Qt6 cadrées — outils de prépublication |
| **0.8.1** | Repères d'exutoire qui ne s'accumulent plus — classeur Excel non coupé à l'impression — groupes de couches nommés |
| **0.8.0** | Recalage de l'exutoire sur le chevelu du MNT — contrôle que le bassin contient son réseau amont |
| **0.7.x** | Calcul en tâche de fond avec annulation — panneau resserré, réglages dans le menu de l'extension |
| **0.6.x** | Maille du MNT ajustée à la mémoire disponible — économies de mémoire, option de recalcul fin |
| **0.5.x** | Rapport A4 en PDF et en classeur Excel — couches créées en mémoire |
| **0.4.0** | Algorithme Processing et branchement du panneau — pagination WFS |
| **0.3.0** | Caractéristiques morphométriques, masse d'eau DCE, occupation du sol |
| **0.2.0** | Cœur de calcul : emprise, MNT, délimitation GRASS |
| **0.1.0** | Squelette du plugin |

---

<div align="center">

Développé par / Developed by **Yoan Laloux**

Technicien SIG — Vichy Communauté · GIS Technician — Vichy Communauté

[![LinkedIn](https://img.shields.io/badge/LinkedIn-ylaloux-0A66C2?logo=linkedin&logoColor=white)](https://www.linkedin.com/in/ylaloux/)
[![GitHub](https://img.shields.io/badge/GitHub-Cartoyoyo-black?logo=github)](https://github.com/Cartoyoyo)

*Concept et idée originale par Yoan Laloux — développé avec l'assistance d'outils d'IA générative.*
*Concept and original idea by Yoan Laloux — developed with the assistance of generative AI tools.*

</div>

---

## Licence · License

Ce plugin est distribué sous licence **GNU General Public License v3** — voir [`LICENSE`](LICENSE).

This plugin is released under the **GNU General Public License v3** — see [`LICENSE`](LICENSE).

Données : RGE ALTI et BD TOPO © IGN · Corine Land Cover 2018 © Union européenne, SDES · Référentiel des masses d'eau © Sandre / OFB.

Signaler un problème · Report an issue : [github.com/Cartoyoyo/BVLIP/issues](https://github.com/Cartoyoyo/BVLIP/issues)
