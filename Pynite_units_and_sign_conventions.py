"""
Example demonstrating and testing units and sign conventions in Pynite.


Sign convention in PyNite:
  - Negative axial force = TENSION  (member being pulled apart)
  - Positive axial force = COMPRESSION (member being pushed together)

Units:
  - For self weight it is important to notice that Pynite
    uses weight density (force per volume)

"""

import numpy as np
from Pynite import FEModel3D


# Create model object
model = FEModel3D()

# ============================================================================
# Material definition
# ============================================================================
# Typical steel properties in SI units.
# Reference: https://www.matweb.com/search/datasheet.aspx?bassnum=MS0001

E = 200e9       # Modulus of Elasticity [Pa] (200 GPa) 
G = 80e9        # Shear Modulus [Pa] (80 GPa) 
nu = 0.25       # Poisson's Ratio
rho_mass = 8e3  # Mass density [kg/m³]

g_accel = 9.81                   # [m/s²]
rho_weight = rho_mass * g_accel  # ≈ 78480 [N/m³] — this is what PyNite uses

model.add_material('Steel', E, G, nu, rho_weight)


# ============================================================================
# Cross-section definition
# ============================================================================
# A beam element in PyNite needs four section properties:
#   A  — cross-sectional area [m²]:  determines axial stiffness (EA)
#   Iy — second moment of area about local y-axis [m⁴]: bending stiffness (EI_y)
#   Iz — second moment of area about local z-axis [m⁴]: bending stiffness (EI_z)
#   J  — torsional constant [m⁴]: torsional stiffness (GJ)
#
# Only A matters in this example because there is no bending.

A  = 1e-2    # [m²]  — 10cm × 10cm square bar
Iy = 0    # [m⁴]  
Iz = 0    # [m⁴]  
J  = 0    # [m⁴]  

# Define A "section"
model.add_section('Section', A, Iy, Iz, J)

# ============================================================================
# Build and "solve" the model
# ============================================================================

# Vertical beam of length L [m]

L = 10

# --- Nodes (name, X, Y, Z) ---
# Z = 0 for all nodes: this is a 2D problem in the XY-plane.
model.add_node('N1', 0, 0, 0)
model.add_node('N2', 0, -L, 0)

# --- Members (bars) ---
model.add_member('M1', 'N1', 'N2', 'Steel', 'Section')   # bottom horizontal

# --- Supports ---
# def_support(node, DX, DY, DZ, RX, RY, RZ) - True means fixed
# All rotations fixed, as no rotation is present in this model
# Pin at N1: fix all translations
model.def_support('N1', True, True, True, True, True, True)
# Node 2: fix in X and Z (as this is an 1D example)
model.def_support('N2', True, False, True, True, True, True)

# Add self weight (Notice the -1 to have gravity point in negative Y)
model.add_member_self_weight('FY', -1, 'SelfWeight')

# Add downwards force at N2 (1000N)
F0 = 1000 
model.add_node_load('N2', 'FY', -F0, 'PointForce')

# Define scenarios for handling different load cases in on solve
# Scenario A: self weight
model.add_load_combo('SC_A_SelfWeight', {'SelfWeight': 1.0})

# Scenario B: point force
model.add_load_combo('SC_B_PointForce', { 'PointForce': 1.0})

# Analyze (solves all load cases and combos in one pass)
model.analyze()


# ============================================================================
# Print and compare results
# ============================================================================

# Individual load-case results (unfactored, always available after analyze)
print("=== Reaction at N1 — SelfWeight load case  ===")
print(f"N1: Fy = {model.nodes['N1'].RxnFY['SC_A_SelfWeight']:.1f} N")
print(f"Expected: rho_weight * L * A = {rho_weight * L * A:.1f} N")

print("\n=== Displacement at N2 — PointForce load case ===")
print(f"N2: dy = {model.nodes['N2'].DY['SC_B_PointForce']:.1e} m")
print(f"Expected: - F0 / (E * A / L)  = -  {F0 /(E * A / L ):.1e} m")


# PyNite sign convention: positive = compression, negative = tension.
# (This is opposite to the usual structural engineering convention.)
print("\n=== Axial forces (PyNite: + = compression, − = tension) ===")
print(f"M1: Max axial {model.members['M1'].max_axial('SC_B_PointForce'):.1e} N")
print(f"Expected: tension: (-) {F0} N")


