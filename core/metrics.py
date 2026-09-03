# -*- coding: utf-8 -*-
"""Caracteristiques morphometriques du bassin versant.

Tout se calcule a partir de trois rasters deja produits par la delimitation
(MNT, masque du bassin, directions d'ecoulement) et du polygone : aucun
telechargement supplementaire n'est necessaire.

Conventions d'unites, pour eviter les confusions classiques :
    surfaces    en m2 en interne, exposees aussi en km2
    longueurs   en m en interne, exposees aussi en km
    pentes      en m/m en interne, exposees aussi en %
    temps       en heures
"""

import math
import os
import tempfile

import numpy as np
from osgeo import gdal

# Directions d'ecoulement de r.watershed : 1 a 8 dans le sens trigonometrique
# a partir du nord-est. Les valeurs negatives designent les mailles qui
# s'ecoulent hors de la region, 0 une cuvette fermee.
FLOW_OFFSETS = {
    1: (-1, 1), 2: (-1, 0), 3: (-1, -1), 4: (0, -1),
    5: (1, -1), 6: (1, 0), 7: (1, 1), 8: (0, 1),
}

# Quantiles retenus pour la courbe hypsometrique.
HYPSO_QUANTILES = (0, 5, 10, 25, 50, 75, 90, 95, 100)


class MetricsError(RuntimeError):
    """Les caracteristiques n'ont pas pu etre calculees."""


def _read(path, band=1, window=None):
    """Lit un raster, ou seulement la fenetre demandee.

    window vaut (colonne, ligne, largeur, hauteur). Restreindre la lecture au
    rectangle qui contient le bassin est le principal levier d'economie de
    memoire : l'emprise de calcul est celle du reseau amont elargie de deux
    kilometres, souvent trois a six fois plus vaste que le bassin lui-meme.
    Tout ce qui est en dehors ne sert a rien, puisque seules les mailles du
    bassin sont retenues ensuite.
    """
    dataset = gdal.Open(path)
    if dataset is None:
        raise MetricsError("Raster illisible : {0}".format(path))
    raster = dataset.GetRasterBand(band)
    if window is None:
        array = raster.ReadAsArray()
    else:
        array = raster.ReadAsArray(*window)
    nodata = raster.GetNoDataValue()
    transform = dataset.GetGeoTransform()
    dataset = None
    if array is None:
        raise MetricsError("Lecture impossible de {0}".format(path))
    return array, nodata, transform


def basin_window(mask, pad=1):
    """Rectangle englobant les mailles du bassin, elargi de pad mailles.

    Renvoie (fenetre, masque recadre) ou la fenetre est au format attendu par
    GDAL : (colonne, ligne, largeur, hauteur).
    """
    rows, cols = np.nonzero(mask)
    if rows.size == 0:
        raise MetricsError("Masque du bassin vide.")
    row_min = max(0, int(rows.min()) - pad)
    row_max = min(mask.shape[0], int(rows.max()) + 1 + pad)
    col_min = max(0, int(cols.min()) - pad)
    col_max = min(mask.shape[1], int(cols.max()) + 1 + pad)
    window = (col_min, row_min, col_max - col_min, row_max - row_min)
    return window, mask[row_min:row_max, col_min:col_max].copy()


# ------------------------------------------------------- Forme du contour

def shape_metrics(area, perimeter):
    """Indice de Gravelius et rectangle equivalent.

    Le rectangle equivalent est le rectangle de meme surface et meme
    perimetre que le bassin : sa longueur sert de reference pour l'indice de
    pente global. Il n'existe que si l'indice de compacite depasse 1,128,
    valeur du disque ; en dessous, le bassin est plus compact qu'un cercle,
    ce qui traduit un contour trop lisse et non un cas physique.
    """
    if area <= 0:
        raise MetricsError("Surface nulle.")
    gravelius = 0.28 * perimeter / math.sqrt(area)

    ratio = 1.128 / gravelius
    if ratio >= 1.0:
        length = math.sqrt(area)
        width = length
    else:
        root = math.sqrt(1.0 - ratio * ratio)
        length = (gravelius * math.sqrt(area) / 1.128) * (1.0 + root)
        width = area / length
    return {
        "gravelius": gravelius,
        "rect_longueur_m": length,
        "rect_largeur_m": width,
    }


# ----------------------------------------------------------- Altimetrie

