import numpy as np 
import matplotlib.pyplot as plt
import scipy as sp
import shapely
import re
from utils.distribution import Distribution
from utils.spatial import voronoi_finite_polygons_2d


class Well:
    def __init__(self, type, x, y):
        self.type = type    # 'i' for injector ; 'p' for producer
        self.x = x          # (m)
        self.y = y          # (m)
        self.n = None       # number of opposite type neighbors
        self.RC = None      # (m) characteristical radius

    @classmethod
    def injector(cls, x, y):
        return cls('i', x, y)
    
    @classmethod
    def producer(cls, x, y):
        return cls('p', x, y)



class DistributionPlacer:

    available_placement_types = [ "HEX", "SQR", "ORG" ]
    T_res_ref = (3*np.sqrt(3) * 42**2) * 12 / 12    # h for a 42m-radius cell with 12 m3/h production flow

    def __init__(self, dtb: Distribution):
        self.dtb = dtb
        self.U = dtb.get_col("Uraninite")
        self.gx, self.gy = dtb.meshgrid


    # CALCULATION
    def function_sum(self, wells: list[Well], f):
        filter = np.zeros(self.U.shape)
        for well in wells:
            filter += f((well.x - self.gx) ** 2 + (well.y - self.gy) ** 2)
        return filter

    def filter_inverse_square(self, wells: list[Well], RC: float):
        x = 0.334       # R^2/(2 sigma^2) -> eta = 85%
        sigma = RC / np.sqrt(2*x)
        return self.function_sum(wells, lambda d: np.exp(-d/(2*sigma**2)))

    def estimated_production_filter(self, wells: list[Well], RC):
        filter_injectors = self.filter_inverse_square([ well for well in wells if well.type == 'i' ], RC)
        filter_producers = self.filter_inverse_square([ well for well in wells if well.type == 'p' ], RC)
        filter_injectors = np.minimum(filter_injectors, 1)
        filter_producers = np.minimum(filter_producers, 1)
        return filter_injectors * filter_producers

    def estimated_U_production(self, wells: list[Well], RC: float):
        filter = self.estimated_production_filter(wells, RC)
        porosity = 0.23
        Vcell = (400/80) * (300/60) * 12            # m3
        Vwater = filter * Vcell * porosity * 1000   # L
        return np.sum(Vwater * self.U) * 270 / 1e6       # T


    # GENERATION
    def generate_grid_hexagons(self, RC: float) -> list[Well]:
        R = np.sqrt(2*np.pi/np.sqrt(3)) * RC
        wells = []
        x, y = self.dtb.x_min, self.dtb.y_min
        i, j = 0, 0
        while x < self.dtb.x_max and y < self.dtb.y_max:
            if i % 3 == 1:
                wells.append(Well.producer(x, y))
            else:
                wells.append(Well.injector(x, y))
            x += R
            i += 1
            if x > self.dtb.x_max:
                j += 1
                i = (j % 2) * 2
                y += R * np.cos(np.pi / 6)
                x = self.dtb.x_min + (j % 2) * R / 2
        return R, wells
    
    def generate_grid_square(self, RC: float) -> list[Well]:
        R = np.sqrt(np.pi) * RC
        wells = []
        x, y = self.dtb.x_min, self.dtb.y_min
        j = 0
        while x < self.dtb.x_max and y < self.dtb.y_max:
            if j % 2 == 1:
                wells.append(Well.producer(x, y))
            else:
                wells.append(Well.injector(x, y))
            x += np.sqrt(2) * R
            if x > self.dtb.x_max:
                j += 1
                x = self.dtb.x_min + (j % 2) * np.sqrt(2) * R / 2
                y += np.sqrt(2) * R / 2
        return R, wells


    # TRANSFORMATION
    def filter_wells(self, wells, RC):
        estimated_wells_individual_production = np.array(list(map(lambda pos: (self.filter_inverse_square([pos], RC) * self.U).sum(), wells)))
        valid_indices = list(filter(lambda i: estimated_wells_individual_production[i] > estimated_wells_individual_production.max() / 4, range(len(wells))))
        return [ wells[i] for i in valid_indices ]
    

    # OPTIMIZATION
    def optimal_transformation(self, wells: list[Well], max_R: float, RC: float) -> list[Well]:

        cx = (self.dtb.x_min + self.dtb.x_max) / 2    # center x
        cy = (self.dtb.y_min + self.dtb.y_max) / 2    # center y
        
        def transform(well: Well, opt_X) -> Well:
            x, y = well.x, well.y
            theta, dx, dy = opt_X
            cost, sint = np.cos(theta), np.sin(theta)
            x2, y2 = x + dx - cx, y + dy - cy
            x3, y3 = x2 * cost - y2 * sint, x2 * sint + y2 * cost
            return Well(well.type, x3 + cx, y3 + cy)
        
        def transform_wells(wells: list[Well], opt_X) -> list[Well]:
            return [ transform(well, opt_X) for well in wells ]

        def opt_error(opt_X):
            filtered_wells = self.filter_wells(transform_wells(wells, opt_X), RC)
            return - self.estimated_U_production(filtered_wells, RC)

        res = sp.optimize.minimize(
            opt_error,
            np.array([ 0, 0, 0 ]),
            bounds = [ (-2*np.pi, 2*np.pi), (-max_R, max_R), (-max_R, max_R) ],
            method = "Nelder-Mead"
        )

        return self.filter_wells(transform_wells(wells, res.x), RC)

    def place(self, settings: dict, output_figure_path: str = None) -> list[Well]:

        type = settings["type"]
        RC = settings["RC"]

        if type == "ORG":

            IP_ratio = settings["IP_ratio"]     # N_injectors / N_producers

            # overall distribution shape
            US = self.dtb.smoothen("Uraninite", "U_smoothed", 10)
            U_area = US > US.max() / 10
            U_area_points = []
            gx, gy = self.dtb.meshgrid
            for i, U_area_i in enumerate(U_area):
                for j, U_area_ij in enumerate(U_area_i):
                    if U_area_ij:
                        x, y = gx[i,j], gy[i,j]
                        U_area_points.append([ x, y ])
            dilation = max(self.dtb.xw, self.dtb.yh)*3
            shape = shapely.MultiPoint(U_area_points).buffer(dilation)
            shape = shape.buffer(-dilation).simplify(dilation)

            # configuration
            cell_area = self.dtb.xw * self.dtb.yh          # m2
            area = U_area.sum() * cell_area      # m2
            well_area = np.pi * RC**2
            N_wells = area / well_area
            N_injectors = int(round(N_wells / (1 + 1/IP_ratio)))
            N_producers = int(round(N_wells / (1 +   IP_ratio)))
            N_wells = N_injectors + N_producers
            print(f" RC={RC:.1f}m -> {N_wells} wells ({N_producers} producers)")

            # wells generation
            np_wells = np.array([ self.dtb.generate("U_smoothed") for _ in range(N_wells) ])

            # OPTIMIZATION
            def decompose_opt_X(opt_X):
                injectors = opt_X[0:N_injectors*2].reshape((N_injectors, 2))
                producers = opt_X[N_injectors*2: ].reshape((N_producers, 2))
                return [ Well.injector(x, y) for [ x, y ] in injectors ] + [ Well.producer(x, y) for [ x, y ] in producers ]

            def opt_error(opt_X):
                wells = decompose_opt_X(opt_X)

                # U production
                U = self.estimated_U_production(wells, RC)

                # preventing aggregates
                distance_factor = 0
                for i, well_i in enumerate(wells):
                    for well_j in wells[i+1:]:
                        d = np.sqrt((well_i.x - well_j.x)**2 + (well_i.y - well_j.y)**2)
                        if d <= 3*RC:
                            distance_factor += abs(d - 2*RC)**2
                distance_factor /= N_wells * (N_wells - 1) / 2

                # preventing diverging wells
                diverging_factor = 0
                for well in wells:
                    distance = shape.distance(shapely.Point(well.x, well.y))
                    diverging_factor += distance

                # return diverging_factor
                return diverging_factor / 10 + distance_factor / 10 - U

            res = sp.optimize.minimize(
                opt_error,
                np_wells.reshape(N_wells * 2),
                bounds = [ (self.dtb.x.min(), self.dtb.x.max()) if i % 2 == 0 else (self.dtb.y.min(), self.dtb.y.max()) for i in range(N_injectors * 2 + N_producers * 2) ],
                # method = "Nelder-Mead"
            )

            wells = decompose_opt_X(res.x)
            
        elif type == "HEX":
            max_R, wells = self.generate_grid_hexagons(RC)
            wells = self.optimal_transformation(wells, max_R, RC)

        elif type == "SQR":
            max_R, wells = self.generate_grid_square(RC)
            wells = self.optimal_transformation(wells, max_R, RC)

        else:
            print(f"invalid placement type {type}")
            return

        self.plot_estimated_production(wells, RC, output_figure_path)

        return wells


    # OUTPUT
    def plot_estimated_production(self, wells: list[Well], RC, output_path = None):
        estimated_production = self.estimated_production_filter(wells, RC)
        plt.figure()
        plt.pcolormesh(self.dtb.x, self.dtb.y, estimated_production * self.U)
        for well in wells:
            plt.scatter(well.x, well.y, marker='x', color=('red' if well.type == 'i' else 'white'))
        N_injectors = len([ well for well in wells if well.type == 'i' ])
        plt.suptitle(f"{N_injectors} injectors ; {len(wells) - N_injectors} producers")
        plt.title(f"Estimated production: {self.estimated_U_production(wells, RC):.1f} T")
        if output_path is not None: plt.savefig(output_path)

    @classmethod
    def geometry_htc_string(cls, wells: list[Well]) -> str:
        DX, DY, DZ = 5, 5, 12
        out = ""

        for i, well in enumerate([ w for w in wells if w.type == 'p' ]):
            out += f"zone producteur_{i+1} {{\n"
            out += f"  geometry = rectangle {well.x:.2f}, {well.y:.2f}, 6 {DX}, {DY}, {DZ} m\n"
            out += f"  global-flux producteur_{i+1} \n"
            out += f"  geochem = aquifer\n"
            out += f"  source = -{well.d:.2f} m3/h\n}}\n\n"

        for i, well in enumerate([ w for w in wells if w.type == 'i' ]):
            out += f"zone injecteur_{i+1} {{\n"
            out += f"  geometry = rectangle {well.x:.2f}, {well.y:.2f}, 6 {DX}, {DY}, {DZ} m\n"
            out += f"  global-flux injecteur_{i+1} \n"
            out += f"  geochem = aquifer\n"
            out += f"  source = {well.d:.2f} m3/h using leaching_solution_20\n"
            out += f"  modify at 30 days, source = {well.d:.2f} m3/h using leaching_solution\n}}\n\n"

        return out

    @classmethod
    def parse_geometry(cls, geometry: str) -> list[Well]:
        wells = []
        wells_strs = re.findall("(zone (producteur|injecteur)_(.+)) ", geometry)
        for [ zone, type, id ] in wells_strs:
            htcz = geometry[geometry.index(zone):]
            htczb = htcz.index('{')
            htcze = htcz.index('}')
            htcz_lines = htcz[htczb+1:htcze].split('\n')
            for line in htcz_lines:
                if "geometry" in line:
                    coords_str = re.findall("([0-9.]+)", line)
                    coords_float = list(map(float, coords_str))
                    x, y = coords_float[0], coords_float[1]
                    if type == "injecteur":
                        wells.append(Well.injector(x, y))
                    elif type == "producteur":
                        wells.append(Well.producer(x, y))
        return wells


