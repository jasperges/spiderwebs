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

from . import helpers
from . import curve_tools


class Spiderweb(bpy.types.Operator):
    """Add a spiderweb (or wires) between the selected objects"""
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
    seed = IntProperty(name="Seed",
                       description="The seed to use for the generation "
                                   "(change it to get a different variant "
                                   "of the web)",
                       default=0)
    drape_min = FloatProperty(name="Drape min",
                              description="The minimum drape of the strands",
                              default=-1.0,
                              soft_min=-50.0,
                              soft_max=50.0,
                              step=10)
    drape_max = FloatProperty(name="Drape max",
                              description="The maximum drape of the strands",
                              default=0,
                              soft_min=-50.0,
                              soft_max=50.0,
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
        box.prop(self, 'seed')
        box.prop(self, 'drape_min')
        box.prop(self, 'drape_max')
        box.prop(self, 'length_solver')

    # Poll
    @classmethod
    def poll(cls, context):
        if context.selected_objects:
            for obj in context.selected_objects:
                if obj.type == 'MESH':
                    return True

    # Helper functions
    def create_psystem(self, obj):
        name = "cobwebs"
        p_modifier = obj.modifiers.new(name, 'PARTICLE_SYSTEM')
        p_system = p_modifier.particle_system
        p_settings = p_system.settings
        p_system.name = p_settings.name = name
        p_system.seed = self.seed * 1979
        p_settings.count = self.amount
        p_settings.frame_start = p_settings.frame_end = 0
        p_settings.physics_type = 'NO'
        return p_system

    def join_objects(self, objects):
        scene = bpy.context.scene
        ctx = bpy.context.copy()
        # One of the objects to join.
        ctx['active_object'] = objects[0]
        ctx['selected_objects'] = objects
        # We need the scene bases as well for joining.
        ctx['selected_editable_bases'] = [scene.object_bases[obj.name] for obj in objects]
        bpy.ops.object.join(ctx)
        return objects[0]

    def spline_length(self, spline):
        # Only works for straight (sp)lines.
        return (spline.points[-1].co - spline.points[0].co).length

    def average_spline_length(self, curve):
        # Only works for straight (sp)lines.
        total_length = 0
        for spline in curve.splines:
            total_length += self.spline_length(spline)
        return total_length / len(curve.splines)

    def range_string_to_list(range_string):
        # !!!
        return

    def drape_web(self, curve, range_string=None):
        if not range_string:
            splines = curve.splines
        else:
            pass
        for i, spline in enumerate(splines):
            random.seed(self.seed + i * 100)
            drape = random.uniform(self.drape_min, self.drape_max)
            length = self.spline_length(spline)
            average_length = self.average_spline_length(curve)
            if self.length_solver:
                drape = length * drape / average_length
            spline.points[1].co.z += drape

    def pick_random_point_gauss(self, points, divide, i, sub_iter):
        points = list(points)
        max_index = len(points) - 1
        random.seed(self.seed * sub_iter * i * 33)
        point_index = int(random.gauss(max_index / 2, max_index / 2 / divide))
        # Just to be sure the index is not out of range
        point_index = max(0, min(len(points) - 1, point_index))
        return points[point_index]

    def get_mid_points(self, curve, divide, sub_iter):
        mid_points = []
        for i, _ in enumerate(curve.splines):
            points = curve_tools.get_nurbs_points(curve, i)
            mid_points.append(self.pick_random_point_gauss(points, divide, i, sub_iter))
        return mid_points

    # Execute
    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        old_objects = [obj for obj in selected_objects if obj.type == 'MESH']
        end_positions = []
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
        particle_object = self.join_objects(copy_objects)
        p_system = self.create_psystem(particle_object)
        # Update scene for particles to be there during script run
        scene.update()
        end_positions = [p.location for p in p_system.particles]

        # Step 3: Create "Main strands" using particles for end positions
        if not len(end_positions) > 1:
            return
        curve = bpy.data.curves.new("cobweb", 'CURVE')
        curve.dimensions = '3D'
        curve.fill_mode = 'FULL'
        for i in range(self.main_iterations):
            for ip, loc in enumerate(end_positions):
                points = end_positions[:]
                points.pop(ip)
                spline = curve.splines.new('NURBS')
                spline.points.add(count=2)
                loc1 = loc
                random.seed(self.seed + i * ip * 100)
                loc3 = random.choice(points)
                loc2 = loc + ((loc3 - loc) * .5)
                spline.points[0].co = loc1.to_4d()
                spline.points[1].co = loc2.to_4d()
                spline.points[2].co = loc3.to_4d()
                spline.use_endpoint_u = True
                spline.order_u = 3

        self.drape_web(curve)

        #Step 4: Create "Sub strands"
        if self.include_ends:
            divide = 3.8
        else:
            divide = 4
        curve_copy = curve.copy()
        for i in range(self.sub_iterations):
            mid_points = self.get_mid_points(curve_copy, divide, i)
            for ip, loc in enumerate(mid_points):
                points = mid_points[:]
                points.pop(ip)
                spline = curve.splines.new('NURBS')
                spline.points.add(count=2)
                loc1 = loc.to_3d()
                random.seed(self.seed + i * ip * 133)
                loc3 = random.choice(points).to_3d()
                loc2 = loc + ((loc3 - loc) * .5)
                spline.points[0].co = loc1.to_4d()
                spline.points[1].co = loc2.to_4d()
                spline.points[2].co = loc3.to_4d()
                spline.use_endpoint_u = True
                spline.order_u = 3

                # !!!TEMP DRAPE
                random.seed(self.seed + i * ip * 100)
                drape = random.uniform(self.drape_min, self.drape_max)
                length = self.spline_length(spline)
                average_length = self.average_spline_length(curve)
                if self.length_solver:
                    drape = length * drape / average_length
                spline.points[1].co.z += drape

        cobweb = bpy.data.objects.new("cobweb", curve)
        bpy.context.scene.objects.link(cobweb)
        # Delete the object with the particle system, we don't need it anymore.
        scene.objects.unlink(particle_object)
        bpy.data.objects.remove(particle_object)
        # Add some drape to the splines.
        # Select the cobweb and make it the active object.
        cobweb.select = True
        bpy.context.scene.objects.active = cobweb

        return {'FINISHED'}

    # Invoke
    def invoke(self, context, event):
        self.execute(context)

        return {'FINISHED'}