def elevation_metrics(dem_path, mask, window=None):
    """Statistiques d'altitude et courbe hypsometrique sur les mailles du bassin."""
    elevations, nodata, _ = _read(dem_path, window=window)
    values = elevations[mask]
    del elevations
    if nodata is not None:
        values = values[values != nodata]
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise MetricsError("Aucune altitude valide dans le bassin.")

    quantiles = np.percentile(values, HYPSO_QUANTILES)
    curve = [
        {"part_surface_pct": 100 - q, "altitude_m": float(z)}
        for q, z in zip(HYPSO_QUANTILES, quantiles)
    ]

    # En hypsometrie, H5 % designe l'altitude que depasse 5 % de la surface :
    # c'est donc le 95e centile des altitudes, et non le 5e. L'inverse pour
    # H95 %. Confondre les deux donne une denivelee utile negative.
    z_hypso_5 = float(np.percentile(values, 95))
    z_hypso_95 = float(np.percentile(values, 5))
    return {
        "z_min_m": float(values.min()),
        "z_max_m": float(values.max()),
        "z_moyen_m": float(values.mean()),
        "z_median_m": float(np.median(values)),
        "z_hypso_5_m": z_hypso_5,
        "z_hypso_95_m": z_hypso_95,
        "denivelee_m": float(values.max() - values.min()),
        "hypsometrie": curve,
    }


def slope_metrics(dem_path, mask, window=None):
    """Pente du terrain, en moyenne et en mediane, calculee par gdaldem.

    L'algorithme de Horn est utilise (defaut de gdaldem) : il moyenne les huit
    voisins, ce qui limite le bruit du MNT sur les versants reguliers.

    Le raster de pente est ecrit sur disque plutot que garde en memoire : sur
    une grande emprise, un raster complet de plus en memoire est exactement ce
    qu'on cherche a eviter. Seule la fenetre du bassin est relue ensuite.
    """
    handle, temporary = tempfile.mkstemp(suffix=".tif", prefix="bvlip_pente_")
    os.close(handle)
    try:
        slope_ds = gdal.DEMProcessing(
            temporary, dem_path, "slope", format="GTiff",
            slopeFormat="degree", computeEdges=True,
            creationOptions=["COMPRESS=DEFLATE", "TILED=YES"],
        )
        if slope_ds is None:
            raise MetricsError("Calcul de pente impossible.")
        slope_ds = None
        array, nodata, _ = _read(temporary, window=window)
    finally:
        try:
            os.remove(temporary)
        except OSError:
            pass

    values = array[mask]
    del array
    if nodata is not None:
        values = values[values != nodata]
    values = values[np.isfinite(values)]
    if values.size == 0:
        raise MetricsError("Aucune pente valide dans le bassin.")

    mean_deg = float(values.mean())
    return {
        "pente_moyenne_deg": mean_deg,
        "pente_moyenne_pct": math.tan(math.radians(mean_deg)) * 100.0,
        "pente_moyenne_mm": math.tan(math.radians(mean_deg)),
        "pente_mediane_deg": float(np.median(values)),
        "pente_max_deg": float(values.max()),
    }


# ------------------------------------------- Plus long cheminement hydraulique

