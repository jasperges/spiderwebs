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


import math
import random
import bpy
import bpy_extras.mesh_utils
from mathutils import Vector


def get_random_points_on_verts(mesh, amount, transform_matrix):
    """
    get_random_points_on_verts(mesh mesh, int amount, matrix transform_matrix)
            -> list of vector points

        Gets <amount> number of random vert coordinates.

        mesh mesh               - the mesh to get the points from
        int amount              - the amount of points to return
        matrix transform_matrix - the matrix to transform the points by
    """

    points = []
    for _ in range(amount):
        points.append(transform_matrix * random.choice(mesh.vertices).co)

    return points


def get_random_points_on_edges(mesh, amount, transform_matrix):
    """
    get_random_points_on_edges(mesh mesh, int amount, matrix transform_matrix)
            -> list of vector points

        Gets <amount> number of random points on the edges of the mesh.

        mesh mesh               - the mesh to get the points from
        int amount              - the amount of points to return
        matrix transform_matrix - the matrix to transform the points by
    """

    points = []
    for _ in range(amount):
        edge = random.choice(mesh.edges)
        v1 = mesh.vertices[edge.vertices[0]]
        v2 = mesh.vertices[edge.vertices[1]]
        p = v1.co + random.random() * (v2.co - v1.co)
        points.append(transform_matrix * p)

    return points


# def get_random_points_on_surface(mesh, amount, transform_matrix):
#     """
#     get_random_points_on_surface(mesh mesh, int amount, matrix transform_matrix)
#             -> list of vector points

#         Gets <amount> number of random points on the surface of the mesh.

#         mesh mesh               - the mesh to get the points from
#         int amount              - the amount of points to return
#         matrix transform_matrix - the matrix to transform the points by
#     """

#     tessfaces = mesh.tessfaces
#     num_points = math.ceil(amount / len(tessfaces))
#     points = bpy_extras.mesh_utils.face_random_points(num_points, tessfaces)
#     # points = random.sample(points, amount)
#     random.shuffle(points)
#     points = [transform_matrix * p for p in points[:amount]]
#     # points = []
#     # for _ in range(amount):
#     #     face = random.choice(mesh.tessfaces)
#     #     p = bpy_extras.mesh_utils.face_random_points(1, [face])[0]
#     #     points.append(transform_matrix * p)

#     return points


def get_random_points_on_surface(obj, amount):
    """
    get_random_points_on_surface(mesh mesh, int amount)
            -> list of vector

        Gets <amount> number of random points on the surface of the object.

        object obj              - the object to get the points from
        int amount              - the amount of points to return
    """

    m = obj.modifiers.new('points', 'PARTICLE_SYSTEM')
    ps = m.particle_system
    ps.settings.count = amount
    ps.settings.frame_start = 1
    ps.settings.frame_end = 1
    ps.settings.physics_type = 'NO'
    bpy.context.scene.update()
    points = [p.location.copy() for p in ps.particles]
    obj.modifiers.remove(m)

    return points


def get_random_points_in_volume(obj, amount):
    # !!! NEEDS FIXING!!!
    """
    get_random_points_in_volume(object obj, int amount)
            -> list of vector points

        Gets <amount> number of random points inside the volume of the mesh.

        object obj              - the object to get the points from
        int amount              - the amount of points to return

    Adopted from code by CoDEmanX and pi (19.01.2014)
    """

    def point_in_box(O, W):
        return Vector((random.uniform(O.x, W.x),
                       random.uniform(O.y, W.y),
                       random.uniform(O.z, W.z)))

    points = []
    max_attempts = 999
    bbox = [Vector(b) for b in obj.bound_box]
    O = bbox[0]
    W = bbox[6]
    X = Vector((W.x - O.x, 0.0, 0.0))
    errors = 0

    for _ in range(amount):
        got_point = False
        for _ in range(max_attempts):
            p = point_in_box(O, W)
            _, normal, index = obj.ray_cast(p, p + X)
            if index > -1 and normal.x > 0.0:
                got_point = True
                break
        if not got_point:
            errors += 1
            continue
        points.append(obj.matrix_world * p)

    if errors:
        print("Max attempts reached, got {} points less "
              "then specified...".format(errors))

    return points


# def get_point_on_edge(edge, transform_matrix, method='RANDOM'):
#     """
#     get_point_on_edge(edge edge, string method) -> vector

#         Calculates a point on an edge according to method in world space.

#         edge edge                  - the edge to calculate a point on
#         matrix transform_matrix    - the matrix to transform the points by
#         string method              - the method to calculate the point
#                                      valid options: - 'RANDOM'
#                                                     - 'HALFWAY'
#                                                     - 'END_POINTS'
#     """

#     valid_methods = {'RANDOM', 'HALFWAY', 'END_POINTS'}

#     if not method in valid_methods:
#         return

#     if method == 'RANDOM' or 'HALFWAY':
#         v1 = edge.id_data.vertices[edge.vertices[0]]
#         v2 = edge.id_data.vertices[edge.vertices[1]]
#         if method == 'RANDOM':
#             fac = random.random()
#         else:
#             fac = 0.5
#         return transform_matrix * (v1.co + fac * (v2.co - v1.co))
#     elif method == 'END_POINTS':
#         v = edge.id_data.vertices[random.choice(edge.vertices)]
#         return transform_matrix * v.co


def get_points(obj, amount=1, method='SURFACE', apply_modifiers=True):
    """
    get_points(object obj,
               int amount,
               string method,
               bool apply_modifiers) -> tuple of vector points

        Calculates points on the object according to method in world space.
        !!! For now, apart from "pivot", they will be random.
            Later there might be an option to change this behavior. !!!

        object obj           - the object to calculate the points on
        int amount           - the amount of points to calculate
        string method        - the method to calculate the points
                               valid options: - 'VERTS'
                                              - 'EDGES'
                                              - 'SURFACE'
                                              - 'VOLUME'
                                              - 'PIVOT'
        bool apply_modifiers - use the deformed or original mesh
    """

    valid_methods = {'VERTS', 'EDGES', 'SURFACE', 'VOLUME', 'PIVOT'}

    if not method in valid_methods:
        return

    if apply_modifiers and not method == 'PIVOT':
        mesh = obj.to_mesh(bpy.context.scene, True, 'PREVIEW')
    elif method != 'PIVOT':
        mesh = obj.data.copy()
    transform_matrix = obj.matrix_world.copy()

    if method == 'VERTS':
        return get_random_points_on_verts(mesh, amount, transform_matrix)
        # points.append(transform_matrix * random.choice(mesh.vertices).co)
    if method == 'EDGES':
        return get_random_points_on_edges(mesh, amount, transform_matrix)
        # edge = random.choice(mesh.edges)
        # points.append(get_point_on_edge(edge, transform_matrix))
    if method == 'SURFACE':
        return get_random_points_on_surface(obj, amount)
        # face = random.choice(mesh.tessfaces)
        # point = bpy_extras.mesh_utils.face_random_points(1, [face])[0]
        # points.append(transform_matrix * point)
    if method == 'VOLUME':
        return get_random_points_in_volume(obj, amount)
    if method == 'PIVOT':
        # Only return the pivot point
        return [transform_matrix.to_translation()]


# obj = bpy.data.objects['Suzanne']
# points = get_points(obj, amount=33, method='SURFACE')
# for p in points:
#     bpy.ops.mesh.primitive_cube_add(location=p, radius=.05)
#     bpy.ops.object.material_slot_add()
#     bpy.context.object.material_slots[0].material = bpy.data.materials['red']
# for obj in bpy.data.objects:
#     if 'Cube' in obj.name:
#         obj.select = True