def build_flow_rates_from_voronoi(wells: list[Well], RC: float, T_res: float, figure_path: str = None) -> float:

    points = np.array([ [well.x, well.y] for well in wells ]) + np.random.random((len(wells), 2))/2
    dilation_max = RC*1.5
    bounding_region_box = shapely.MultiPoint(points).buffer(dilation_max)
    v = sp.spatial.Voronoi(points)
    regions, vertices = voronoi_finite_polygons_2d(v)

    for i, well in enumerate(wells):

        well.frontier = 0
        u = np.array([ well.x, well.y ])

        for j, well_j in enumerate(wells):
            if well.type != well_j.type:

                v = np.array([ well_j.x, well_j.y ])
                m = (u+v)/2

                matches = []
                for vi in regions[i]:
                    if vi in regions[j]:
                        matches.append(vi)

                if len(matches) > 0:
                    
                    if len(matches) == 1:
                        v1, = vertices[matches]
                        v2 = m - 20 * (v1 - m)

                    if len(matches) == 2:
                        v1, v2 = vertices[matches]
                        if np.linalg.norm(v1-m) > np.linalg.norm(v2-m):
                            v1, v2 = v2, v1

                    alpha_2 = dilation_max**2 - np.linalg.norm(m-u)**2
                    if alpha_2 > 0:
                        alpha = np.sqrt(alpha_2)
                    else:
                        # wells are too far away and cannot intersect
                        continue

                    if np.linalg.norm(v1-u) > dilation_max:
                        if np.dot(v1-m, v2-m) > 0:
                            continue
                        v1 = m + alpha * (v1-v2) / np.linalg.norm(v1-v2)

                    if np.linalg.norm(v2-u) > dilation_max:
                        v2 = m + alpha * (v2-v1) / np.linalg.norm(v2-v1)
                        well.frontier += np.linalg.norm(v1-v2)
                    else:
                        well.frontier += np.linalg.norm(v1-v2)

        polygon = shapely.Polygon(vertices[regions[i]])
        polygon = polygon.intersection(bounding_region_box)
        well.polygon = polygon
        well.area = polygon.area

    total_area = np.sum([ well.area for well in wells ])
    total_frontier = np.sum([ well.frontier for well in wells if well.type == 'p' ])
    diff = abs(np.sum([ well.frontier for well in wells if well.type == 'i' ]) - total_frontier)
    if diff > 0.001:
        print(f" WARNING : Voronoi frontiers difference = {diff:.3f} m")

    # T_res = 9166                    # h
    D = 12 * total_area / T_res     # m3/h

    for well in wells:
        well.frontier_ratio = well.frontier / total_frontier
        well.d = D * well.frontier_ratio

    max_d = max([ well.d for well in wells ])

    if figure_path is not None:
        # plotting
        plt.figure()
        plt.axis('equal')
        for i, well in enumerate(wells):
            color = "red" if well.type == 'i' else 'black'
            poly = [p for p in well.polygon.exterior.coords]
            plt.fill(*zip(*poly), alpha=well.d/max_d/3, color=color)
            plt.scatter(well.x, well.y, s=10*well.d/max_d, color=color)
            plt.text(well.x, well.y + RC/4, str(i), horizontalalignment="center")
        plt.savefig(figure_path)

    return max_d

# dtb = Distribution.load_from_file("../distributions/ellipse/U.dat")
# for R in np.linspace(20, )
# place_hexagons(dtb, 20, "../distributions/ellipse/hex20.geo", "../distributions/ellipse/hex20.png")