def longest_flow_path(drainage_path, mask, outlet_rowcol, cellsize,
                      window=None):
    """Longueur du plus long cheminement hydraulique et maille la plus eloignee.

    La distance d'une maille a l'exutoire se calcule par saut de pointeur : on
    part de la distance a la maille aval immediate, puis on compose
    repetitivement la relation avec elle-meme. A chaque tour, la portee double,
    si bien qu'une vingtaine de tours suffit pour un bassin de plusieurs
    millions de mailles.

    Le parcours maille par maille, plus direct a lire, devenait inutilisable
    des quelques millions de mailles : plusieurs minutes la ou cette version
    prend moins d'une seconde, pour un resultat identique.

    Renvoie (longueur en m, (ligne, colonne) de la maille la plus eloignee).
    """
    directions, _, _ = _read(drainage_path, window=window)
    rows, cols = directions.shape
    outlet_row, outlet_col = outlet_rowcol
    if not (0 <= outlet_row < rows and 0 <= outlet_col < cols):
        raise MetricsError("Exutoire hors du raster d'ecoulement.")

    size = rows * cols
    if size > np.iinfo(np.int32).max:
        raise MetricsError(
            "Raster trop grand pour le calcul du cheminement : "
            "{0:.0f} millions de mailles.".format(size / 1e6)
        )

    # Entiers 32 bits et flottants simple precision : deux fois moins de
    # memoire qu'en 64 bits, pour un resultat identique. Un indice tient
    # largement sur 32 bits, et une distance en metres reste juste au
    # centimetre pres jusqu'a plusieurs centaines de kilometres. Sur un poste
    # ou il ne reste qu'un ou deux gigaoctets libres, cet ecart decide si le
    # calcul aboutit ou si QGIS s'arrete.
    #
    # Le tableau des indices sert directement de tableau des mailles aval :
    # chaque maille y pointe d'abord sur elle-meme, ce qui donne des racines
    # stables aux mailles hors bassin, aux cuvettes et a l'exutoire.
    down = np.arange(size, dtype=np.int32).reshape(rows, cols)
    codes = np.abs(directions).astype(np.int16)
    del directions          # le raster brut n'est plus utile
    step = np.zeros((rows, cols), dtype=np.float32)
    diagonal = cellsize * math.sqrt(2.0)

    for code, (dr, dc) in FLOW_OFFSETS.items():
        selected = mask & (codes == code)
        if not selected.any():
            continue
        source_rows, source_cols = np.nonzero(selected)
        target_rows = source_rows + dr
        target_cols = source_cols + dc
        # Une maille qui s'ecoule hors du bassin reste sa propre racine.
        inside = (
            (target_rows >= 0) & (target_rows < rows)
            & (target_cols >= 0) & (target_cols < cols)
        )
        source_rows, source_cols = source_rows[inside], source_cols[inside]
        target_rows, target_cols = target_rows[inside], target_cols[inside]
        keep = mask[target_rows, target_cols]
        source_rows, source_cols = source_rows[keep], source_cols[keep]
        target_rows, target_cols = target_rows[keep], target_cols[keep]
        down[source_rows, source_cols] = (
            target_rows * cols + target_cols
        ).astype(np.int32)
        step[source_rows, source_cols] = diagonal if (dr and dc) else cellsize
    del codes

    root = outlet_row * cols + outlet_col
    down_flat = down.ravel()
    distance = step.ravel()
    down_flat[root] = root
    distance[root] = 0.0

    # Saut de pointeur : la portee double a chaque tour. Les deux tampons sont
    # alloues une fois pour toutes et les operations se font en place ; ecrire
    # ces lignes de la facon naturelle creerait trois tableaux neufs a chaque
    # tour, soit sur un grand bassin plusieurs centaines de megaoctets alloues
    # et rendus une vingtaine de fois.
    reached = np.empty_like(distance)
    composed = np.empty_like(down_flat)
    for _ in range(64):
        np.take(distance, down_flat, out=reached)
        distance += reached
        np.take(down_flat, down_flat, out=composed)
        if np.array_equal(composed, down_flat):
            break
        down_flat, composed = composed, down_flat
    del reached, composed

    # Seules comptent les mailles qui atteignent reellement l'exutoire. Le
    # masquage se fait en place, sur le tableau de distances lui-meme : passer
    # par np.where avec un -1.0 Python produirait un tableau neuf en double
    # precision, deux fois plus lourd que celui qu'on masque.
    reaches = (down_flat == root) & mask.ravel()
    reaches[root] = True
    distance[~reaches] = np.float32(-1.0)
    del reaches
    flat = int(np.argmax(distance))
    far_row, far_col = divmod(flat, cols)
    return float(distance[flat]), (far_row, far_col)


# ---------------------------------------------------- Temps de concentration

def concentration_times(area_km2, length_km, slope_mm, z_mean, z_min):
    """Temps de concentration selon quatre formules usuelles, en heures.

    Les formules ne mesurent pas la meme chose et divergent volontiers d'un
    facteur deux : c'est cet ecart qui renseigne, pas une valeur isolee. Une
    formule dont les conditions d'application ne sont pas reunies renvoie None
    plutot qu'un nombre trompeur.
    """
    times = {}

    # Kirpich : petits bassins ruraux pentus, formule d'origine en minutes.
    if length_km > 0 and slope_mm > 0:
        length_m = length_km * 1000.0
        times["kirpich_h"] = (
            0.0195 * (length_m ** 0.77) * (slope_mm ** -0.385) / 60.0
        )
    else:
        times["kirpich_h"] = None

    # Giandotti : usage courant en France, demande une denivelee utile.
    relief = z_mean - z_min
    if area_km2 > 0 and relief > 0:
        times["giandotti_h"] = (
            (4.0 * math.sqrt(area_km2) + 1.5 * length_km)
            / (0.8 * math.sqrt(relief))
        )
    else:
        times["giandotti_h"] = None

    # Passini : combine surface et longueur du cheminement.
    if area_km2 > 0 and length_km > 0 and slope_mm > 0:
        times["passini_h"] = (
            0.108 * ((area_km2 * length_km) ** (1.0 / 3.0))
            / math.sqrt(slope_mm)
        )
    else:
        times["passini_h"] = None

    # Ventura : ne depend que de la surface et de la pente.
    if area_km2 > 0 and slope_mm > 0:
        times["ventura_h"] = 0.1272 * math.sqrt(area_km2 / slope_mm)
    else:
        times["ventura_h"] = None

    valid = [v for v in times.values() if v is not None]
    times["min_h"] = min(valid) if valid else None
    times["max_h"] = max(valid) if valid else None
    times["moyen_h"] = sum(valid) / len(valid) if valid else None
    return times


