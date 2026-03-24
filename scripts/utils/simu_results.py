import numpy as np
import os
import re
import matplotlib.pyplot as plt

from hytecio.core import HytecSimulation
from prices import Prices
from distribution import Distribution

class SimuResults:

    def __init__(self, root):
        """
        initiates numpy arrays of the same length, corresponding to different simulation results
        - time (years)
        - pH
        - flow_water (m3/s)
        - flow_U (mol/s)
        - cum_U (mol)
        - acid_injected (tons)
        - acid_recovered (tons)
        """

        self.root = root
        self.parse_configuration()

        simu: HytecSimulation = HytecSimulation("config", root=root)
        simu.read_hytec_results()
        self.simu = simu

        # list of flow variables
        self.flow_vars = simu.handlers.results.flux_res_columns

        # list of self.wells
        self.wells = simu.handlers.results.cumflux_res_names
        self.wells_prod = [ i for i, well in enumerate(self.wells) if 'prod' in well ]    # indices of producer self.wells
        self.wells_inj  = [ i for i, well in enumerate(self.wells) if 'inj'  in well ]    # indices of injector self.wells

        # data itself
        fdata = simu.handlers.results.flux_res_data
        fdata_cum = simu.handlers.results.cumflux_res_data
        N = fdata.shape[1]      # number of samples for each column
        self.time = fdata[0,:,0]     # in years
        self.time[0] = 0             # replacing nan
        print(f"{len(self.flow_vars)} flow variables ; {len(self.wells_prod)} producers, {len(self.wells_inj)} injectors ; {N} time stamps ({self.time.min():.1f} - {self.time.max():.1f} y)")

        # aggregate data from all self.wells
        def sum_for_wells(wells, col_name, cum=False):
            icol = self.flow_vars.index(col_name)
            flow_col = np.zeros(N)
            data = fdata_cum if cum else fdata
            for i in wells:
                flow_col += data[icol,:,i]
            return flow_col
        
        self.water_flow_m3s = sum_for_wells(self.wells_prod, 'water [m3/s]')    # m3/s
        self.water_flow_Ls  = self.water_flow_m3s * 1e3                         # L/s

        # ----------------- pH -----------------
        self.flow_H = sum_for_wells(self.wells_prod, 'H[+] [mol/s]')
        act_coeff = 0.7
        self.pH = - np.log10(act_coeff * np.abs(self.flow_H / (self.water_flow_m3s * 1000)))

        # ----------------- URANIUM PRODUCTION -----------------
        self.U_flow_mols    = np.abs(sum_for_wells(self.wells_prod, "aqueous{UO2[2+]} [mol/s]"))           # mol/s
        self.U_flow_mgL     = np.abs(self.U_flow_mols * 238 / self.water_flow_m3s)   # mg/L
        self.U_produced_mol = np.abs(sum_for_wells(self.wells_prod, "aqueous{UO2[2+]} [mol/s]", cum=True))  # mol
        self.U_produced_tons  = np.abs(self.U_produced_mol * 238) / 1e6          # tons
        self.U_produced_total = self.U_produced_tons[-1]                         # tons

        # ----------------- ACID CONSUMPTION -----------------
        mH, mSulf = 1, 32+4*16      # H and SO4 mass numbers
        acidic_cols = [ 'H[+] [mol/s]',   'HSO4[-] [mol/s]',   'H2SO4(aq) [mol/s]' ]
        acidic_As   = [             mH,          mH + mSulf,   2*(mH + mH + mSulf) ]
        acidic_ids  = [ self.flow_vars.index(acidic_col) for acidic_col in acidic_cols ]

        self.acid_recovered = np.zeros(N)
        for i in self.wells_prod:
            for v in range(len(acidic_cols)):
                self.acid_recovered += acidic_As[v]*fdata_cum[acidic_ids[v],:,i]/1e6 # tons

        self.acid_injected = np.zeros(N)
        for i in self.wells_inj:
            for v in range(len(acidic_cols)):
                self.acid_injected += acidic_As[v]*fdata_cum[acidic_ids[v],:,i]/1e6

        self.acid_injected  = np.abs(self.acid_injected)
        self.acid_recovered = np.abs(self.acid_recovered)
        self.acid_consumed  = self.acid_injected - self.acid_recovered
        self.acid_consumed_total = self.acid_consumed[-1]

    def parse_configuration(self):
        """
        Returns:
        - distribution
        - injectors
        - producers
        """

        htc = os.path.join(self.root, "config.htc")
        htcd = open(htc, "r").read()

        # finding distribution
        lines = htcd.split('\n')
        for line in lines:
            if "read minerals" in line:
                if "#" not in line:
                    minerals = "distributed"
                    minerals_dat = line[line.index("=") + 2 : ]
                else:
                    minerals = "uniform"
            if "mineral Uraninite =" in line:
                minerals_v = line[line.index("=") + 2 : ]
                minerals_v_abs = float(minerals_v[0:minerals_v.index(' ')])
                self.U_unit = minerals_v[minerals_v.index(' ') + 1 : ]
                minerals_v = minerals_v_abs * (1 if "mg/L" in self.U_unit else 1e3 if "g/L" in self.U_unit else 0)      # mg/L

        if minerals == "distributed":
            self.dtb = Distribution.load_from_file(os.path.join(self.root, minerals_dat))
        else:
            # uniform distribution
            self.dtb = None

        # finding wells
        self.injectors = []
        self.producers = []
        wells = re.findall("(zone (producteur|injecteur)_(.+)) ", htcd)
        for [ zone, type, id ] in wells:
            htcz = htcd[htcd.index(zone):]
            htczb = htcz.index('{')
            htcze = htcz.index('}')
            htcz_lines = htcz[htczb+1:htcze].split('\n')
            for line in htcz_lines:
                if "geometry" in line:
                    coords_str = re.findall("([0-9.]+)", line)
                    coords_float = list(map(float, coords_str))
                    x, y = coords_float[0], coords_float[1]
                    if type == "injecteur":
                        self.injectors.append([x, y])
                    elif type == "producteur":
                        self.producers.append([x, y])

    def plot_configuration(self, ax):
        title = "2D configuration"
        if self.dtb != None:
            U = self.dtb.get_col("Uraninite")
            # divider = make_axes_locatable(ax)
            # cax = divider.append_axes('right', size='5%', pad=0.05)
            ax.pcolormesh(self.dtb.x, self.dtb.y, U, alpha=0.5)
            # plt.colorbar(im, cax=cax, orientation='vertical')
            title += f" ({U.min()*27000:.0f}-{U.max()*27000:.0f} ppm)"
            # im = ax.imshow(data, cmap='bone')
        for [x, y] in self.injectors:
            ax.scatter(x, y, marker='x', color='red')
        for [x, y] in self.producers:
            ax.scatter(x, y, marker='x', color='black')
        ax.set_title(title)

    def plot_pH(self, ax):
        ax.plot(self.time, self.pH, color='black')
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('Global pH [-]')
        ax.set_ylim(1, 8)
        ax.set_xlim(0, 5)
        ax.set_title("pH")

    def plot_U(self, ax):
        # for prod in range(N_self.wells):
        #     if 'prod' in self.wells[prod]:
        #         ax.plot(timeSim,np.abs(238000*fdata[u_id,:,prod]/fdata[water_id,:,prod]/1000),linestyle="dashed",linewidth=0.5)

        # ax.plot(self.time, self.U_flow_mgL, color='black')
        U_flow_kgd = self.U_flow_mols * (1000 * (238 + 2 * 16)) / (24 * 60 * 60)
        ax.plot(self.time, U_flow_kgd, color='black')
        ax.set_xlabel('Time (years)')
        ax.set_ylabel('U [kg/d]')
        ax.set_ylim(0)
        ax.set_xlim(0, 5)
        ax.set_title("Uranium production")

        ax2 = ax.twinx()
        ax2.plot(self.time, self.U_produced_tons, label="cumulated", color='green')
        ax2.set_ylabel('U [T]')
        ax2.set_ylim(0)
        ax2.axhline(self.U_produced_total, color="green", linestyle="dashed")
        ax2.annotate(f"U produced = {self.U_produced_total:.1f} T", xy=(5, self.U_produced_total), ha="right", va="bottom", color="green")

    def plot_acid(self, ax):
        ax.plot(self.time, self.acid_recovered, color='black', label="Recovered")
        ax.plot(self.time, self.acid_injected,  color='black', label="Injected", linestyle="dashed")
        ax.plot(self.time, self.acid_consumed,  color='red',   label="Consumed")
        ax.annotate(f"Acid consumed = {self.acid_consumed_total:.1f} T", xy=(5,self.acid_consumed_total), ha="right", va="bottom", color="red")
        ax.axhline(self.acid_consumed_total, color="red", linestyle="dashed")
        ax.set_xlabel('Time (days)')
        ax.set_ylabel('SO4 (T)')
        ax.set_xlim(0, 5)
        ax.set_title("Acid consumption")
        ax.legend()

    def plot_flows(self, path=None):
        print("Plotting production and acidity")
        fig, axes = plt.subplots(1, 3, figsize=(18, 6))
        axs = axes.flatten()
        self.plot_pH(axs[0])
        self.plot_U(axs[1])
        self.plot_acid(axs[2])

        fig.suptitle("Global flows")
        fig.tight_layout()

        if path != None:
            fig.savefig(path)
        
        return fig

    # ----------------- ECONOMIC RESULTS -----------------

    @property
    def d_U_produced_mol(self):
        return np.ediff1d(self.U_produced_mol)
    @property
    def d_acid_consumed(self):
        return np.ediff1d(self.acid_consumed)
    @property
    def d_time(self):
        return np.ediff1d(self.time)

    def profit_raw(self, prices: Prices) -> np.array:
        # raw instantaneous profit ($/y)
        return (self.d_U_produced_mol * prices.U_mol_price - self.d_acid_consumed * prices.SO4_T_price) / self.d_time

    def profit_actualized(self, prices: Prices, r: float) -> np.array:
        # actualized instantaneous profit ($/y) with interest rate 1+r
        actualizer = 1/np.pow(1+r, self.time[:-1])
        return self.profit_raw(prices) * actualizer

    def net_present_value(self, prices: Prices, r: float) -> float:
        # net present value with interest rate 1+r
        return self.profit_actualized(prices, r).sum() - len(self.injectors) * prices.well_inj_price - len(self.producers) * prices.well_prd_price

    def plot_profit(self, prices: Prices, r: float, ax = None):
        if ax == None:
            fig, ax = plt.subplots(1, 1)

        ax.set_title(f"Instantaneous profit (r = {r*100}%, NPV = {self.net_present_value(prices, r)/1e6:.2f} M$)")
        ax.plot(self.time[0:-1], self.profit_raw(prices), label="raw", color="black")
        ax.plot(self.time[0:-1], self.profit_actualized(prices, r), label="actualized", color="black", linestyle="dashed")
        ax.set_xlabel("time (years)")
        ax.set_ylabel("profit ($/y)")
        ax.set_xlim((self.time.min(), self.time.max()))
        ax.grid()
        ax.legend()

    def plot_npvs(self, prices: Prices, rmin: float = 0, rmax: float = 20/100, ax = None):
        if ax == None:
            fig, ax = plt.subplots(1, 1)

        N = 40
        rs = [ rmin + i/N * (rmax - rmin) for i in range(N+1) ]
        npvs = [ self.net_present_value(prices, r) for r in rs ]
        npv_max = np.array(npvs).__abs__().max()

        ax.set_title("Net Present Value for different interest rates")
        ax.plot([ r*100 for r in rs], npvs, color="blue")
        ax.set_xlabel("$r$ (%)")
        ax.set_ylabel("NPV ($)")
        ax.set_xlim((rmin*100, rmax*100))
        ax.set_ylim((-npv_max*1.1, npv_max*1.1))
        ax.axhline(0, color="black", linestyle="dashed")
        ax.grid()

    # ----------------- PLOT ALL -----------------

    def plot_all(self, prices: Prices, title: str = None, path = None):
        print("Plotting simulation results")
        fig, axes = plt.subplots(2, 3, figsize=(18, 11))
        axs = axes.flatten()

        self.plot_pH(axs[0])
        self.plot_U(axs[1])
        self.plot_acid(axs[2])
        self.plot_profit(prices, 10/100, axs[3])
        self.plot_npvs(prices, 0, 20/100, axs[4])
        self.plot_configuration(axs[5])

        ftitle = "Simulation results"
        if title != None:
            ftitle += f" ({title})"
        fig.suptitle(ftitle, weight="bold")

        fig.tight_layout()

        if path != None:
            fig.savefig(path)
        
        return fig