import csv
import gc
import matplotlib.pyplot as plt
from starplot import OpticPlot, DSO, _,  MapPlot, Projection
from starplot.callables import color_by_bv
from starplot.optics import Refractor
from starplot.styles import PlotStyle, extensions, ColorStr
from datetime import datetime, timezone
import io


def generate_map(object_name: str) -> io.BytesIO:
    try:
        style = PlotStyle().extend(
            extensions.BLUE_LIGHT,
            extensions.MAP,
        )
        
        if object_name.upper().startswith('M'):
            object_name = object_name[1:]
        dso = DSO.get(m=object_name)
        if not dso:
            dso = DSO.get(name=object_name)
        
        if not dso:
            return None
        
        p = MapPlot(
                projection=Projection.MERCATOR,
                ra_min=(dso.ra-30),
                ra_max=(dso.ra+30),
                dec_min=(dso.dec-20),
                dec_max=(dso.dec+20),
                style=style,
                resolution=4000,
                autoscale=True,
        )

        p.gridlines()
        p.constellations()
        p.constellation_borders()

        p.stars(where=[_.magnitude < 6], bayer_labels=True, where_labels=[_.magnitude < 5])

        p.open_clusters(
            where=[_.size < 1, _.magnitude < 9],
            labels=None,
            label_fn=lambda d: d.ngc,
            true_size=False,
        )
        p.open_clusters(
            # plot larger clusters as their true apparent size
            where=[_.size > 1, (_.magnitude < 9) | (_.magnitude.isnull())],
            labels=None,
        )

        p.nebula(
            where=[(_.magnitude < 9) | (_.magnitude.isnull())],
            labels=None,
            label_fn=lambda d: d.ngc,
        )

        #p.galaxies()
        p.dsos(where=[_.magnitude < 8], labels=None)
        
        p.constellation_labels()
        p.milky_way()
        p.ecliptic()

        p.marker(
            ra=dso.ra,
            dec=dso.dec,
            style={
                "marker": {
                    "size": 80,
                    "symbol": "circle",
                    "fill": "full",
                    "color": "#ed7eed",
                    "edge_color": "#e0c1e0",
                    "alpha": 0.6,
                },
                "label": {
                    "font_size": 25,
                    "font_weight": "bold",
                    "font_color": "#c83cc8",
                    "font_alpha": 1,
                },
            },
            label=object_name,
            legend_label=object_name
        )

        image_bytes = io.BytesIO()
        p.export(image_bytes, format="jpg", padding=0.1, transparent=True)
        image_bytes.seek(0)
        
        return image_bytes
        
    finally:
        # Nettoyer explicitement les objets matplotlib/starplot
        try:
            if 'p' in locals():
                # Fermer la figure matplotlib associée
                if hasattr(p, 'fig') and p.fig is not None:
                    plt.close(p.fig)
                elif hasattr(p, 'ax') and p.ax is not None and hasattr(p.ax, 'figure'):
                    plt.close(p.ax.figure)
                del p
        except:
            pass
        
        # Forcer le garbage collection
        gc.collect()


# Ouvrir et lire le fichier CSV
with open('../catalog/catalog.csv', 'r', encoding='utf-8') as file:
    reader = csv.DictReader(file, delimiter=';')
    
    count = 0
    # Parcourir toutes les lignes et afficher la colonne 1 (Type)
    for row in reader:
        if (row['Type']=='0'):
            print(f"Traitement de {row['Name']} ({count})")
            
            try:
                image = generate_map(row['Name'])
                if image:
                    with open(f'../catalog/location/{row["Name"]}.jpg', 'wb') as f:
                        f.write(image.getvalue())
                    # Libérer explicitement l'objet BytesIO
                    image.close()
                    del image
                
            except Exception as e:
                print(f"Erreur pour {row['Name']}: {e}")
            
            count += 1
            
            # Forcer un nettoyage périodique (tous les 10 objets par exemple)
            if count % 10 == 0:
                plt.close('all')  # Fermer toutes les figures matplotlib
                gc.collect()      # Forcer le garbage collection
                print(f"Nettoyage mémoire effectué après {count} objets")

print("Traitement terminé")
# Nettoyage final
plt.close('all')
gc.collect()