# ------------------------------------------------------------- Orchestration

def compute(delineation_result, network_result=None, progress=None):
    """Calcule toutes les caracteristiques du bassin.

    Renvoie un dictionnaire plat, complete de la courbe hypsometrique.
    """
    def report(message):
        if progress is not None:
            progress(message)

    rasters = delineation_result["rasters"]
    dem_info = delineation_result["dem"]
    cellsize = dem_info["resolution"]

    basin_array, basin_nodata, transform = _read(rasters["basin"])
    mask = np.isfinite(basin_array) & (basin_array > 0)
    if basin_nodata is not None:
        mask &= basin_array != basin_nodata
    del basin_array
    cell_count = int(mask.sum())
    if cell_count == 0:
        raise MetricsError("Masque du bassin vide.")

    # Tout ce qui suit ne travaille que sur le rectangle du bassin. L'emprise
    # de calcul couvre le reseau amont elargi de deux kilometres, souvent bien
    # plus vaste : lire le reste serait de la memoire depensee pour des
    # mailles qui seront ecartees de toute facon.
    full_shape = mask.shape
    window, mask = basin_window(mask)
    col_offset, row_offset = window[0], window[1]
    if progress is not None and window[2] * window[3] < full_shape[0] * full_shape[1]:
        report("Fenetre du bassin : {0} x {1} px au lieu de {2} x {3}".format(
            window[2], window[3], full_shape[1], full_shape[0]))

    area = delineation_result["area"]
    perimeter = delineation_result["perimeter"]

    report("Forme et rectangle equivalent...")
    values = {
        "surface_m2": area,
        "surface_km2": area / 1e6,
        "surface_ha": area / 1e4,
        "perimetre_m": perimeter,
        "perimetre_km": perimeter / 1000.0,
        "nb_mailles": cell_count,
    }
    values.update(shape_metrics(area, perimeter))

    report("Altimetrie et hypsometrie...")
    values.update(elevation_metrics(dem_info["path"], mask, window))

    report("Pentes...")
    values.update(slope_metrics(dem_info["path"], mask, window))

    report("Plus long cheminement hydraulique...")
    origin_x, pixel_x, _, origin_y, _, pixel_y = transform
    outlet_x, outlet_y = delineation_result["outlet"]
    # Les indices sont ceux de la fenetre, pas ceux du raster entier.
    outlet_rowcol = (int((outlet_y - origin_y) / pixel_y) - row_offset,
                     int((outlet_x - origin_x) / pixel_x) - col_offset)
    length, far_cell = longest_flow_path(
        rasters["drainage"], mask, outlet_rowcol, cellsize, window
    )
    values["long_cheminement_m"] = length
    values["long_cheminement_km"] = length / 1000.0
    values["point_le_plus_eloigne"] = (
        origin_x + (far_cell[1] + col_offset + 0.5) * pixel_x,
        origin_y + (far_cell[0] + row_offset + 0.5) * pixel_y,
    )

    # Indice de pente global : denivelee utile rapportee a la longueur du
    # rectangle equivalent. La denivelee utile ecarte les 5 % extremes, qui
    # relevent souvent d'artefacts du MNT plutot que du relief.
    useful_relief = values["z_hypso_5_m"] - values["z_hypso_95_m"]
    rect_length = values["rect_longueur_m"]
    values["denivelee_utile_m"] = useful_relief
    values["indice_pente_global_mkm"] = (
        useful_relief / (rect_length / 1000.0) if rect_length > 0 else None
    )
    values["denivelee_specifique_m"] = (
        values["indice_pente_global_mkm"] * math.sqrt(values["surface_km2"])
        if values["indice_pente_global_mkm"] else None
    )

    report("Densite de drainage...")
    values["lineaire_hydro_km"] = None
    values["densite_drainage_kmkm2"] = None
    if network_result is not None:
        geometry = delineation_result["geometry"]
        linear = 0.0
        for record in network_result.get("upstream", []):
            clipped = record["geometry"].intersection(geometry)
            if not clipped.isEmpty():
                linear += clipped.length()
        values["lineaire_hydro_km"] = linear / 1000.0
        values["densite_drainage_kmkm2"] = (
            (linear / 1000.0) / values["surface_km2"]
            if values["surface_km2"] > 0 else None
        )

    report("Temps de concentration...")
    values["temps_concentration"] = concentration_times(
        values["surface_km2"], values["long_cheminement_km"],
        values["pente_moyenne_mm"], values["z_moyen_m"], values["z_min_m"],
    )

    return values
