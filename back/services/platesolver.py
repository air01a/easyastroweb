from os import (path, access, X_OK)
import subprocess

class PlateSolveAstap(object):

    ASTAP_POSSIBLE_PATHS =  [
        'C:/Program Files/astap/astap_cli.exe',
        '/usr/bin/astap_cli'
    ]

    def __init__(self, fov, catalog, search_radius=10, downsample_factor=0, max_stars=400, astap_path = ""):

        if len(astap_path)>0 : 
            self.ASTAP_PATH = astap_path

        for astap_path in self.ASTAP_POSSIBLE_PATHS:
            if path.isfile(astap_path):
                self.ASTAP_PATH = astap_path
                break
        self.SEARCH_RADIUS = search_radius
        self.DOWNSAMPLE_FACTOR = downsample_factor
        self.MAX_STARS = max_stars
        self.FOV = fov #0.36
        self.CATALOG = catalog

    def _get_solution(self, fits):
        wcs_path = path.splitext(fits)[0]+'.ini'
        if not path.isfile(wcs_path):
            return (None, None)
        
        wcs_file = open(wcs_path, 'r')
        ra = None
        dec = None

        for line in wcs_file.readlines():
            if line.find('CRVAL1') != -1:
                ra = float((line.split('='))[1])*24.0/360.0
            if line.find('CRVAL2') != -1:
                dec = float((line.split('='))[1])
            if line.find('CROTA1') != -1:
                orientation = float((line.split('='))[1])
        return (ra,dec, orientation)

    def _return(self, error, ra, dec, orientation):
        return {'error':error,'ra':ra,'dec':dec, 'orientation':orientation}

    def resolve(self, fits, ra=None, dec= None, radius=0):
        radius=self.SEARCH_RADIUS if radius==0 else radius
        astap_cmd = [
            self.ASTAP_PATH,
            '-f',
            fits,
            '-r', str(radius),
            '-s', str(self.MAX_STARS),
            '-z', str(self.DOWNSAMPLE_FACTOR),
             '-d', self.CATALOG,
             '-update'
        ]
        if ra!=None:
            astap_cmd.append('-ra')
            astap_cmd.append(str(ra))
        if dec!=None:
            astap_cmd.append('-spd')
            astap_cmd.append(str(dec+90))
        result = subprocess.run(astap_cmd,capture_output=True, text=True)
        print(result)
        if result.returncode == 1:
            return {'error':1,'ra': ra,'dec': dec, 'orientation':0}
        (ra,dec, orientation) = self._get_solution(fits)
        return self._return( 2*int(ra==None),ra,dec, orientation)
        
#test = PlateSolveAstap(1.62,"c:/Program Files/astap/",search_radius=10 )
#print(test.resolve("capture-ps-test-2025-07-10T08.41.37.fits", radius=180))