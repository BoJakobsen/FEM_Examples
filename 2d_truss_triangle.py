"""
2D Triangle Truss 
========================================================
A single triangle with three bars, two supports and one external load.

This example can easily be solved by hand using the method of joints.

All z coordinates set to 0 as this is a 2D model.

Also demonstrate how to used 2d truss in Pynite

All material and section parameters are set to 1 for simplicity.
"""

from Pynite import FEModel3D
import numpy as np


# Create model object
model = FEModel3D()

# Material definition

# All set to 1 for simplicity 
E  = 1       # Young's modulus  [force/area]
G  = 1       # Shear modulus    [force/area]  
nu = 0.3     # Poisson's ratio  [-]           
rho = 0      # Weight density   [force/volume] — set to 0: no self-weight

model.add_material('Mat', E, G, nu, rho)


# Cross-section definition

# A beam element in PyNite needs four section properties:
#   A  — cross-sectional area [m²]:  determines axial stiffness (EA)
#   Iy — second moment of area about local y-axis [m⁴]: bending stiffness (EI_y)
#   Iz — second moment of area about local z-axis [m⁴]: bending stiffness (EI_z)
#   J  — torsional constant [m⁴]: torsional stiffness (GJ)
#
# Only A matters in this example because it uses truss elements.
# The product EA is the axial stiffness of a bar 

A  = 1       # Cross-section area [area]

# Second moments of area (Iy, Iz) and torsion constant (J) are needed
# for the section definition, Iy,Yz need to be non-zero for solver to work
Iy = 1
Iz = 1
J  = 0

model.add_section('Sec', A, Iy, Iz, J)


# Build and "solve" the model

# Nodes (name, X, Y, Z)
model.add_node('N1', 0, 0, 0)
model.add_node('N2', 2, 0, 0)
model.add_node('N3', 1, 1, 0)

# Members (bars) 
model.add_member('M1', 'N1', 'N2', 'Mat', 'Sec')   # bottom horizontal
model.add_member('M2', 'N2', 'N3', 'Mat', 'Sec')   # right diagonal
model.add_member('M3', 'N1', 'N3', 'Mat', 'Sec')   # left diagonal

# Supports
# Each support definition handles 6 DOF.
# DX, DY, DZ  (translations)  and  RX, RY, RZ  (rotations)
# True = fixed (that DOF is constrained), False = free.

# Fix DZ and all rotations everywhere to enforce a 2D truss in XY.
# In-plane, N1 is a pin (DX, DY fixed) and N2 is a roller (DY fixed).
model.def_support('N1', True,  True,  True, True, True, True)  # pin
model.def_support('N2', False, True,  True, True, True, True)  # roller
model.def_support('N3', False, False, True, True, True, True)  # free, but locked in Z

# Release bending moments
# Truss's are achieved by releasing the bending rotations (Ry, Rz) at both
# ends of every member.

# def_releases(member,
#     Dxi, Dyi, Dzi, Rxi, Ryi, Rzi,   ← Start node
#     Dxj, Dyj, Dzj, Rxj, Ryj, Rzj)   ← End node
for m in model.members.keys(): # loop over all members
    model.def_releases(m,
        False, False, False, False, True, True,   # i-end: release Ry, Rz
        False, False, False, False, True, True)   # j-end: release Ry, Rz


# Apply external load
# A unit downward force on the free node N3.
Fload = -1
model.add_node_load('N3', 'FY', Fload)


# Solve

model.analyze()



# Results

# Reaction forces at supports
print("=== Reactions ===")
for name in ['N1', 'N2']:
    n = model.nodes[name]
    Fx = n.RxnFX['Combo 1']
    Fy = n.RxnFY['Combo 1']
    print(f"  {name}:  Fx = {Fx:.3f},  Fy = {Fy:+.3f}")
print(f"Expected sum Fy = -Fload = {-Fload} ")
print(f"Expected sum Fx = 0 ")

# Axial forces
# PyNite sign: positive = compression, negative = tension.

print("\n=== Axial forces (PyNite: + = compression, − = tension) ===")
for name in ['M1', 'M2', 'M3']:
    mbr = model.members[name]
    N = mbr.max_axial('Combo 1')
    print(f"  {name}:  N = {N:+.4f} ")
print(f" Expected from Method of joints. M1:  -0.5, M2: {np.sqrt(2)/2:.4f}, M3: {np.sqrt(2)/2:.4f}")

# Nodal displacements
print("\n=== Displacements ===")
for name in ['N1', 'N2', 'N3']:
    n = model.nodes[name]
    dx = n.DX['Combo 1']
    dy = n.DY['Combo 1']
    print(f"  {name}:  dx = {dx:+.6f},  dy = {dy:+.6f}")


# Rotations (should be zero for a truss)
print("\n=== Rotations===")
for name in ['N1', 'N2', 'N3']:
    theta = model.nodes[name].RZ['Combo 1']
    print(f"  {name}:  θz = {theta:.6f} rad")
print("Expected 0 for truss")
