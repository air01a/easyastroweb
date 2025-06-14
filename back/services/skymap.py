
from starplot import OpticPlot, DSO, _,  MapPlot, Projection
from starplot.callables import color_by_bv
from starplot.optics import Refractor
from starplot.styles import PlotStyle, extensions
from datetime import datetime, timezone
import io

def generate_dso_image(object_name: str) -> io.BytesIO:
    dso = DSO.get(m=object_name)
    if not dso:
        dso = DSO.get(name=object_name)
    
    if not dso:
            return None
    
    dt = datetime(2024, 11, 29, 23, 0, 0, tzinfo=timezone.utc)

    style = PlotStyle().extend(
        extensions.GRAYSCALE_DARK,
        extensions.OPTIC,
    )

    plot = OpticPlot(
        ra=dso.ra,
        dec=dso.dec,
        lat=50.6667,
        lon=3.15,
        optic=Refractor(
            focal_length=250,
            eyepiece_focal_length=11,
            eyepiece_fov=100,
        ),
        dt=dt,
        style=style,
        resolution=800,
        autoscale=True,
    )

    plot.stars(where=[_.magnitude < 14], color_fn=color_by_bv, bayer_labels=True)
    plot.dsos(where=[_.magnitude < 4.1], labels=None)

    image_bytes = io.BytesIO()
    plot.export(image_bytes, format="png", padding=0.1, transparent=True)
    image_bytes.seek(0)
    return image_bytes

def generate_map(object_name:str)-> io.BytesIO:
    style = PlotStyle().extend(
        extensions.BLUE_LIGHT,
        extensions.MAP,
    )

    dso = DSO.get(m=object_name)
    if not dso:
        dso = DSO.get(name=object_name)
    
    if not dso:
            return None
    print(dso)
    p = MapPlot(
        projection=Projection.MERCATOR,
        ra_min=(dso.ra-2)*15,
        ra_max=(dso.ra+2)*15,
        dec_min=(dso.dec-20),
        dec_max=(dso.dec+20),
        style=style,
        resolution=4096,
        autoscale=True,
    )
    p.gridlines()
    p.constellations()
    p.constellation_borders()

    p.stars(where=[_.magnitude < 8], bayer_labels=True, where_labels=[_.magnitude < 5])

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

    p.galaxies()

    p.constellation_labels()
    p.milky_way()
    p.ecliptic()

    image_bytes = io.BytesIO()
    p.export(image_bytes, format="png", padding=0.1, transparent=True)
    image_bytes.seek(0)
    return image_bytes