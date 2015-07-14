# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# Import modules.
import random
import bpy
from bpy.props import (IntProperty,
                       FloatProperty,
                       BoolProperty)


def create_psystem(obj, count):
    name = "cobwebs"
    p_modifier = obj.modifiers.new(name, 'PARTICLE_SYSTEM')
    p_system = p_modifier.particle_system
    p_settings = p_system.settings
    p_system.name = p_settings.name = name
    # p_system.seed = seed
    p_settings.count = count
    p_settings.frame_start = p_settings.frame_end = 0
    p_settings.physics_type = 'NO'
    # p_locations = [p.location for p in p_system.particles]
    # obj.modifiers.remove(p_modifier)
    # return p_locations
    return p_system


def join_objects(objects):
    scene = bpy.context.scene
    ctx = bpy.context.copy()
    # one of the objects to join
    ctx['active_object'] = objects[0]
    ctx['selected_objects'] = objects
    # we need the scene bases as well for joining
    ctx['selected_editable_bases'] = [scene.object_bases[obj.name] for obj in objects]
    bpy.ops.object.join(ctx)
    return objects[0]


def main(context, self):
    selected_objects = bpy.context.selected_objects
    old_objects = [obj for obj in selected_objects if obj.type == 'MESH']
    end_positions = []
    num_main_strands = self.amount
    main_iter = self.main_iterations
    # sub_iter = self.sub_iterations

    scene = context.scene

    # Step 1 + 2: Create particles to use for 'main strand' end positions
    #             Collect the locations of all particles
    if not old_objects:
        return
    # Make a copy of the selected objects and join them
    copy_objects = [obj.copy() for obj in old_objects]
    for obj in copy_objects:
        obj.data = obj.data.copy()
        scene.objects.link(obj)
    particle_object = join_objects(copy_objects)
    p_system = create_psystem(particle_object, num_main_strands)
    # Update scene for particles to be there during script run
    scene.update()
    end_positions = [p.location for p in p_system.particles]

    # Step 3: Create "Main strands" using particles for end positions
    if not len(end_positions) > 1:
        return
    curve = bpy.data.curves.new("cobweb", 'CURVE')
    curve.dimensions = '3D'
    curve.fill_mode = 'FULL'
    for _ in range(main_iter):
        for i, loc in enumerate(end_positions):
            points = end_positions[:]
            points.pop(i)
            spline = curve.splines.new('NURBS')
            spline.points.add(count=3)
            loc1 = loc
            loc4 = random.choice(points)
            loc2 = loc1 + (loc4 - loc1) * .3
            loc3 = loc1 + (loc4 - loc1) * .6
            # loc2.z -= random.random() * 2 + .2
            # loc3.z -= random.random() * 2 + .2
            spline.points[0].co = loc1.to_4d()
            spline.points[1].co = loc2.to_4d()
            spline.points[2].co = loc3.to_4d()
            spline.points[3].co = loc4.to_4d()
            spline.use_endpoint_u = True
            spline.order_u = 4
    cobweb = bpy.data.objects.new("cobweb", curve)
    bpy.context.scene.objects.link(cobweb)

    scene.objects.unlink(particle_object)
    bpy.data.objects.remove(particle_object)


class Spiderweb(bpy.types.Operator):
    """Add a spiderweb (or wires) between the selected objects."""
    bl_idname = "curve.spiderweb"
    bl_label = "Create spiderweb"
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    def __init__(self):
        # Because creating a lot of wires can take some time and slow down the
        # viewport, set the initial amount of wires to 50 if it is higher.
        if self.amount > 50:
            self.amount = 50

    amount = IntProperty(name="Amount",
                         description="The number of wires to create",
                         default=20,
                         min=2,
                         max=999999,
                         soft_max=100)
    main_iterations = IntProperty(name="Iterations",
                                  description="Iterations",
                                  default=1,
                                  min=1,
                                  max=100)
    include_ends = BoolProperty(name="Include ends",
                                description="Include ends",
                                default=True)
    sub_iterations = IntProperty(name="Iterations",
                                 description="Iterations",
                                 default=3,
                                 min=0,
                                 max=999999,
                                 soft_max=100)
    drape_min = FloatProperty(name="Drape min",
                              description="The minimum drape of the strands",
                              default=-1.0,
                              soft_min=-10.0,
                              soft_max=10.0,
                              step=10)
    drape_max = FloatProperty(name="Drape max",
                              description="The maximum drape of the strands",
                              default=0,
                              soft_min=-10.0,
                              soft_max=10.0,
                              step=10)
    length_solver = BoolProperty(name="Length solver",
                                 description="Length solver",
                                 default=True)

    # Draw
    def draw(self, context):
        layout = self.layout

        # Options
        box = layout.box()
        box.label(text="Main strands")
        box.prop(self, 'amount')
        box.prop(self, 'main_iterations')
        box = layout.box()
        box.label(text="Sub strands")
        box.prop(self, 'include_ends')
        box.prop(self, 'sub_iterations')
        box = layout.box()
        box.prop(self, 'drape_min')
        box.prop(self, 'drape_max')
        box.prop(self, 'length_solver')

    # Poll
    @classmethod
    def poll(cls, context):
        return (context.selected_objects and
                context.scene.active_object.type == 'MESH')

    # Execute
    def execute(self, context):
        # Run main function.
        main(context, self)

        return {'FINISHED'}

    # Invoke
    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}
