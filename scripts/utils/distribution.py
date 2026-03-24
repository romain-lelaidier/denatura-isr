import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import scipy as sp

def find_correct_skip_rows(fpath, max_skip=200):
    """
    Attempts to find the correct number of rows to skip when opening a CSV with pandas.
    
    :param file_path: Path to the CSV file.
    :param max_skip: Maximum number of rows to try skipping.
    :return: A tuple containing the DataFrame and the correct skiprows value.
    """
    nskip = 6  # Start with no skipped rows
    
    while nskip <= max_skip:
        try:
            df = pd.read_csv(fpath, sep=r'\s+', skiprows=nskip)
            # Check if column names are valid
            if all(isinstance(col, str) for col in df.columns):
                #print(f"Successfully loaded with skiprows={nskip}")
                return nskip
        except Exception as e:
            pass
        
        nskip += 1  # Increment and try again

    #raise ValueError(f"Could not determine the correct skiprows value within {max_skip} rows.")
    print(f"Could not determine the correct skiprows value within {max_skip} rows.")
    return -1 

def get_distribution_file_info(fpath):
    m_read = open(fpath,'r')
    lines = m_read.readlines()
    cols = []
    for line in lines:
        if("# column" in line):
            line = line.replace(":"," ")
            tokens = line.split()
            cols.append(tokens[3])
        if("# NX" in line):
            tokens = line.split()
            NX = int(tokens[3])
        if("# NY" in line):
            tokens = line.split()
            NY = int(tokens[3])
    nskip = find_correct_skip_rows(fpath)
    return NX, NY, cols, nskip+2

class Distribution:

    def __init__(self, NX, NY, df):
        self.NX = NX
        self.NY = NY
        self.df = df

    @classmethod
    def load_from_file(cls, fpath):
        NX, NY, colnames, nskip = get_distribution_file_info(fpath)
        df = pd.read_csv(fpath,sep=r'\s+',header=None,skiprows=nskip)
        df.columns = colnames
        return cls(NX, NY, df)
    
    @property
    def x_min(self):
        return self.df['x-distance'].min()
    @property
    def x_max(self):
        return self.df['x-distance'].max()
    @property
    def y_min(self):
        return self.df['y-distance'].min()
    @property
    def y_max(self):
        return self.df['y-distance'].max()
    @property
    def x(self):
        return np.linspace(self.x_min, self.x_max, self.NX)
    @property
    def y(self):
        return np.linspace(self.y_min, self.y_max, self.NY)
    @property
    def xw(self):
        return (self.x_max - self.x_min) / self.NX
    @property
    def yh(self):
        return (self.y_max - self.y_min) / self.NY
    @property
    def xs(self):
        return self.df['x-distance'].unique()
    @property
    def ys(self):
        return self.df['y-distance'].unique()
    
    @property
    def area(self):
        return (self.x_max - self.x_min) * (self.y_max - self.y_min)
    
    def get_col(self, colname):
        values = self.df[colname].to_numpy()
        return values.reshape(self.NY, self.NX)
    
    def add_col(self, colname, colval):
        assert(colval.size == len(self.df))
        self.df[colname] = colval.reshape(colval.size)

    def plot(self, column="Uraninite", alpha=1):
        U = self.get_col(column)
        plt.pcolormesh(self.x, self.y, U, alpha=alpha)
        plt.colorbar()
        # plt.show()

    def evaluate(self, x, y, colname):
        x_close = self.xs[np.argmin([ np.abs(x - xg) for xg in self.xs ])]
        y_close = self.ys[np.argmin([ np.abs(y - yg) for yg in self.ys ])]
        entry = self.df[ (self.df['x-distance'] == x_close) & (self.df['y-distance'] == y_close) ]
        return entry[colname].values[0]

    def generate(self, colname):
        d = self.df[colname]
        while True:
            x = self.x_min + np.random.rand(1) * (self.x_max - self.x_min)
            y = self.y_min + np.random.rand(1) * (self.y_max - self.y_min)
            z = d.min() + np.random.rand(1) * (d.max() - d.min())
            if z <= self.evaluate(x, y, colname):
                return [x, y]
            
    def smoothen(self, colname, smoothed_colname, smooth_factor):
        sigma = [ smooth_factor / self.xw, smooth_factor / self.yh ]
        smoothed = sp.ndimage.filters.gaussian_filter(self.get_col(colname), sigma, mode='constant')
        self.add_col(smoothed_colname, smoothed)
        return smoothed
