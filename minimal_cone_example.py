"""
Cone — a minimal rotational symmetric structural analysis example
=====================================================

A simple cone analyzed as a truss network

This cone model is a minimal example demonstrating how to make
rotational symmetric truss models of cones and similar shapes.
2 hoops (rings) of nodes connected by meridian bars,
plus a single apex node.

Geometry (cross-section through the axis):

          apex (0, 0, H)
          /|\
         / | \          The cone has base radius R and height H.
        /  |  \
       /   |   \
      /    |    \
     / ring 1    \      Two hoops divide the cone into strips.
    /      |      \     Each hoop is a regular polygon.
   /       |       \
  /   ring 0        \
 /______|__|________ \
         base

Loading comes from the weight of a thin shell covering the cone surface.
The shell area are calculated analytically and distributed
at vertical point loads on the nodes.

"""

import numpy as np
from Pynite import FEModel3D


# Geometry of the cone
R = 1.0      # Base radius [m]
H = 1.0      # Height [m]
NSEG = 6     # Sides per hoop

# Slant height of the full cone:
#   L = sqrt(R² + H²)
L_slant = np.sqrt(R**2 + H**2)

# The two hoops divide the cone into 3 zones (2 strips + apex cap).
# The are placed at equal spacing along the height:
#   Ring 0 (base):   z = 0,    r = R
#   Ring 1 (middle): z = H/2,  r = R/2   (r = R·(1 - z/H))
#   Apex:            z = H,    r = 0

z_rings = np.array([0.0, H / 2])        # heights of ring 0 and ring 1
r_rings = R * (1 - z_rings / H)          # radii:  [R, R/2]


# Shell surface area for a cone

# The cone surface between two heights is a "frustum" (truncated cone).
# Its lateral surface area is:
#
#     A_frustum = pi · (r_lower + r_upper) · s
#
# where s is the slant height of the strip:
#
#     s = sqrt( (r_lower - r_upper)² + (z_upper - z_lower)² )
#

# The full list of levels from base to apex:
r_levels = np.array([r_rings[0], r_rings[1], 0.0])   # [R, R/2, 0]
z_levels = np.array([z_rings[0], z_rings[1], H])      # [0, H/2, H]

# Compute the area of each strip
n_strips = len(r_levels) - 1   # = 2 strips
strip_areas = np.zeros(n_strips)

print("=== Strip areas (analytical) ===")
for k in range(n_strips):
    dr = r_levels[k] - r_levels[k + 1]
    dz = z_levels[k + 1] - z_levels[k]
    s = np.sqrt(dr**2 + dz**2)                          
    strip_areas[k] = np.pi * (r_levels[k] + r_levels[k + 1]) * s
    print(f"  Strip {k}: r = [{r_levels[k]:.2f}, {r_levels[k+1]:.2f}], "
          f"s = {s:.4f} m, A = {strip_areas[k]:.4f} m²")

# Check: total should equal the full cone lateral area = pi·R·L
A_total_analytical = np.pi * R * L_slant
print(f"  Sum of strips:    {np.sum(strip_areas):.4f} m²")
print(f"  Exact full cone:  {A_total_analytical:.4f} m²")

# Distribute strip areas to nodes using the tributary area idea:
# each strip is shared 50/50 between its upper and lower ring.
# Then each node in a ring gets 1/NSEG of that ring's share.
level_areas = np.zeros(len(r_levels))   # [base, middle, apex]
for k in range(n_strips):
    level_areas[k]     += strip_areas[k] / 2    # lower ring gets half
    level_areas[k + 1] += strip_areas[k] / 2    # upper ring gets half

ring0_node_area = level_areas[0] / NSEG    # per node in base ring
ring1_node_area = level_areas[1] / NSEG    # per node in middle ring
apex_node_area  = level_areas[2]           # apex is a single node

print(f"\n=== Tributary areas per node ===")
print(f"  Ring 0 (base):   {ring0_node_area:.4f} m²/node  "
      f"(× {NSEG} nodes = {level_areas[0]:.4f} m²)")
print(f"  Ring 1 (middle): {ring1_node_area:.4f} m²/node  "
      f"(× {NSEG} nodes = {level_areas[1]:.4f} m²)")
print(f"  Apex:            {apex_node_area:.4f} m²  (single node)")


# Shell weight

# Weight per unit area of the shell surface:
#   q = density × gravity × thickness    [N/m²]

rho_mass = 8000     # [kg/m³]  (steel)
g_accel  = 9.81     # [m/s²]
t_shell  = 0.01     # [m]  (10 mm thick shell)

q = rho_mass * g_accel * t_shell    # ≈ 785 N/m²

# Point loads at each node = q × tributary area
F_ring0 = q * ring0_node_area    # [N] per node in ring 0
F_ring1 = q * ring1_node_area    # [N] per node in ring 1
F_apex  = q * apex_node_area     # [N] at apex

total_load = F_ring0 * NSEG + F_ring1 * NSEG + F_apex
print(f"\n=== Loading ===")
print(f"  q = {q:.1f} N/m²")
print(f"  F per base node:   {F_ring0:.2f} N")
print(f"  F per middle node: {F_ring1:.2f} N")
print(f"  F at apex:         {F_apex:.2f} N")
print(f"  Total load:        {total_load:.2f} N")


