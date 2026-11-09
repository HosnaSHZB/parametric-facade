# ============================================================
# WAVY WOODEN LOUVER FACADE
# Rhino 7 + Grasshopper + GhPython
#
# INPUTS:
# S, H, Spacing, LouverWidth, Thickness,
# WaveAmp, WaveCount, ArchHeight, CornerWidth
#
# OUTPUTS:
# FacadeLouvers, CornerPosts, GuideLines
# ============================================================
# ------------------------------------------------------------
# 1. IMPORT LIBRARIES
# ------------------------------------------------------------

import Rhino
import Rhino.Geometry as rg
import math

# ------------------------------------------------------------
# 2. SET DEFAULT INPUT VALUES
# ------------------------------------------------------------

# Square building footprint dimension
if S is None:
    S = 8.0

# Overall facade height
if H is None:
    H = 5.0

# Distance between louver centerlines
if Spacing is None:
    Spacing = 0.15

# Width of individual wooden louvers
if LouverWidth is None:
    LouverWidth = 0.07

# Thickness of wooden louvers
if Thickness is None:
    Thickness = 0.12

# Maximum horizontal wave displacement
if WaveAmp is None:
    WaveAmp = 0.50

# Number of waves around the perimeter
if WaveCount is None:
    WaveCount = 4

# Maximum height of the bottom arch
if ArchHeight is None:
    ArchHeight = 1.60

# Width of the four corner elements
if CornerWidth is None:
    CornerWidth = 0.25


# ------------------------------------------------------------
# 3. VALIDATE INPUTS
# ------------------------------------------------------------

# Convert dimensions to floating point numbers
S = max(0.1, float(S))
H = max(0.1, float(H))
Spacing = max(0.01, float(Spacing))
LouverWidth = max(0.005, float(LouverWidth))
Thickness = max(0.005, float(Thickness))
WaveAmp = max(0.0, float(WaveAmp))
ArchHeight = max(0.0, float(ArchHeight))
CornerWidth = max(0.01, float(CornerWidth))

# Convert wave count to integer
WaveCount = max(1, int(WaveCount))

# Ensure the bottom opening does not exceed facade height
ArchHeight = min(ArchHeight, H * 0.85)

# Calculate half of the square footprint
half = S / 2.0

# Calculate total perimeter
perimeter = 4.0 * S

# Set Rhino document tolerance
try:
    tol = Rhino.RhinoDoc.ActiveDoc.ModelAbsoluteTolerance
except:
    tol = 0.01

angle_tol = math.radians(1.0)


# ------------------------------------------------------------
# 4. INITIALIZE OUTPUT COLLECTIONS
# ------------------------------------------------------------

# Collection for the individual facade louvers
FacadeLouvers = []

# Collection for the four corner posts
CornerPosts = []

# Collection for reference guide curves
GuideLines = []


# ------------------------------------------------------------
# 5. DEFINE THE FOUR FACADE DIRECTIONS
# ------------------------------------------------------------

# Each facade has:
# Start point
# Tangent direction
# Outward direction
#
# The four facades are arranged clockwise around the square.

facades = [

    # SOUTH FACADE
    {
        "start": rg.Point3d(-half, -half, 0),
        "tangent": rg.Vector3d(1, 0, 0),
        "outward": rg.Vector3d(0, -1, 0)
    },

    # EAST FACADE
    {
        "start": rg.Point3d(half, -half, 0),
        "tangent": rg.Vector3d(0, 1, 0),
        "outward": rg.Vector3d(1, 0, 0)
    },

    # NORTH FACADE
    {
        "start": rg.Point3d(half, half, 0),
        "tangent": rg.Vector3d(-1, 0, 0),
        "outward": rg.Vector3d(0, 1, 0)
    },

    # WEST FACADE
    {
        "start": rg.Point3d(-half, half, 0),
        "tangent": rg.Vector3d(0, -1, 0),
        "outward": rg.Vector3d(-1, 0, 0)
    }

]


# ------------------------------------------------------------
# 6. DEFINE WAVE DEFORMATION FUNCTION
# ------------------------------------------------------------

# The wave function moves each louver inward or outward.
#
# The displacement changes along the entire perimeter.
# This produces the organic undulating facade.

def wave_function(global_position):

    # Convert the perimeter position to a normalized value.
    u = global_position / perimeter

    # Calculate sinusoidal displacement.
    wave = WaveAmp * math.sin(
        2.0 * math.pi * WaveCount * u
    )

    return wave


# ------------------------------------------------------------
# 7. DEFINE THE ARCH FUNCTION
# ------------------------------------------------------------

# Each facade has an arched lower edge.
#
# At the two ends of each facade:
# Bottom height = 0
#
# At the middle of each facade:
# Bottom height = ArchHeight
#
# This creates openings below the facade louvers.

def arch_function(t):

    # Calculate sinusoidal bottom elevation.
    z_bottom = ArchHeight * math.sin(math.pi * t)

    return z_bottom


# ------------------------------------------------------------
# 8. GENERATE THE VERTICAL WOODEN LOUVERS
# ------------------------------------------------------------

