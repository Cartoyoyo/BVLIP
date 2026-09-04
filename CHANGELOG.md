# Journal des versions

Le format suit [Keep a Changelog](https://keepachangelog.com/fr/1.1.0/), et le
plugin la [gestion sémantique de version](https://semver.org/lang/fr/).

## [0.9.2] - 2026-09-04

### Ajouté

- **Le chevelu amont se charge de proche en proche, par dalles de 10 km.** Le
  WFS ne filtre que par emprise : on ne peut pas lui demander « les tronçons à
  l'amont de celui-ci ». La dalle de l'exutoire est chargée, le graphe remonté
  tant qu'il peut l'être, et là où le parcours bute sur un nœud sans amont
  connu, la dalle qui contient ce nœud est chargée à son tour — vague après
  vague, quatre requêtes de front, les dalles contiguës d'une même rangée
  regroupées en une seule requête.

  Mesuré sur l'Allier à Vichy : 125 dalles, 56 726 tronçons lus pour 38 013
  utiles, en 77 s. Le rectangle englobant en demandait 267 185 et n'aboutissait
  pas.

- **Un bassin hors gabarit est refusé, et le refus est une question.** Au-delà
  de 80 000 tronçons, le calcul s'arrête et montre ce qui a été atteint contre
  ce que coûterait la suite. Le refus est le choix par défaut ; si l'utilisateur
  demande d'aller au bout, jusqu'à 200 000 tronçons, le calcul **repart de ce
  qui est déjà chargé** au lieu de tout refaire.

  Le garde-fou porte sur les tronçons réellement lus et non sur une largeur
  d'emprise : la densité du chevelu va du simple au double d'une région à
  l'autre, et un seuil en kilomètres se trompait dans les deux sens.

- **Seconde recherche de l'exutoire, guidée par l'écoulement.** Quand le bassin
  obtenu ne contient pas le réseau amont qu'il devrait, l'exutoire est cherché
  par l'amont : on s'accroche là où le lit cartographié et celui du MNT
  coïncident franchement, puis on suit les flèches d'écoulement vers l'aval
  jusqu'au point qui passe au plus près du point demandé. Sur le Darot, cette
  approche rend 15,05 km² là où la première en rendait 0,04.

- **Ménage des répertoires de travail** au démarrage de QGIS, pour ce qu'une
  session fermée brutalement a pu oublier. Relevé sur un poste : 116 dossiers
  et 6 Go, jusqu'à saturer le disque — et le symptôme n'était pas « disque
  plein » mais un raster tronqué en plein calcul.

- **La fiche du plugin annonce les seuils**, lus dans le module qui les
  applique plutôt que recopiés.

### Modifié

- **Les canaux ne sont plus remontés.** Un canal n'est pas un chemin de
  drainage : l'eau du Canal de Roanne à Digoin vient de la Loire par
  dérivation. Sur la Besbre à Diou, la remontée empruntait un chemin de
  53 tronçons jusqu'à la Loire et ramenait 47 442 tronçons sur 16 100 km² pour
  un bassin qui en fait un millier. Canaux, aqueducs et bassins portuaires sont
  désormais infranchissables ; buses, écoulements canalisés et retenues restent
  franchissables, car ce sont des cours d'eau ordinaires.

- **L'écoulement est routé en direction simple.** `r.water.outlet` ne lit que la
  carte des directions : en écoulement multiple, elle et l'accumulation cessent
  de mesurer la même chose — à l'embouchure du Gourcet, 5,47 km² annoncés pour
  1,02 ha extraits. En direction simple : 16,31 km² annoncés, 16,307 extraits.
  Le coût est négligeable, de 0,006 à 0,03 % de surface sur quatre bassins de
  33 à 9 008 km².

- **Le recalage de l'exutoire retient le talweg le plus proche qui puisse être
  le bon**, et non le plus drainé : une surface minimale déduite du linéaire
  BD TOPO écarte les ravins voisins, les mailles dont le bassin sort de
  l'emprise sont ignorées, et la recherche s'élargit jusqu'à 400 m tant
  qu'aucun chenal recevable n'est à portée.

- **Le contrôle de contenance exige 60 % du linéaire strictement amont**, le
  tronçon portant l'exutoire étant écarté du décompte : il se prolonge vers
  l'aval et cette partie-là est légitimement dehors.

- **README refondu** : limites connues réorganisées en six volets et complétées
  — domaine d'emploi, taille des bassins, délimitation, précision des mesures,
  données annexes, interface et sorties — plus un résumé des limites en
  espagnol, portugais et allemand.

### Corrigé

- **Les altitudes aberrantes du MNT sont réparées avant tout calcul.** Le
  service rend −97 m à 50 m de maille là où il rend 371 à 536 m à 5 m et à
  25 m : ces valeurs naissent du rééchantillonnage, pas de la donnée source.
  Non filtrées, elles donnaient sur l'Allier à Vichy une dénivelée de 6 535 m
  au lieu de 1 936. La portion fautive est redemandée à une maille plus fine,
  où la donnée est saine, puis ramenée par moyenne de blocs ; à défaut elle est
  comblée par interpolation, jamais laissée en trou — un trou en fond de vallée
  coupe l'écoulement et ampute le bassin, 8 394 km² au lieu de 9 008.

- **Une réponse WFS qui n'est pas du GeoJSON est rejouée sous une autre URL.**
  La Géoplateforme a rendu un relevé de métriques de supervision avec un code
  200 à la place des données ; un cache en amont resservait la mauvaise réponse
  à l'identique. Varier l'URL est le seul moyen d'en sortir.

- **Un bassin tronqué est signalé** plutôt que rendu en silence : chevelu amont
  incomplet, ou contour venant affleurer le bord du MNT.

- Commentaires du module de rapport qui parlaient encore d'une sortie HTML,
  supprimée depuis, et affectation dupliquée dans le lancement du panneau.

## [0.9.1] - 2026-09-03

### Modifie

- **Nouveau logo.** Le dessin montre d'un coup d'oeil ce que fait l'extension :
  la ligne de partage des eaux ferme le bassin, le chevelu s'y ramifie, et le
  point orange marque l'exutoire â€” le point que l'utilisateur clique.

  Il remplace l'icone provisoire, dessinee au trait dans le code. La source est
  desormais un unique `icons/bvlip.svg` ; `tools/make_icons.py` en tire les deux
  PNG dont QGIS et GitHub ont besoin, en 96 px pour la barre d'outils et en
  320 px pour la fenetre A propos et l'en-tete du README. Un seul fichier a
  reprendre quand le dessin change, au lieu de deux images a garder en accord.

## [0.9.0] — 2026-09-03

### Ajouté

- **Les cours d'eau amont portent leur nom.** La couche reprend cinq attributs
  de la BD TOPO, en plus de la longueur déjà présente : le toponyme, le code
  hydrographique, la nature de l'écoulement, sa persistance et sa classe de
  largeur.

  Le toponyme n'est renseigné que sur un peu plus de la moitié du réseau —
  266 tronçons sur 473 pour le bassin de la Besbre, soit 32 cours d'eau
  distincts — mais c'est justement ce qui rend une carte lisible : on y
  reconnaît la Besbre, le Sapey, le Coindre.

- **Les noms s'affichent sur la carte**, en italique le long de la courbe du
  cours d'eau comme sur une carte topographique. Une étiquette horizontale
  posée sur un méandre serait illisible. Les tronçons sans nom restent muets
  plutôt que d'encombrer la carte de vides.

- **Le trait distingue les écoulements permanents des intermittents** : plein
  pour les premiers, tireté pour les seconds. La persistance est renseignée
  sur la totalité des tronçons et change la lecture d'une carte — sur le
  bassin de la Besbre, 302 tronçons intermittents pour 171 permanents. Les
  afficher tous du même trait laisserait croire à un réseau en eau toute
  l'année. Les retenues et conduits, qui ne relèvent ni de l'un ni de
  l'autre, gardent un trait plein plus clair plutôt que de disparaître.

## [0.8.3] — 2026-09-03

### Ajouté

- **README de présentation**, bilingue français-anglais complet puis condensé
  en espagnol, portugais et allemand, avec quatre captures prises dans QGIS :
  le panneau, un bassin de 155 km² sur fond Plan IGN v2, la page A4 du rapport
  et la fenêtre de réglages. Les limites connues y sont écrites plutôt que
  tues — SCAN 25 indisponible, maille élargie sur les grands bassins,
  périmètre dépendant de l'échelle de mesure, troncature des noms de champs à
  l'export Shapefile.
- Contrôle de la **longueur des intitulés** dans `tools/check_fields.py`. La
  colonne des libellés du rapport A4 fait 62 mm à 6,4 points, soit environ
  55 caractères : au-delà, le texte passe à la ligne et recouvre l'intitulé
  suivant. Le défaut ne se voit qu'à la relecture du PDF produit, jamais à
  l'écran.

### Corrigé

- Deux intitulés dépassaient cette largeur et se chevauchaient dans le
  rapport : « Réseau strictement amont contenu dans le bassin (% du
  linéaire) » et « Recalculé à la maille la plus fine sur le bassin
  recadré ». Raccourcis sans perdre leur sens.

### Modifié

- Les captures d'écran sont exclues de l'archive : elles servent au README du
  dépôt, que GitHub rend depuis le dépôt lui-même. Les embarquer ferait passer
  le ZIP de 0,13 à près d'un mégaoctet sans rien apporter à l'exécution.

## [0.8.2] — 2026-09-03

Préparation à la publication sur plugins.qgis.org. Les deux contrôles
bloquants du dépôt passent, et les signalements Qt6 sont traités bien qu'ils
ne bloquent pas : ce sont de vrais plantages sous QGIS 4.

### Modifié

- **Les téléchargements passent par le gestionnaire de réseau de QGIS** plutôt
  que par `urllib`. Trois raisons, dans cet ordre d'importance :

  - il applique les réglages de **proxy et d'authentification du poste**. Avec
    `urllib`, le plugin ne fonctionnait tout simplement pas derrière un proxy
    d'entreprise — ce qui est le cas de beaucoup de collectivités ;
  - il est prévu pour être appelé depuis un fil secondaire, ce qui est
    exactement le cas depuis que le traitement tourne en tâche de fond ;
  - il ferme l'ouverture d'URL arbitraire que Bandit signalait (B310), le
    schéma n'étant plus à la main de l'appelant. C'était le seul contrôle
    bloquant en échec.

  Le délai d'attente est désormais posé sur la requête elle-même : sans lui,
  une requête qui n'aboutit pas laisserait la tâche de fond suspendue
  indéfiniment, et le bouton Annuler ne rendrait jamais la main.

- **43 énumérations Qt sont passées sous leur forme cadrée** :
  `Qt.AlignCenter` devient `Qt.AlignmentFlag.AlignCenter`,
  `QgsWkbTypes.Polygon` devient `QgsWkbTypes.Type.Polygon`, et ainsi de suite
  dans dix fichiers. La forme courte disparaît sous Qt 6 ; la forme cadrée
  fonctionne sur les deux.

### Ajouté

- `tools/build_zip.py` : fabrique l'archive à déposer, avec un dossier racine
  unique et sans les outils de développement. Son périmètre d'exclusion est
  le même que celui passé au contrôle de prépublication, faute de quoi on
  corrigerait des fichiers qui ne partent pas.
- `tools/check_fields.py` rejoint `tools/check_i18n.py` dans la séquence de
  vérification avant publication.

### Vérifié

Contrôle de prépublication sur le dépôt puis sur l'archive elle-même :
Bandit 0 problème sur 28 fichiers, aucun secret détecté, toutes les
énumérations cadrées, aucun binaire, 0,13 Mo. Et le bassin de référence
ressort inchangé après le changement de pile réseau : 1,3417 km²,
Gravelius 1,249, 66 bâtiments, masse d'eau FRGR0208B.

## [0.8.1] — 2026-09-03

### Corrigé

- **Les repères d'exutoire s'accumulaient sur la carte.** Le canevas est
  propriétaire des repères qu'on y pose : quand le panneau disparaît sans
  avoir retiré le sien — rechargement du plugin, fermeture brutale — le point
  rouge reste à l'écran, et le suivant vient s'y ajouter. Douze repères
  relevés sur une session de mise au point, dont huit visibles.

  Le repère est désormais une classe à part entière, ce qui permet de
  retrouver les nôtres parmi les objets du canevas et de les retirer sans
  toucher à ceux des autres extensions. Le ménage se fait à la création de
  l'outil, ce qui couvre aussi les fermetures qui ne préviennent pas, et le
  déchargement du plugin rend explicitement le canevas.

- **Le classeur Excel était coupé à l'impression.** Sa zone d'impression est
  bornée aux colonnes A et B, larges ensemble de 472 pixels, alors que les
  images en font 660 : tout ce qui dépassait la colonne B disparaissait sur la
  page. Le défaut ne se voyait qu'à l'aperçu avant impression, l'affichage à
  l'écran ne connaissant pas cette limite.

  Les deux colonnes couvrent maintenant la largeur imprimable — 696 pixels
  pour 700 disponibles en A4 portrait — et les images tiennent à l'intérieur.
  Vérifié sur les trois onglets.

- **Deux calculs successifs produisaient deux groupes de couches homonymes.**
  Chaque résultat porte maintenant le nom de son cours d'eau et sa surface :
  « BVLIP - Le moulin gonge (2.61 km²) ». Les libellés hérités de la
  BD Carthage sont nettoyés de leurs mentions « (NC) » et ramenés en casse
  ordinaire.

## [0.8.0] — 2026-09-03

Un bassin versant contient les cours d'eau qu'il draine. Le plugin le vérifie
désormais, et ne se trompe plus d'écoulement.

### Corrigé

- **Le recalage de l'exutoire s'appuie sur le chevelu, et non plus sur le
  maximum d'accumulation dans un rayon de quelques mailles.** Le tracé
  cartographique d'un cours d'eau et le talweg calculé à partir du modèle de
  terrain ne se superposent pas : en fond de vallée, l'écart atteint
  couramment plusieurs dizaines de mètres.

  Sur un cas relevé par l'utilisateur, le point cliqué était à 5 m du tracé
  BD TOPO, mais à 50 m du talweg. L'ancien rayon de 4 mailles — 20 m —
  n'atteignait pas le chenal et retenait une maille de versant drainant
  0,06 ha. Le bassin sortait à **600 m² au lieu de 2,61 km²**, et 99,2 % du
  réseau amont se retrouvait en dehors.

  `r.watershed` produit déjà le réseau de chenaux ; il était calculé depuis le
  lot 2 sans jamais servir. On y prend maintenant la maille la plus proche —
  et non la plus drainée, ce qui ferait sauter l'exutoire sur la rivière
  voisine dès qu'elle passe à portée. À égale distance, la maille la plus
  drainée l'emporte : c'est ce qui départage les deux rives d'un même chenal.

- **Le rayon de recalage s'exprime en mètres**, plus en mailles, et vaut 50 m
  par défaut. La distance entre un tracé et un talweg ne dépend pas de la
  finesse du modèle de terrain.

- **Le garde-fou contre les bassins dégénérés était inopérant.** Il refusait
  en dessous de cinq mailles, soit 125 m² : un bassin de 600 m² passait sans
  broncher. Il compare maintenant la surface extraite à celle que le raster
  d'accumulation annonce à l'exutoire — un écart de plus de moitié entre les
  deux signale un point tombé à côté du talweg, quelle que soit la taille du
  bassin.

### Ajouté

- **Contrôle de cohérence sur le réseau amont.** Après délimitation, la part
  du linéaire strictement amont contenue dans le polygone est mesurée. En
  dessous de 80 %, le traitement s'arrête en disant pourquoi : ce n'est pas le
  bassin de ce cours d'eau, l'exutoire est tombé sur un autre écoulement.

  Le tronçon qui porte l'exutoire est écarté du calcul : il se prolonge vers
  l'aval au-delà du point de sortie, et cette partie est légitimement dehors.
  La compter brouillait le signal — 78 % au lieu des 100 % que donnent les
  tronçons strictement amont.

- Le champ « Réseau strictement amont contenu dans le bassin (% du linéaire) »
  figure dans la table et dans le rapport : le lecteur peut en juger lui-même.
- Le journal annonce la surface drainée par l'exutoire retenu, en kilomètres
  carrés : un exutoire qui ne draine que quelques ares se repère aussitôt.

### Vérifié

| Cas | Avant | Après | Réseau amont contenu |
|---|---|---|---|
| Point signalé | 0,0006 km² | **2,6119 km²** | 0,8 % → **100 %** |
| Bassin de référence | 1,3417 km² | **1,3417 km²** | tête de bassin |
| Besbre | 154,982 km² | 154,968 km² | **100 %** |

Le bassin de référence, validé à la main, ressort au dix-millième près.

## [0.7.2] — 2026-09-03

### Modifié

- **Les étapes de calcul reviennent dans le panneau.** Elles se décident d'un
  bassin à l'autre — on calcule l'occupation du sol pour celui-ci mais pas
  pour celui-là — alors que le rayon d'accrochage se règle une fois. Les
  premières restent donc sous la main, le second reste au menu. Les cases
  s'enregistrent dès qu'on les coche : il n'y a qu'un seul endroit où l'état
  est conservé, et le traitement le relit au lancement.
- **Tous les boutons ont la même hauteur**, 30 pixels, et « Délimiter » et
  « Annuler » exactement la même largeur. Le rembourrage propre à chaque style
  disparaît au profit d'une hauteur unique.

  La paire est posée dans une grille à deux colonnes de même poids, et non
  dans une boîte horizontale : celle-ci ne répartit que l'espace
  *supplémentaire* et laissait au bouton au texte le plus long une largeur
  plus grande — 151 contre 92 pixels.

- La fenêtre de réglages ne porte plus que les deux accrochages de l'exutoire,
  pour qu'il n'existe pas deux endroits où cocher la même chose.

### Vérifié

Hauteurs mesurées après affichage : 30 pixels pour les quatre boutons,
192 pixels chacun pour la paire. Cases décochées puis relues, traitement qui
saute effectivement l'étape écartée, surface inchangée à 1,3417 km².

## [0.7.1] — 2026-09-03

Le panneau se resserre sur le geste courant.

### Modifié

- **Le panneau ne porte plus que ce qui sert à chaque usage** : choisir un
  exutoire, lancer, annuler, produire le rapport, suivre l'avancement. Sa
  hauteur utile tombe à 396 pixels. Un panneau qui tient dans un coin d'écran
  reste utilisable à côté d'une carte ; un panneau qui affiche tous les
  réglages ne l'est plus.
- **Le menu de l'extension accueille le reste.** Extensions → BVLIP donne
  accès au panneau, aux réglages, au choix de la langue et à la fiche du
  plugin — tout ce qu'on règle une fois et qu'on ne retouche plus.
- **Les réglages sont conservés d'une session à l'autre**, dans les
  préférences de QGIS : rayon d'accrochage au réseau, recalage sur le talweg,
  étapes de calcul facultatives, langue. Ils ne sont plus à reposer à chaque
  ouverture, et une modification prend effet au lancement suivant sans qu'il
  faille rouvrir le panneau.

### Ajouté

- `gui/settings.py` et `gui/settings_dialog.py` : lecture, écriture et
  fenêtre de réglages, avec un bouton de retour aux valeurs par défaut.
- Choix de la langue dans un sous-menu à cases exclusives, appliqué
  immédiatement au menu comme au panneau, et retenu pour les sessions
  suivantes. Sans choix explicite, la langue de QGIS continue de servir.

### Vérifié

Réglages enregistrés puis relus, bascule français/anglais sur le menu et le
panneau, et calcul complet utilisant le rayon d'accrochage venu des
préférences : 1,3417 km², Gravelius 1,249, plus long cheminement 2,359 km —
inchangés.

## [0.7.0] — 2026-09-03

Le calcul ne fige plus QGIS.

### Modifié

- **La délimitation part dans une tâche de fond**, le mécanisme de tâches de
  QGIS. Le panneau émet la demande et rend la main aussitôt : mesuré à
  **0,008 s** au lieu des 57 s que durait l'appel bloquant sur un bassin de
  155 km². Pendant le calcul, la carte reste navigable et les autres outils
  utilisables.

  Le `processEvents` qui parsemait le code ne suffisait pas : il ne rend la
  main à Qt qu'*entre* deux étapes, alors que le temps se passe *dans* des
  appels bloquants. Mesure par étape sur un petit bassin : 9,8 s de
  téléchargement de l'occupation du sol, 6,8 s de GRASS, 4,1 s de WFS, 2,9 s
  de WMS, et seulement 0,3 s de calcul numérique — soit 26 s de sablier sur
  27.

  Quand le panneau a été écrit, un traitement durait une trentaine de
  secondes et le fil principal se défendait. À deux ou trois minutes, ce
  raisonnement ne tenait plus.

- **Les couches ne sont fabriquées qu'au retour de la tâche**, donc dans le
  fil principal. Le fil de fond produit des données brutes et ne touche
  jamais au projet : construire une couche puis l'ajouter au projet depuis un
  fil secondaire est le moyen le plus sûr de faire tomber QGIS.

### Ajouté

- **Un bouton Annuler**, qui n'avait pas de sens tant que l'interface était
  gelée. La chaîne acceptait déjà un signal d'interruption depuis le lot 4,
  faute de pouvoir cliquer. L'annulation prend effet dès que l'opération en
  cours se termine — mesuré à 10 s pendant un téléchargement de MNT, qui ne
  peut pas être coupé en son milieu.
- Fermer le panneau pendant un calcul l'annule proprement, au lieu de
  refuser la fermeture.
- `tools/check_fields.py` : contrôle de la table des champs avant
  publication. Il vérifie que les intitulés portent l'unité annoncée par le
  suffixe du nom, et surtout que **les dix premiers caractères des noms sont
  uniques** — c'est la limite du format Shapefile, et deux champs qui s'y
  télescopent se font renommer d'office à l'export, l'un des deux devenant
  indéchiffrable.

### Corrigé

- `pente_moy_deg` et `pente_moy_pct` se réduisaient tous deux à `pente_moy_`
  sur les dix premiers caractères : à l'export Shapefile, l'un des deux
  serait devenu `pente_mo_1`. Ils deviennent `pente_deg`, `pente_pct`, et
  `pente_med_deg` devient `pente_med`. Sur 61 champs, 34 restent tronqués à
  l'export mais tous demeurent distincts et lisibles.

### Vérifié

- Petit bassin : 1,3417 km², Gravelius 1,249 — identiques au calcul
  synchrone. 478 tours de boucle d'événements traités pendant les 25 s.
- Bassin de 155 km² : 154,982 km², Gravelius 1,781, plus long cheminement
  35,526 km, 6 009 bâtiments — identiques. 1 084 tours d'interface pendant
  les 57 s.
- Annulation : statut mis à jour, boutons rétablis, aucune couche ajoutée,
  gestionnaire de tâches vide.

## [0.6.1] — 2026-09-03

Économie de mémoire, sur trois fronts. Le traitement complet d'un bassin de
155 km² atteint désormais un pic de **173 Mo**, mesuré au fil de l'exécution.

### Ajouté

- **Option « recalculer à la maille la plus fine »**, décochée par défaut.
  Elle recadre sur le bassin obtenu à la première passe, avec 50 m de marge de
  part et d'autre, et consacre la mémoire ainsi libérée à une seconde passe
  plus fine. Sur un bassin de 155 km², elle ramène la maille de 10 m à 5 m sur
  un poste qui n'avait pas la mémoire de le faire d'emblée.

  Le résultat reste exact : le bassin fin est contenu dans le bassin grossier
  à une maille près, donc les directions d'écoulement calculées sur l'emprise
  recadrée sont identiques à l'intérieur. Un contrôle vérifie que le contour
  n'affleure pas le bord du recadrage, et élargit la marge si c'est le cas.

  Ce qu'elle apporte, mesuré : la surface bouge de +0,02 %, le plus long
  cheminement et la pente de 1 à 2 %, pour un temps de calcul doublé. D'où le
  choix de la laisser décochée, et l'infobulle qui le dit franchement.

- Deux champs de traçabilité, dans la table et dans le rapport : « Maille
  élargie faute de mémoire » et « Recalculé à la maille la plus fine sur le
  bassin recadré ». Le lecteur sait ainsi si périmètre, Gravelius et pente
  portent quelques pour cent d'incertitude supplémentaire.

### Modifié

- **Les caractéristiques ne sont plus calculées que sur le rectangle du
  bassin.** L'emprise de calcul couvre le réseau amont élargi de deux
  kilomètres, souvent bien plus vaste : sur le bassin de référence, la fenêtre
  utile fait 299 × 314 mailles au lieu de 921 × 844, soit **huit fois moins**
  à lire. Le pic mesuré du calcul des caractéristiques est de 38 octets par
  maille de fenêtre — c'est ce chiffre, et non l'emprise entière, qui commande
  la mémoire.
- **Le raster de pente est écrit sur disque** au lieu d'être gardé en mémoire.
  Sur une grande emprise, un raster complet de plus en mémoire était
  exactement ce qu'on cherchait à éviter ; seule la fenêtre du bassin est
  relue.
- **L'occupation du sol est cumulée page par page.** Les entités sont
  traitées puis oubliées au fil de la pagination, au lieu d'être toutes
  gardées pour n'en tirer qu'une somme. Sur le bassin d'essai, cela concerne
  6 009 bâtiments ; sur un bassin plus vaste, le seul texte GeoJSON de la
  couche du bâti se compterait en centaines de mégaoctets.

### Vérifié

Non-régression sur le bassin de référence validé à la main : surface
1,3417 km², Gravelius 1,249, plus long cheminement 2,359 km, 66 bâtiments,
50,1 % de conifères. Toutes les valeurs sont identiques au chiffre près.

## [0.6.0] — 2026-09-03

Les grands bassins passent. Jusqu'ici, au-delà de quelques centaines de
kilomètres carrés, QGIS s'arrêtait net — sans message, sans trace dans le
journal, puisqu'un manque de mémoire ne laisse rien derrière lui.

### Ajouté

- **La maille du MNT s'ajuste à l'emprise et à la mémoire disponible.** Le
  plafond ne pouvait pas être une constante : la même emprise passe sans
  difficulté sur un poste à 32 Go et fait tomber QGIS sur un poste à 8 Go dont
  il ne reste que deux libres. Il est donc déduit de la mémoire réellement
  libre au moment du calcul (35 % de celle-ci, à raison de 40 octets par
  maille pour toute la chaîne), puis la maille la plus fine qui tienne sous ce
  plafond est retenue parmi 5, 10, 25 et 50 m.
- Le choix est annoncé dans le journal, avec sa raison : « Emprise de 471 km²
  : maille portée à 10 m pour tenir dans la mémoire disponible (4,7 Mpx au
  lieu de 18,8) ».
- Le refus, quand même la maille la plus grossière ne suffit pas, dit quoi
  faire plutôt que de constater : fermer des applications, ou remonter
  l'exutoire.
- L'algorithme Processing accepte `0` comme résolution, ce qui déclenche le
  même ajustement ; une valeur explicite reste respectée.

### Corrigé

- **Le calcul du plus long cheminement consommait deux fois trop de mémoire.**
  Les indices passent en entiers 32 bits et les distances en flottants simple
  précision — un indice tient largement sur 32 bits, et une distance en mètres
  reste juste au centimètre près jusqu'à plusieurs centaines de kilomètres.
  Le tableau des indices sert directement de tableau des mailles aval, et les
  opérations du saut de pointeur se font dans deux tampons alloués une fois
  pour toutes : écrites naturellement, elles créaient trois tableaux neufs à
  chaque tour, soit plusieurs centaines de mégaoctets alloués et rendus une
  vingtaine de fois. Le masquage final ne passe plus par `np.where`, qui
  produisait un tableau neuf en double précision.

### Mesuré

Même exutoire sur la Besbre, calculé à trois mailles. La maille plus large ne
coûte presque rien sur les grandeurs de surface, et quelques pour cent sur
celles qui dérivent du contour ou de la pente :

| Grandeur | 5 m | 10 m | 25 m |
|---|---|---|---|
| Surface (km²) | 146,331 | −0,0 % | −0,0 % |
| Altitudes mini et maxi | référence | −0,0 % | −0,1 % |
| Plus long cheminement | 33,547 km | −2,3 % | −5,0 % |
| Périmètre et Gravelius | 1,704 | −2,4 % | −6,2 % |
| Pente moyenne | 22,45 % | −1,5 % | −5,7 % |
| Durée du calcul | 192 s | −73 % | −91 % |

## [0.5.4] — 2026-09-02

### Corrigé

- **Le panneau plantait si son propriétaire disparaissait pendant un calcul.**
  `processEvents`, qui garde l'interface réactive pendant le traitement, rend
  la main à Qt : le panneau peut alors être fermé, ou le plugin rechargé,
  alors que la chaîne tourne encore. L'objet Python survit à son homologue
  C++ et la moindre mise à jour lève une `RuntimeError` — barre de
  progression, puis journal, puis boutons, chaque bloc `except` échouant à son
  tour. Toute écriture dans l'interface vérifie désormais que le widget existe
  encore, la fermeture du panneau attend la fin du traitement, et un second
  lancement est refusé tant que le premier n'est pas terminé.

- **Les appels dépréciés sont remplacés**, ils remplissaient le journal à
  chaque exécution et auraient été relevés à la publication :
  - `QgsField(nom, QVariant.Type, len=, prec=)` devient
    `QgsField(nom, QMetaType.Type, "", longueur, précision)`, avec repli sur
    l'ancienne forme là où `QMetaType.Type` n'est pas exposé ;
  - `QgsLayoutItemLabel.setFont` et `setFontColor`, ainsi que
    `QgsLayoutItemScaleBar.setFont`, passent par `QgsTextFormat` ;
  - `QgsRectangle.setMinimal` disparaît : l'enveloppe du réseau amont suit ses
    extrêmes à la main, sans dépendre d'une API dont la construction d'un
    rectangle nul a changé selon les versions.

  Vérifié sur QGIS 3.44.13 : plus aucun avertissement de dépréciation sur un
  cycle complet, délimitation et rapport compris.

## [0.5.3] — 2026-09-02

### Corrigé

- **Le classeur débordait de la feuille A4.** Les graphiques étaient posés en
  colonnes E a I, à droite du tableau comme sur la page A4 : la largeur du
  classeur atteignait le double d'une feuille, et les intitulés longs se
  retrouvaient coupés à l'impression. L'image du bassin, à 883 pixels,
  dépassait elle aussi la zone imprimable.
- Les graphiques passent **sous** le tableau, la carte est ramenée à 660
  pixels et les graphiques à 560, sous la limite de 700 pixels que représente
  une zone imprimable A4 portrait de 186 mm à 96 points par pouce.
- Les trois onglets déclarent leur mise en page : **A4 portrait, ajustement à
  la largeur d'une page**, hauteur libre, marges de 12 mm et zone d'impression
  bornée. Le classeur s'imprime tel quel, sans réglage préalable.

## [0.5.2] — 2026-09-02

### Ajouté

- Une fois le rapport écrit, le panneau propose d'ouvrir le dossier qui le
  contient, en rappelant les fichiers produits. Le rapport part rarement seul :
  il y a le PDF et le classeur, souvent à transmettre dans la foulée.
- L'ouverture passe par `QDesktopServices`, qui délègue au gestionnaire de
  fichiers du système : aucune commande shell à construire, donc rien à
  échapper et rien à adapter d'un système à l'autre. Un échec d'ouverture est
  signalé dans le journal plutôt que passé sous silence.

## [0.5.1] — 2026-09-02

### Modifié

- **Le classeur Excel remplace la version HTML.** Même organisation que la
  page A4 : le titre, l'image du bassin, puis les sections de caractéristiques
  à gauche et les graphiques à droite. Deux onglets s'y ajoutent — le détail
  Corine Land Cover de niveau 3, que la page A4 ne peut pas contenir, et le
  relevé des cours d'eau amont avec la longueur de chaque tronçon.
- Les valeurs y sont écrites **comme des nombres**, pas comme du texte mis en
  forme : une surface recopiée dans une formule s'additionne sans
  retraitement. La présentation passe par les formats de nombre, calés sur la
  précision déjà déclarée pour chaque champ — une part en pourcentage garde
  une décimale, un indice de compacité trois, un nombre de bâtiments aucune.

## [0.5.0] — 2026-09-02

Lot 5 : le rapport. Et un panneau qui n'écrit plus rien sans qu'on le demande.

### Modifié

- **Plus de dossier de sortie.** La délimitation produit des couches en
  mémoire, chargées dans un groupe du projet. Rien n'atterrit sur disque : un
  essai qui ne convient pas se ferme sans laisser de fichier. Ce qui mérite
  d'être conservé s'exporte par le menu habituel de QGIS.
- **La case « produire le rapport » devient un bouton.** Le rapport est une
  demande explicite, pas un effet de bord du calcul : il ne part jamais tout
  seul, et c'est à ce moment seulement que l'emplacement du fichier est
  demandé. Le bouton reste inactif tant qu'aucun bassin n'a été délimité.
- **Tous les intitulés portent leur unité.** « Surface (km²) », « Indice de
  pente global Ig (m/km) », « Temps de concentration — Giandotti (heures) »,
  « Distance du point cliqué au réseau BD TOPO (m) »… Ces intitulés sont
  définis au même endroit que les champs, posés en alias sur les couches, et
  repris tels quels par le rapport : aucune valeur ne peut être lue sans
  savoir en quoi elle est exprimée.
- La couche « Réseau amont » devient **« Cours d'eau amont »**, et chaque
  tronçon porte sa longueur en mètres.
- Les quatre états de l'exutoire sont désormais symbolisés distinctement —
  point cliqué en gris, accroché en orange, recalé en étoile rouge, point le
  plus éloigné en triangle violet.

### Ajouté

- `report/charts.py` : courbe hypsométrique, camembert d'occupation du sol et
  comparaison des temps de concentration, en matplotlib. Son absence ne fait
  pas échouer le rapport, elle le prive seulement de ses graphiques.
- `report/layout.py` : mise en page A4 montée par le code — carte masquée en
  moitié haute, tableaux et graphiques en moitié basse. Le gabarit n'est pas
  un fichier `.qpt` : il se construit à partir des sections déclarées dans
  `core/results.py`, si bien qu'ajouter une caractéristique suffit à la voir
  apparaître, sans maintenir un gabarit en parallèle du code.
- `report/html.py` : version HTML autonome, images en base64. Remplacée dès
  la 0.5.1 par le classeur Excel.
- `report/builder.py` : enchaînement graphiques → mise en page → PDF → HTML.
- Le fond de plan est le **Plan IGN v2**, seule carte topographique servie
  librement par la Géoplateforme.

### Corrigé

- **`QgsLayoutItemMap.setExtent` redimensionne l'élément** pour respecter le
  rapport de forme de l'emprise : le cadre carte débordait sur toute la page
  et passait derrière les tableaux. `zoomToExtent` conserve la taille posée.
- **Le fond de plan ne s'affichait pas.** Toutes les couches XYZ rendent du
  vide sur ce poste — OpenStreetMap compris, vérifié en témoin — alors que le
  fournisseur WMTS aboutit. Le fond passe donc par WMTS, qui est aussi le mode
  d'accès officiel du service.
- Les couleurs du camembert étaient appariées sur le libellé des classes, or
  une différence d'accentuation entre deux modules suffisait à toutes les
  faire retomber sur le gris par défaut. L'appariement se fait sur le code.
- Le toponyme BD TOPO empile parfois plusieurs dénominations séparées par une
  barre oblique, souvent la même répétée : le titre ne garde que la première.
- `QgsLayoutExporter.exportToImage` n'exporte que des pages entières ; le
  rendu du seul cadre carte passe par `renderRegionToImage`.

## [0.4.0] — 2026-09-02

Lot 4 : les deux points d'entrée. Le panneau et la boîte à outils appellent
désormais la même chaîne de traitement.

### Ajouté

- `core/pipeline.py` : orchestration unique du traitement, du point cliqué au
  bassin caractérisé. C'est le seul endroit où l'ordre des étapes est écrit,
  de sorte que le panneau et l'algorithme ne peuvent pas diverger.
- Algorithme Processing `bvlip:delimiterbassinversant`, groupe « Hydrologie » :
  traite une couche de points entière, reprojette les exutoires en Lambert 93,
  et produit deux couches — les bassins et les exutoires sous leurs quatre
  états. Un point qui échoue n'interrompt pas le lot.
- Fournisseur Processing enregistré au chargement du plugin, avec import
  différé : une erreur dans le code des algorithmes n'empêche pas le panneau
  de se charger.
- Le panneau exécute la chaîne réelle : barre de progression par étape,
  journal détaillé, résumé final, écriture du GeoPackage et chargement des
  couches dans le projet.

### Corrigé

- **Les réponses WFS étaient tronquées sans aucun signe.** Le service plafonne
  le nombre d'entités renvoyées et signale la troncature en renvoyant
  exactement le nombre demandé — une réponse valide, simplement incomplète.
  Sur un exutoire de la Besbre, les 5 000 tronçons rapatriés ne contenaient
  pas celui qui longeait le point, et l'accrochage échouait sur un exutoire
  pourtant au bord de l'eau. Toutes les requêtes WFS sont désormais paginées ;
  le même point charge 7 921 tronçons et aboutit. Le calcul du bâti était
  exposé au même défaut et sous-estimait silencieusement les grands bassins.
- **Le plus long cheminement hydraulique était trop lent pour les grands
  bassins.** Le parcours maille par maille demandait environ 150 s sur un
  bassin de 5,85 millions de mailles. Il est remplacé par un saut de pointeur
  vectorisé, qui double la portée à chaque tour : 5,2 s pour un résultat
  identique au millimètre.

### Vérifié

- Bassin de la Besbre à l'amont de Châtel-Montagne : 146,33 km², réseau amont
  de 197 km sur 439 tronçons, MNT de 16,4 Mpx téléchargé en quatre dalles,
  plus long cheminement 33,55 km, altitudes de 397 à 1 287 m. L'élargissement
  itératif de l'emprise s'est déclenché une fois, comme prévu.

## [0.3.0] — 2026-09-02

Lot 3 : caractéristiques du bassin. La table passe de 18 à 57 champs.

### Ajouté

- `core/metrics.py` : indice de compacité de Gravelius et rectangle
  équivalent, altitudes et courbe hypsométrique, pentes moyenne et médiane,
  indice de pente global et dénivelée spécifique, longueur du plus long
  cheminement hydraulique, densité de drainage, et temps de concentration
  selon Kirpich, Giandotti, Passini et Ventura.
- `core/waterbody.py` : rattachement de l'exutoire à sa masse d'eau DCE, par
  le bassin versant spécifique du référentiel Sandre.
- `core/landcover.py` : répartition Corine Land Cover 2018 (niveaux 3 et 1)
  et emprise bâtie mesurée sur la BD TOPO.
- Le rayon de recalage sur le talweg est réglable depuis le panneau, en
  nombre de mailles ; 0 désactive le recalage.
- Trois champs de traçabilité : périmètre avant simplification, tolérance
  appliquée, et point le plus éloigné hydrologiquement, écrit dans la couche
  des exutoires.

### Corrigé

- Les quantiles hypsométriques étaient inversés : H5 % est l'altitude que
  dépasse 5 % de la surface, donc le 95e centile des altitudes et non le 5e.
  La dénivelée utile ressortait négative, entraînant un indice de pente global
  et une dénivelée spécifique négatifs.
- Le contour issu de la rasterisation est désormais simplifié à deux mailles.
  L'escalier de pixels allongeait le périmètre de 30 % — 7 170 m au lieu de
  5 168 m sur le bassin d'essai — et surestimait d'autant l'indice de
  Gravelius, à 1,73 au lieu de 1,25, alors que la surface varie de moins de
  0,05 %.
- L'écriture d'un GeoPackage déjà présent échouait : OGR refuse d'écraser un
  fichier existant malgré `CreateOrOverwriteFile`. Le fichier et son journal
  sont supprimés au préalable, avec un message explicite s'ils sont
  verrouillés par QGIS.

### Choix documentés

- L'enrichissement par la couche des masses d'eau rivière (type, longueur,
  bassin DCE, Strahler) est désactivé par défaut : le service Sandre
  n'applique aucun filtre attributaire côté serveur, ni par CQL ni par
  requête SQL, si bien qu'il faut rapatrier les 9 746 masses d'eau
  nationales — 44 s — pour n'en retenir qu'une.
- La couche des bassins versants de masses d'eau de la Géoplateforme n'est
  pas utilisée : elle ne compte que 1 115 entités et ne couvre pas le
  secteur d'essai. Le référentiel Sandre la remplace.
- Corine Land Cover et la BD TOPO ne sont pas additionnées. CLC donne la
  répartition, qui somme à 100 % ; la BD TOPO donne le bâti, mesuré
  indépendamment. Sur le bassin d'essai, CLC annonce 0 % d'artificialisé
  alors que la BD TOPO y compte 66 bâtiments et 8 zones d'habitation
  couvrant 4,2 % de la surface : l'unité minimale de collecte de 25 ha de
  CLC efface les hameaux.

## [0.2.0] — 2026-09-02

Lot 2 : cœur de calcul. La chaîne tourne de bout en bout, hors interface.

### Ajouté

- `core/geoservices.py` : accès WFS et WMS de la Géoplateforme IGN, sans clé,
  avec réessais et contrôle de la taille des réponses.
- `core/network.py` : construction du graphe des tronçons BD TOPO, accrochage
  de l'exutoire, remontée du réseau amont, et calcul de l'emprise de travail
  par élargissement itératif si le réseau sort de la zone interrogée.
- `core/dem.py` : téléchargement du RGE ALTI en BIL 32 bits, découpé en dalles
  sous la limite de 5010 px du service, assemblé en GeoTIFF Lambert 93.
- `core/delineation.py` : `r.watershed` puis `r.water.outlet`, avec recalage de
  l'exutoire sur la maille de plus forte accumulation avant extraction.
- `core/results.py` : écriture d'un GeoPackage à trois couches (bassin,
  exutoire, réseau amont) et mise en forme dans le projet QGIS.

### Corrigé

- La région GRASS n'est plus imposée : l'ordre de coordonnées attendu par
  `GRASS_REGION_PARAMETER` produisait une région d'un million de lignes et un
  échec d'allocation mémoire, sans message exploitable. Le raster d'entrée
  définit déjà l'emprise voulue.
- Les indicateurs booléens de `r.watershed` ne sont plus transmis : passés à
  `False`, ils faisaient échouer l'algorithme silencieusement.

## [0.1.0] — 2026-09-02

Lot 1 : squelette du plugin. Rien n'est encore calculé, mais tout se charge.

### Ajouté

- Chargement du plugin dans QGIS 3.40 : icône de barre d'outils et entrée de
  menu, avec bascule d'affichage du panneau.
- Panneau latéral ancrable : choix de l'exutoire, rayon d'accrochage, options
  de traitement, dossier de sortie, barre de progression, journal.
- Outil de carte pour désigner l'exutoire, avec repère visuel et reprojection
  immédiate en Lambert 93.
- Interface multilingue FR / EN / ES / PT / DE, commutable à la volée, langue
  initiale héritée de QGIS.
- Dialogue « À propos » : version lue dans `metadata.txt`, licence, lien auteur,
  signalement de bug, crédits des producteurs de données.
- Génération des icônes par script (`tools/make_icons.py`).
