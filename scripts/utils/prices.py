kg_per_lbs = 0.454      # kg/LBS

class Prices:
    def __init__(self, U_lbs_price: float, SO4_T_price: float, well_inj_price: float, well_prd_price: float):
        self.U_lbs_price = U_lbs_price
        self.SO4_T_price = SO4_T_price
        self.well_inj_price = well_inj_price
        self.well_prd_price = well_prd_price

    @property
    def U_mol_price(self):
        # ----------------- CALCULATIONS -----------------
        M_U = 238         # g / mol
        # M_O = 16        # g / mol
        # M_UO2  = M_U + 2*M_O    # g / mol
        N_U_1lbs = 1e3 * kg_per_lbs / M_U     # mol (for 1 LBS)
        return self.U_lbs_price / N_U_1lbs    # USD / mol U
    

# https://tradingeconomics.com/commodity/uranium
U_lbs_price = 85.90     # USD/LBS (1 LBS = 250 pounds of U3O8 = 113,4 kg U3O8)

# https://businessanalytiq.com/procurementanalytics/index/sulfuric-acid-price-index/
SO4_T_price = 170         # USD/T (Europe, NorthEast Asia)

# Batiyev, R. (2009). Uranium project-pre feasibility of tortkuduk central (kazakhstan-katco)
well_inj_price = 32400  # USD
well_prd_price = 43200  # USD

prices = Prices(U_lbs_price, SO4_T_price, well_inj_price, well_prd_price)
