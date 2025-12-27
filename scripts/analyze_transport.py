#!/usr/bin/env python3
"""
analyze_transport.py

A Python script to analyze colloid-facilitated contaminant transport data.
Calculates breakthrough curves, retardation factors, and other key metrics.

Input: CSV file with columns: time (min), concentration (mg/L), column_length (cm), flow_rate (mL/min), etc.
Output: Plots, calculated parameters, and summary statistics.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse
import sys

def load_data(csv_path):
    """
    Load experimental data from a CSV file.
    Expected columns: 'time', 'concentration', 'column_length', 'flow_rate',
                      'porosity', 'bulk_density', 'colloid_concentration' (optional).
    """
    df = pd.read_csv(csv_path)
    required = ['time', 'concentration']
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Required column '{col}' not found in CSV.")
    return df

def calculate_breakthrough_curve(df, column_length, flow_rate, porosity):
    """
    Compute normalized concentration C/C0 vs pore volumes.
    
    Parameters:
        df: DataFrame with 'time' and 'concentration'
        column_length: column length (cm)
        flow_rate: flow rate (mL/min)
        porosity: soil porosity (dimensionless)
    
    Returns:
        df with added columns 'pore_volumes' and 'C_normalized'
    """
    # Assume initial concentration C0 is the maximum concentration observed
    C0 = df['concentration'].max()
    if C0 == 0:
        C0 = 1.0  # avoid division by zero
    
    # Pore volume (mL) = column cross‑sectional area * length * porosity
    # For simplicity, assume column cross‑sectional area = 1 cm² (adjust if needed)
    column_area = 1.0  # cm²
    pore_volume = column_area * column_length * porosity  # mL
    
    # Pore volumes = cumulative volume / pore_volume
    # Cumulative volume = flow_rate * time
    df['cumulative_volume'] = flow_rate * df['time']
    df['pore_volumes'] = df['cumulative_volume'] / pore_volume
    df['C_normalized'] = df['concentration'] / C0
    
    return df

def compute_retardation_factor(df):
    """
    Estimate retardation factor R from breakthrough curve.
    R = (V_peak) / (V_peak_non‑retarded) where V_peak is pore volume at C/C0 = 0.5.
    Simplistic approach: use the pore volume at which C_normalized reaches 0.5.
    """
    # Find the first time C_normalized crosses 0.5
    series = df['C_normalized']
    idx = (series >= 0.5).idxmax() if (series >= 0.5).any() else len(series) - 1
    pore_vol_at_half = df.loc[idx, 'pore_volumes']
    
    # Non‑retarded tracer peak at pore volume ≈ 1 (ideal plug flow)
    R = pore_vol_at_half / 1.0
    return R, pore_vol_at_half

def plot_breakthrough(df, output_path=None):
    """Generate a breakthrough curve plot."""
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(df['pore_volumes'], df['C_normalized'], 'b-', linewidth=2, label='C/C0')
    ax.axhline(0.5, color='r', linestyle='--', alpha=0.5, label='C/C0 = 0.5')
    ax.set_xlabel('Pore volumes')
    ax.set_ylabel('Normalized concentration (C/C0)')
    ax.set_title('Breakthrough curve')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.6)
    
    if output_path:
        plt.savefig(output_path, dpi=300)
        print(f"Plot saved to {output_path}")
    else:
        plt.show()
    plt.close()

def main():
    parser = argparse.ArgumentParser(description='Analyze contaminant transport data.')
    parser.add_argument('input_csv', help='Path to input CSV file')
    parser.add_argument('--column_length', type=float, default=10.0,
                        help='Column length (cm)')
    parser.add_argument('--flow_rate', type=float, default=1.0,
                        help='Flow rate (mL/min)')
    parser.add_argument('--porosity', type=float, default=0.4,
                        help='Soil porosity (dimensionless)')
    parser.add_argument('--output_plot', default='breakthrough_curve.png',
                        help='Filename for output plot (optional)')
    parser.add_argument('--output_summary', default='transport_summary.txt',
                        help='Filename for summary text file (optional)')
    
    args = parser.parse_args()
    
    try:
        df = load_data(args.input_csv)
    except Exception as e:
        print(f"Error loading data: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Calculate breakthrough curve
    df = calculate_breakthrough_curve(df, args.column_length, args.flow_rate, args.porosity)
    
    # Compute retardation factor
    R, pore_vol_half = compute_retardation_factor(df)
    
    # Generate plot
    plot_breakthrough(df, args.output_plot)
    
    # Write summary
    with open(args.output_summary, 'w') as f:
        f.write("=== Colloid‑Facilitated Transport Analysis ===\n")
        f.write(f"Input file: {args.input_csv}\n")
        f.write(f"Column length: {args.column_length} cm\n")
        f.write(f"Flow rate: {args.flow_rate} mL/min\n")
        f.write(f"Porosity: {args.porosity}\n")
        f.write(f"Retardation factor R: {R:.3f}\n")
        f.write(f"Pore volume at C/C0 = 0.5: {pore_vol_half:.3f}\n")
        f.write(f"Maximum concentration C0: {df['concentration'].max():.3f} mg/L\n")
        f.write(f"Number of data points: {len(df)}\n")
    
    print(f"Analysis complete. Summary written to {args.output_summary}")
    print(f"Retardation factor R = {R:.3f}")

if __name__ == '__main__':
    main()