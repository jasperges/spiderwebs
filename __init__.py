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


bl_info = {
    "name": "Create spider webs",
    "author": "Jasper van Nieuwenhuizen",
    "version": (0, 1),
    "blender": (2, 7, 5),
    "location": "View3D > Add > Curve ",
    "description": "Create spider webs or wires between objects",
    "warning": "wip",
    "wiki_url": "",
    "tracker_url": "",
    "support": 'COMMUNITY',
    "category": "Add Curve"}


if "bpy" in locals():
    import importlib
    if "add_curve_spiderwebs" in locals():
        importlib.reload(add_curve_spiderwebs)
else:
    from . import add_curve_spiderwebs

import bpy


# Register
def Spiderweb_menu_item(self, context):
    self.layout.operator(add_curve_spiderwebs.Spiderweb.bl_idname,
                         text="Create spiderweb",
                         icon="PLUGIN")


def register():
    bpy.utils.register_module(__name__)
    bpy.types.INFO_MT_curve_add.append(Spiderweb_menu_item)


def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.INFO_MT_curve_add.remove(Spiderweb_menu_item)


if __name__ == "__main__":
    register()
