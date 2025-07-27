from services.platesolver import PlateSolveAstap
from cv2 import GaussianBlur
def calculate_fov(focale: int, pixel_x, pixel_y, pixel_size: float):

    resolution = pixel_size / focale * 206.265 
    horizontalFov = resolution * pixel_x /  3600
    verticalFov = resolution * pixel_y / 3600
    #fov = (horizontalFov ** 2 + verticalFov ** 2) ** (1/2)
    fov=min(horizontalFov, verticalFov)
    #fov=0.8
    print((resolution, horizontalFov, verticalFov, fov))
    return (resolution, horizontalFov, verticalFov, fov)

def get_solver(CONFIG):
    focale = CONFIG["telescope"].get("focale", 650)
    pixel_x = CONFIG["camera"].get("horizontal_pixels",2000)
    pixel_y = CONFIG["camera"].get("vertical_pixels",1000)
    pixel_size = CONFIG["camera"].get("pixel_size",3.6)
    print(focale, pixel_x, pixel_y, pixel_size)
    fov = calculate_fov(focale, pixel_x, pixel_y, pixel_size)[3]
    print("fov:",fov)
    return PlateSolveAstap(fov,CONFIG["global"].get("astap_catalog"), search_radius=CONFIG["global"].get("astap_default_search_radius",10))


def get_slew_error( ra1, dec1, ra2, dec2):
    error_rate = ((ra1 -ra2)**2 + (dec1 -dec2)**2)**(1/2)
    return error_rate


def apply_focus_blur(image, focus_position, best_position=1020, blur_scale=0.01):
    deviation = abs(focus_position - best_position)
    sigma = deviation * blur_scale + 0.8  # un peu de flou même au mieux
    #print(sigma)
    return GaussianBlur(image, (0, 0), sigma)