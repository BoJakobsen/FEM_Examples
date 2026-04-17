import numpy as np
from Pynite import FEModel3D
from Pynite.Rendering import Renderer

# (x,y) is in the plane, z vertical. 
# Define cylindrical geometry in the (x,z) plane

# If no singular top point is used, remove all "exception" relating to NTOP

# Define nodes
xs = []

zs = []

# Effective weight in notes
ws = []


# Index for top and bottom
NTOP = 
NBOT = 


MSEG = # Number of segments in cylinder
angs = list(range(0,360,int(360/MSEG)))
MOTER =  #Selected point for roler support 

# Definer members
beams = []


# Model objekt
model = FEModel3D()

# Material parameter
E  = 200e9      # [Pa]  
model.add_material('Steel', E, 1, 1, 1)

A_bar = 1e-2    # [m²] 
model.add_section('Sec', A_bar, 1, 1, 1)


# Generate  nodes
for m, p in enumerate(angs):
    for n, (nx, nz) in enumerate(zip(xs,zs)):
        if n != NTOP:
            r = nx
            xp = np.sin(p/180*np.pi)*r
            yp = np.cos(p/180*np.pi)*r
            model.add_node(f'N{m}_{n}',xp , yp, nz)

model.add_node(f'N{0}_{NTOP}',xs[NTOP] , 0, zs[NTOP])

# Generate members vertically
for m, _ in enumerate(angs):
    for n, (bi, bj) in enumerate(beams):
        if bi == NTOP:
            model.add_member(f'Mer{m}_{n}',
                         f'N{0}_{bi}', f'N{m}_{bj}',
                         'Steel', 'Sec')
        elif bj == NTOP:
            model.add_member(f'Mer{m}_{n}',
                         f'N{m}_{bi}', f'N{0}_{bj}',
                         'Steel', 'Sec')
        else:
            model.add_member(f'Mer{m}_{n}',
                         f'N{m}_{bi}', f'N{m}_{bj}',
                         'Steel', 'Sec')


# Generate members horizontally
for m, _ in list(enumerate(angs)):
    for n, _ in enumerate(xs):
        if n != NTOP:
            model.add_member(f'Hoop{m}_{n}',
                f'N{m}_{n}', f'N{(m+1)%MSEG}_{n}',
                'Steel', 'Sec')


#  Fix rotational DOF 
for name in model.nodes:
        model.def_support(name, False, False, False, True, True, True)

# Fix bottom
for i in range(MSEG):
    model.def_support(f'N{i}_{NBOT}', False, False, True, True, True, True)

# Total fix 0 
model.def_support(f'N0_{NBOT}', True, True, True, True, True, True)

# Fix Y for other side
model.def_support(f'N{MOTER}_{NBOT}', False, True, True, True, True, True)

# Truss
for name in model.members:
    model.def_releases(name,
        False, False, False, False, True, True,   # i-end
        False, False, False, False, True, True)   # j-end

# Weights
for p in range(MSEG):
    for n, nw in enumerate(ws):
        if n != NTOP:
            model.add_node_load(f'N{p}_{n}', 'FZ', -nw)
model.add_node_load(f'N{0}_{NTOP}', 'FZ', -ws[NTOP])

# Analyze
model.analyze(log=True)


print("Members in x,z plane ")
for n, (bi, bj) in enumerate(beams):
    print(f"Connecting {bi}-{bj} : {model.members[f'Mer{0}_{n}'].max_axial():3.3f}")


print("Hoop forces")
print("            : Member  Radial")
for n,z in enumerate(zs):
    if n != NTOP:
        print(f"Højde {z:.3f} : {model.members[f'Hoop{0}_{n}'].max_axial():3.3f} ",
        f"{model.members[f'Hoop{0}_{n}'].max_axial()*2 * np.sin(np.pi / MSEG)  :3.3f}")


# Visualization (if you have vtk installed)
# Very slow if large model
if False:
    renderer = Renderer(model)
    renderer.render_loads = True
    # renderer.case = 'Case 1'
    #renderer.annotation_size = 6
    #renderer.deformed_shape = True
    #renderer.deformed_scale = 1 # 30 is default
    renderer.render_model()