# Loop through all four facades.
for side_index in range(4):

    # Get the current facade data.
    facade = facades[side_index]

    # Extract the starting point.
    start = facade["start"]

    # Extract the facade tangent direction.
    tangent = facade["tangent"]

    # Extract the outward direction.
    outward = facade["outward"]

    # Calculate the number of louvers on this facade.
    # The spacing is adjusted slightly to distribute them evenly.
    count = max(2, int(math.ceil(S / Spacing)))

    # Calculate actual center-to-center spacing.
    actual_spacing = S / float(count)

    # Calculate the local inward direction.
    # This is used as the second plane axis.
    inward = rg.Vector3d(
        -outward.X,
        -outward.Y,
        0
    )

    # Create a local construction plane.
    # Its Z direction is vertical.
    facade_plane = rg.Plane(
        start,
        tangent,
        inward
    )

    # Loop through all louver positions.
    for i in range(count):

        # Calculate normalized position along this facade.
        # Half-spacing offset avoids duplicating corner louvers.
        t = (i + 0.5) / float(count)

        # Calculate global perimeter position.
        global_position = side_index * S + t * S

        # Calculate horizontal wave displacement.
        displacement = wave_function(global_position)

        # Calculate the bottom elevation of this louver.
        bottom_z = arch_function(t)

        # Calculate its base position on the facade.
        base_point = rg.Point3d(
            start.X + tangent.X * t * S,
            start.Y + tangent.Y * t * S,
            0
        )

        # Move the louver inward or outward.
        base_point = rg.Point3d(
            base_point.X + outward.X * displacement,
            base_point.Y + outward.Y * displacement,
            0
        )

        # Create a local plane for the louver.
        # X axis = horizontal facade direction.
        # Y axis = inward direction.
        # Z axis = vertical direction.
        louver_plane = rg.Plane(
            base_point,
            tangent,
            inward
        )

        # Define the louver's width.
        x_interval = rg.Interval(
            -LouverWidth / 2.0,
            LouverWidth / 2.0
        )

        # Define the louver's thickness.
        y_interval = rg.Interval(
            -Thickness / 2.0,
            Thickness / 2.0
        )

        # Define its vertical height.
        z_interval = rg.Interval(
            bottom_z,
            H
        )

        # Construct a solid rectangular wooden louver.
        louver_box = rg.Box(
            louver_plane,
            x_interval,
            y_interval,
            z_interval
        )

        # Convert the box to a closed Brep.
        louver_brep = louver_box.ToBrep()

        # Add the Brep to the facade collection.
        if louver_brep is not None:
            FacadeLouvers.append(louver_brep)


# ------------------------------------------------------------
# 9. GENERATE THE FOUR CORNER POSTS
# ------------------------------------------------------------

# These four elements are separate from the regular louvers.
#
# They extend from ground level to the full facade height.
# They are positioned exactly at the four footprint corners.

corner_points = [

    rg.Point3d(-half, -half, 0),
    rg.Point3d(half, -half, 0),
    rg.Point3d(half, half, 0),
    rg.Point3d(-half, half, 0)

]

# Create a horizontal construction plane.
world_plane = rg.Plane.WorldXY

# Loop through the four corners.
for corner in corner_points:

    # Move the center inward by half the corner width.
    # This keeps each square post inside the footprint.
    sx = 1.0 if corner.X > 0 else -1.0
    sy = 1.0 if corner.Y > 0 else -1.0

    corner_center = rg.Point3d(
        corner.X - sx * CornerWidth / 2.0,
        corner.Y - sy * CornerWidth / 2.0,
        0
    )

    # Create a local plane at the corner post position.
    corner_plane = rg.Plane(
        corner_center,
        rg.Vector3d.XAxis,
        rg.Vector3d.YAxis
    )

    # Define horizontal width.
    corner_x = rg.Interval(
        -CornerWidth / 2.0,
        CornerWidth / 2.0
    )

    # Define horizontal depth.
    corner_y = rg.Interval(
        -CornerWidth / 2.0,
        CornerWidth / 2.0
    )

    # Extend the corner post from ground to facade top.
    corner_z = rg.Interval(
        0,
        H
    )

    # Create the solid corner post.
    corner_box = rg.Box(
        corner_plane,
        corner_x,
        corner_y,
        corner_z
    )

    # Convert to Brep geometry.
    corner_brep = corner_box.ToBrep()

    # Add to the corner collection.
    if corner_brep is not None:
        CornerPosts.append(corner_brep)


# ------------------------------------------------------------
# 10. GENERATE FACADE GUIDE CURVES
# ------------------------------------------------------------

# These curves are reference geometry only.
# They do not create walls or building elements.

for side_index in range(4):

    # Retrieve the facade information.
    facade = facades[side_index]

    start = facade["start"]
    tangent = facade["tangent"]

    # Create points along the bottom arch.
    arch_points = []

    # Sample the arch with 40 segments.
    for i in range(41):

        t = float(i) / 40.0

        # Calculate bottom height.
        z = arch_function(t)

        # Calculate XY position.
        x = start.X + tangent.X * t * S
        y = start.Y + tangent.Y * t * S

        # Add point to arch curve.
        arch_points.append(
            rg.Point3d(x, y, z)
        )

    # Convert points into a polyline curve.
    arch_curve = rg.PolylineCurve(arch_points)

    # Add arch curve to guide collection.
    GuideLines.append(arch_curve)


# ------------------------------------------------------------
# 11. CREATE THE TOP PERIMETER GUIDE
# ------------------------------------------------------------

# Create the square perimeter at the top of the facade.

top_points = [

    rg.Point3d(-half, -half, H),
    rg.Point3d(half, -half, H),
    rg.Point3d(half, half, H),
    rg.Point3d(-half, half, H),
    rg.Point3d(-half, -half, H)

]

# Create a closed polyline for the top perimeter.
top_curve = rg.PolylineCurve(top_points)

# Add it to the guide collection.
GuideLines.append(top_curve)


# ------------------------------------------------------------
# 12. FINAL OUTPUTS
# ------------------------------------------------------------
# FacadeLouvers:
# Individual rectangular wooden vertical fins.
# CornerPosts:
# Four solid corner elements touching ground level.
# GuideLines:
# Four lower arch curves and one upper perimeter curve.
