#!/usr/bin/env python

__author__ = 'Tobi Alegbe & Matiss Ozols'
__date__ = '2025-01-17'
__version__ = '0.0.1'


import scanpy as sc
import pandas as pd
import numpy as np
# from pysctransform import vst, get_hvg_residuals, SCTransform
np.random.seed(42)
import argparse
import scipy as sp
import sys

def PF(X):
    cd=np.asarray(X.sum(1)).ravel()
    avg_cd=cd.mean()
    
    return sp.sparse.diags(avg_cd/cd).dot(X)

def log1p(X):
    return X.log1p()
    

def main():
    """Run CLI."""
    parser = argparse.ArgumentParser(
        description="""
            Computes normalised counts from 10x AnnData. Save to AnnData object.
            """
    )

    parser.add_argument(
        '-v', '--version',
        action='version',
        version='%(prog)s {version}'.format(version=__version__)
    )
    parser.add_argument(
        '-h5ad', '--h5ad',
        action='store',
        dest='h5ad',
        required=True,
        help=''
    )
    parser.add_argument(
        '-m', '--method',
        action='store',
        dest='method',
        required=False,
        default='cp10k',
        help=''
    )

    options = parser.parse_args()
    h5ad = options.h5ad
    adata = sc.read_h5ad(filename=h5ad)
    method = options.method
    
    if adata.X.shape[0] > 1:  # Ensure there are at least 2 rows
        print("Second row sum is an integer.")
    else:
        print("Matrix has less than 2 rows.")
        sys.exit(0)  # Exit the script gracefully

    available_methods = ['cp10k', 'scT','NONE','pf_log1p_pf']
    if method not in list(adata.layers.keys()) + available_methods:
        raise ValueError("Method not in adata.layers or available_methods.")

    if np.sum(adata.X.todense()[1,:]).is_integer():
        adata.layers['counts'] = adata.X.copy()
    elif np.sum(adata.layers['counts'].todense()[1,:]).is_integer():
        adata.X = adata.layers['counts'].copy()
    else:
        raise ValueError("Could not find raw counts in layers or X.")

    if method in list(adata.layers.keys()):
        adata.layers['dMean_normalised'] = adata.layers[method]

    if method == 'cp10k':
        # Total-count normalize (library-size correct) the data matrix X to
        # counts per million, so that counts become comparable among cells.
        adata.layers['dMean_normalised']= sc.pp.log1p(sc.pp.normalize_total(adata,
                                                        target_sum=1e4,
                                                        exclude_highly_expressed=False,
                                                        inplace=False)['X'])
    if method == 'pf_log1p_pf':
        adata.layers['dMean_normalised'] = PF(log1p(PF(adata.X)))


    
    # if method == 'scT':
    #     # pySCTransform v2, not working with current version of packages plus takes a lot of memory
    #     vst_out = vst(
    #         adata.layers['counts'].T,
    #         gene_names=adata.var_names.tolist(),
    #         cell_names=adata.obs_names.tolist(),
    #         method="fix-slope",
    #         exclude_poisson=True,
    #         correct_counts=True)
        
    #     # Some gene are dropped by scTransform, so we need to subset the AnnData
    #     adata = adata[:,list(vst_out_v2['model_parameters_fit'].index)]
    #     adata.layers['dMean_normalised'] = vst_out["corrected_counts"].T

    print('Saving normalised AnnData...')
    adata.write(f'nAD_{h5ad}')


if __name__ == '__main__':
    main()