# Build the PyNite model
model = FEModel3D()

# Material
# For a truss only E and A matter.  G, nu are required by PyNite but
# don't affect the results for a truss model
E  = 200e9      # [Pa]  Young's modulus (steel)
G  = 80e9       # [Pa]  shear modulus (unused for truss)
nu = 0.25       # [-]   Poisson's ratio (unused for truss)
model.add_material('Steel', E, G, nu, 0)   # rho=0: we apply loads manually

# Section
# Only A matters for a truss.  Iy, Iz, J are placeholders.
A_bar = 1e-2    # [m²] cross-section of each bar
model.add_section('Sec', A_bar, 1, 1, 1)

# Nodes
# Ring 0 (base): hexagon at z=0, radius R
# Ring 1 (middle): hexagon at z=H/2, radius R/2
for ring_idx, (r, z) in enumerate(zip(r_rings, z_rings)):
    for i in range(NSEG):
        theta = 2 * np.pi / NSEG * i
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        if abs(x) < 1e-10: x = 0.0
        if abs(y) < 1e-10: y = 0.0
        model.add_node(f'N{ring_idx}_{i}', x, y, z)

# Apex: single node
model.add_node('Napex', 0, 0, H)

# Members
# Hoop members: connect adjacent nodes within each ring
for ring_idx in range(len(r_rings)):
    for i in range(NSEG):
        j = (i + 1) % NSEG    # next node; wraps around to close the ring
        model.add_member(f'Hoop_{ring_idx}_{i}',
                         f'N{ring_idx}_{i}', f'N{ring_idx}_{j}',
                         'Steel', 'Sec')

# Meridian members: connect each node to the corresponding node one ring up
# Ring 0 → Ring 1
for i in range(NSEG):
    model.add_member(f'Mer_0_{i}',
                     f'N0_{i}', f'N1_{i}',
                     'Steel', 'Sec')

# Ring 1 → Apex (all nodes connect to the single apex)
for i in range(NSEG):
    model.add_member(f'Mer_1_{i}',
                     f'N1_{i}', 'Napex',
                     'Steel', 'Sec')


# Supports

# Base fix vertical displacement (DZ) everywhere.
# Also need to prevent rigid body sliding (DX, DY) and spinning (RZ).
# One node is fully pinned and one opposite node pined in Y (prevents spin).
# Under symmetric loading these extra constraints carry zero reaction.
for i in range(NSEG):
    model.def_support(f'N0_{i}', False, False, True, True, True, True)

# Pin one base node fully
model.def_support('N0_0', True, True, True, True, True, True)

# Fix Y on the opposite node to prevent rigid body spin
model.def_support(f'N0_{NSEG // 2}', False, True, True, True, True, True)

# For Truss elements we need to fix all rotation DOF (already done for the base) 
for name in model.nodes:
    node = model.nodes[name]
    is_supported = any([node.support_DX, node.support_DY, node.support_DZ,
                        node.support_RX, node.support_RY, node.support_RZ])
    if not is_supported:
        model.def_support(name, False, False, False, True, True, True)

# Truss: release moments + constrain unused rotational DOFs
# Release bending at both ends of every member → pin-jointed truss
for name in model.members:
    model.def_releases(name,
        False, False, False, False, True, True,   # i-end
        False, False, False, False, True, True)   # j-end




# Apply loads
for i in range(NSEG):
    model.add_node_load(f'N0_{i}', 'FZ', -F_ring0)
    model.add_node_load(f'N1_{i}', 'FZ', -F_ring1)
model.add_node_load('Napex', 'FZ', -F_apex)

# Solve
model.analyze()


# Results
print("\n" + "=" * 55)
print(f"Cone :  R = {R} m,  H = {H} m,  {NSEG}-sided polygons")
print("=" * 55)

# Hoop forces
print(f"\n{'Ring':>4}  {'z [m]':>6}  {'r [m]':>6}  {'Hoop [N]':>10}  {'Type':>12}")
print("-" * 55)
for ring_idx in range(len(r_rings)):
    axial = model.members[f'Hoop_{ring_idx}_0'].max_axial()
    kind = "COMPRESSION" if axial > 0 else "TENSION"
    print(f"{ring_idx:>4}  {z_rings[ring_idx]:>6.2f}  {r_rings[ring_idx]:>6.2f}  "
          f"{axial:>10.4f}  {kind:>12}")

# Meridian forces
print(f"\n{'Span':>8}  {'Meridian [N]':>12}")
print("-" * 55)
for ring_idx in range(len(r_rings)):
    axial = model.members[f'Mer_{ring_idx}_0'].max_axial()
    label = f"Ring {ring_idx} → {'Ring 1' if ring_idx == 0 else 'Apex'}"
    print(f"  {label:<20s}  {axial:>12.4f}")

# Reactions
print(f"\n{'Node':>8}  {'Fz reaction [N]':>16}")
print("-" * 55)
Fz_total = 0
for i in range(NSEG):
    Fz = model.nodes[f'N0_{i}'].RxnFZ['Combo 1']
    Fz_total += Fz
    print(f"  N0_{i}:    {Fz:>12.4f}")
print(f"  {'Sum:':>7}  {Fz_total:>12.4f}  (should equal total load {total_load:.2f})")


