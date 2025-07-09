from services.platesolver import PlateSolveAstap

def calculate_fov(focale: int, pixel_x, pixel_y, pixel_size: float):
    sampling = 57.3 * 10e-4 * pixel_size / focale
    horizontalFov = sampling * pixel_x
    verticalFov = sampling * pixel_y
    fov = (horizontalFov ** 2 + verticalFov ** 2) ** (1/2)
    return (sampling, horizontalFov, verticalFov, fov)

def get_solver(CONFIG):
    focale = CONFIG["telescope"].get("focale", 650)
    pixel_x = CONFIG["camera"].get("horizontal_pixels",2000)
    pixel_y = CONFIG["camera"].get("vertical_pixels",1000)
    pixel_size = CONFIG["camera"].get("pixel_size",3.6)
    fov = calculate_fov(focale, pixel_x, pixel_y, pixel_size)[3]
    return PlateSolveAstap(fov,CONFIG["telescope"].get("astap_catalog"), search_radius=CONFIG["camera"].get("astap_default_search_radius",10))