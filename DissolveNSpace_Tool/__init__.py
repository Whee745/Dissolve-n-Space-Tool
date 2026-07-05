
import bpy
import bmesh


# ---------------------------------------------------------------------------
# Properties
# ---------------------------------------------------------------------------

class DissolveSpaceProperties(bpy.types.PropertyGroup):
    target_count: bpy.props.IntProperty(
        name="Target Verts",
        description="Vertex count the selection should reach after dissolve",
        default=5,
        min=2,
    )


# ---------------------------------------------------------------------------
# Core logic
# ---------------------------------------------------------------------------

def _dissolve_at_angle(obj, backup, selected_indices: list, angle_deg: float) -> int:
    """
    Restore mesh from *backup*, re-select *selected_indices*, run Limited
    Dissolve at *angle_deg*, and return the resulting selected vertex count.
    Helper — does NOT free backup.
    """
    import math

    bpy.ops.object.mode_set(mode='OBJECT')
    obj.data.clear_geometry()
    temp = backup.copy()
    temp.to_mesh(obj.data)
    temp.free()
    bpy.ops.object.mode_set(mode='EDIT')

    bm = bmesh.from_edit_mesh(obj.data)
    bm.verts.ensure_lookup_table()
    for v in bm.verts:
        v.select = v.index in selected_indices
    bmesh.update_edit_mesh(obj.data)

    bpy.ops.mesh.dissolve_limited(
        angle_limit=math.radians(angle_deg),
        use_dissolve_boundaries=False,
    )

    bm = bmesh.from_edit_mesh(obj.data)
    return sum(1 for v in bm.verts if v.select)


def run_limited_dissolve(target_count: int) -> bool:
    """
    Find the minimal angle limit that dissolves the selection down to
    *target_count* vertices (or fewer), using:

      Phase 1 — Exponential scan  : 0.5° → 1° → 2° → 4° … to locate the
                                     bracket [lo, hi] that straddles the target.
      Phase 2 — Binary search     : ~10 iterations to pin down the exact angle.

    Worst-case ~18 dissolve operations vs. ~720 for a 0.25° linear scan.
    Returns True on success, False if the target cannot be reached or
    preconditions are not met.
    """
    obj = bpy.context.active_object
    if not obj or obj.type != 'MESH' or obj.mode != 'EDIT':
        return False

    bm = bmesh.from_edit_mesh(obj.data)
    selected_indices = set(v.index for v in bm.verts if v.select)

    if not selected_indices:
        return False
    if len(selected_indices) <= target_count:
        return True  # Already small enough — nothing to do.

    # Back up mesh in Object mode so obj.data is fully synced.
    bpy.ops.object.mode_set(mode='OBJECT')
    backup = bmesh.new()
    backup.from_mesh(obj.data)
    bpy.ops.object.mode_set(mode='EDIT')

    MAX_ANGLE = 180.0
    success   = False

    # ------------------------------------------------------------------
    # Phase 1: exponential scan to bracket the answer
    # ------------------------------------------------------------------
    lo, hi = 0.0, 0.0
    angle  = 0.5                        # start at 0.5°

    while angle <= MAX_ANGLE:
        count = _dissolve_at_angle(obj, backup, selected_indices, angle)
        if count <= target_count:
            hi = angle
            lo = angle / 2.0            # previous step was lo
            break
        lo = angle
        angle *= 2.0                    # double each time: 0.5→1→2→4…
    else:
        # Even 180° wasn't enough — revert and give up.
        _dissolve_at_angle(obj, backup, selected_indices, 0.0)  # restores mesh
        backup.free()
        obj.data.update()
        return False

    # ------------------------------------------------------------------
    # Phase 2: binary search within [lo, hi]  (~10 iterations → 0.18° precision)
    # ------------------------------------------------------------------
    ITERATIONS = 10
    best_angle = hi

    for _ in range(ITERATIONS):
        mid   = (lo + hi) / 2.0
        count = _dissolve_at_angle(obj, backup, selected_indices, mid)
        if count <= target_count:
            best_angle = mid
            hi = mid                    # try a smaller angle
        else:
            lo = mid                    # need a larger angle

    # Apply the best angle found (mesh may already be at best_angle from
    # the last iteration, but re-apply to be certain).
    _dissolve_at_angle(obj, backup, selected_indices, best_angle)
    success = True

    backup.free()
    obj.data.update()
    return success


def run_space() -> bool:
    """Run LoopTools Space on the current selection. Returns False if the
    addon is not enabled."""
    try:
        bpy.ops.mesh.looptools_space(influence=100, input='selected', interpolation='cubic')
        return True
    except AttributeError:
        return False


# ---------------------------------------------------------------------------
# Operators
# ---------------------------------------------------------------------------

class MESH_OT_limited_dissolve_target(bpy.types.Operator):
    bl_idname  = "mesh.limited_dissolve_target"
    bl_label   = "Dissolve"
    bl_description = "Run only Limited Dissolve operation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.scene.dissolve_space_props.target_count
        if run_limited_dissolve(target):
            return {'FINISHED'}
        self.report({'WARNING'}, "Could not reach the target vertex count.")
        return {'CANCELLED'}


class MESH_OT_looptools_space_wrapper(bpy.types.Operator):
    bl_idname  = "mesh.looptools_space_wrapper"
    bl_label   = "Space"
    bl_description = "Run only Space operation"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        if run_space():
            return {'FINISHED'}
        self.report({'WARNING'}, "LoopTools add-on is not enabled.")
        return {'CANCELLED'}


class MESH_OT_solve_combined(bpy.types.Operator):
    bl_idname  = "mesh.solve_combined"
    bl_label   = "Solve n Space"
    bl_description = "Run Dissolve then Space in sequence"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        target = context.scene.dissolve_space_props.target_count

        if not run_limited_dissolve(target):
            self.report({'WARNING'}, "Could not reach the target vertex count.")
            return {'CANCELLED'}

        if not run_space():
            self.report({'WARNING'}, "Dissolve succeeded, but LoopTools Space failed.")
            return {'CANCELLED'}

        return {'FINISHED'}


# ---------------------------------------------------------------------------
# UI Panel
# ---------------------------------------------------------------------------

class VIEW3D_PT_dissolve_space_panel(bpy.types.Panel):
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Edit'
    bl_label       = "Dissolve & Space Tool"

    def draw(self, context):
        layout = self.layout
        props  = context.scene.dissolve_space_props

        layout.prop(props, "target_count")
        layout.separator()
        layout.operator("mesh.solve_combined", icon='PLAY')
        layout.separator()

        row = layout.row(align=True)
        row.operator("mesh.limited_dissolve_target")
        row.operator("mesh.looptools_space_wrapper")

        layout.separator()
        col = layout.column()
        col.scale_y = 0.6
        col.label(text="v2.3 by WheeNg")


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

classes = (
    DissolveSpaceProperties,
    MESH_OT_limited_dissolve_target,
    MESH_OT_looptools_space_wrapper,
    MESH_OT_solve_combined,
    VIEW3D_PT_dissolve_space_panel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.dissolve_space_props = bpy.props.PointerProperty(type=DissolveSpaceProperties)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.dissolve_space_props

if __name__ == "__main__":
    register()
