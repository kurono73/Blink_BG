#Blink BG

import bpy

# --- Global Functions: Safe UI Redraw ---
def force_redraw():
    for wm in bpy.data.window_managers:
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

# --- Utility: Ultimate Camera Data Retrieval ---
def get_real_cam_data(context):
    try:
        space = getattr(context, "space_data", None)
        if space and getattr(space, "use_pin_id", False) and getattr(space, "pin_id", None):
            pin = space.pin_id
            if hasattr(pin, "background_images"): return pin
            if hasattr(pin, "data") and hasattr(pin.data, "background_images"): return pin.data

        for attr in ("camera", "id", "active_object", "object"):
            obj = getattr(context, attr, None)
            if obj:
                if hasattr(obj, "background_images"): return obj
                if hasattr(obj, "data") and hasattr(obj.data, "background_images"): return obj.data
                
        scene = getattr(context, "scene", None)
        if scene and getattr(scene, "camera", None):
            cam = scene.camera
            if hasattr(cam, "background_images"): return cam
            if hasattr(cam, "data") and hasattr(cam.data, "background_images"): return cam.data
    except Exception:
        pass
    return None

# --- Utility: Safe Background Image Retrieval ---
def get_active_bg(cam_data):
    if not cam_data:
        return None
    bg_images = getattr(cam_data, "background_images", None)
    if not bg_images or len(bg_images) == 0:
        return None
    idx = getattr(cam_data, "bg_blink_active_index", 0)
    idx = max(0, min(idx, len(bg_images) - 1))
    return bg_images[idx]

# --- Getters / Setters ---
def get_base_alpha(self):
    if getattr(self, "bg_blink_active", False):
        return self.get("bg_blink_base_alpha", 0.5)
    bg = get_active_bg(self)
    return bg.alpha if bg else 0.5

def set_base_alpha(self, value):
    self["bg_blink_base_alpha"] = value
    if not getattr(self, "bg_blink_active", False):
        bg = get_active_bg(self)
        if bg:
            bg.alpha = value

def update_target_alpha(self, context):
    if getattr(self, "bg_blink_active", False):
        bg = get_active_bg(self)
        if bg:
            bg.alpha = self.bg_blink_target_alpha

def update_active_state(self, context):
    bg = get_active_bg(self)
    if not bg:
        return
    if getattr(self, "bg_blink_active", False):
        self["bg_blink_base_alpha"] = bg.alpha
        bg.alpha = self.bg_blink_target_alpha
    else:
        bg.alpha = self.get("bg_blink_base_alpha", 0.5)


# --- Core Operators ---
class VIEW3D_OT_blink_bg(bpy.types.Operator):
    """Toggle BG image alpha. Supports hold action (shortcut) or auto-off delay (UI click)"""
    bl_idname = "view3d.blink_bg"
    bl_label = "Blink BG"
    bl_options = {'REGISTER'} 

    def toggle_state(self, context):
        cam_data = context.scene.camera.data
        cam_data.bg_blink_active = not cam_data.bg_blink_active
        force_redraw()

    def execute(self, context):
        cam = context.scene.camera
        if not cam or cam.type != 'CAMERA' or not cam.data.background_images:
            return {'CANCELLED'}
        
        self.toggle_state(context)
        return {'FINISHED'}

    def invoke(self, context, event):
        cam = context.scene.camera
        if not cam or cam.type != 'CAMERA' or not cam.data.background_images:
            return {'CANCELLED'}

        if context.scene.bg_blink_lock:
            return self.execute(context)
            
        if event.type == 'LEFTMOUSE':
            cam_data = cam.data
            
            if cam_data.bg_blink_active:
                cam_data.bg_blink_active = False
                force_redraw()
            else:
                cam_data.bg_blink_active = True
                force_redraw()
                
                def auto_off():
                    try:
                        if cam_data and cam_data.bg_blink_active:
                            cam_data.bg_blink_active = False
                            force_redraw()
                    except ReferenceError:
                        pass
                    return None 
                
                delay = context.scene.bg_blink_delay
                bpy.app.timers.register(auto_off, first_interval=delay)
                
            return {'FINISHED'}

        cam.data.bg_blink_active = True
        force_redraw()

        self.trigger_type = event.type
        self.trigger_value = event.value
        
        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if event.type == self.trigger_type and event.value != self.trigger_value:
            self.restore_state(context)
            return {'FINISHED'}
        
        if event.type in {'ESC', 'RIGHTMOUSE'}:
            self.restore_state(context)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}
        
    def restore_state(self, context):
        cam = context.scene.camera
        if cam and cam.type == 'CAMERA':
            cam.data.bg_blink_active = False
            force_redraw()


class VIEW3D_OT_blink_bg_swap_opacity(bpy.types.Operator):
    """Swap Opacity A and Opacity B values"""
    bl_idname = "view3d.blink_bg_swap_opacity"
    bl_label = "Swap Opacity"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        cam = context.scene.camera
        return cam and cam.type == 'CAMERA' and cam.data.background_images

    def execute(self, context):
        cam_data = context.scene.camera.data
        
        temp = cam_data.bg_blink_base_alpha
        cam_data.bg_blink_base_alpha = cam_data.bg_blink_target_alpha
        cam_data.bg_blink_target_alpha = temp

        force_redraw()
        return {'FINISHED'}


class VIEW3D_OT_blink_bg_depth_toggle(bpy.types.Operator):
    """Toggle Background Image Depth (Front/Back)"""
    bl_idname = "view3d.blink_bg_depth_toggle"
    bl_label = "Toggle Depth"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        cam = context.scene.camera
        return cam and cam.type == 'CAMERA' and cam.data.background_images

    def execute(self, context):
        bg = get_active_bg(context.scene.camera.data)
        if bg:
            bg.display_depth = 'BACK' if bg.display_depth == 'FRONT' else 'FRONT'
            force_redraw()
        return {'FINISHED'}


class VIEW3D_OT_blink_bg_set_resolution(bpy.types.Operator):
    """Set the scene render resolution to match the active background image/clip size"""
    bl_idname = "view3d.blink_bg_set_resolution"
    bl_label = "Match Render Size"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True 

    def execute(self, context):
        cam_data = get_real_cam_data(context)
        
        if not cam_data and context.scene.camera:
            cam_data = context.scene.camera.data
            
        if not cam_data:
            self.report({'WARNING'}, "Cannot find active camera.")
            return {'CANCELLED'}

        bg = get_active_bg(cam_data)
        if not bg:
            self.report({'WARNING'}, "Please add a background image first.")
            return {'CANCELLED'}

        scene = context.scene
        res_x, res_y = 0, 0

        if getattr(bg, "source", "") == 'IMAGE' and getattr(bg, "image", None):
            res_x, res_y = bg.image.size
        elif getattr(bg, "source", "") == 'MOVIE_CLIP' and getattr(bg, "clip", None):
            res_x, res_y = bg.clip.size
        else:
            self.report({'WARNING'}, "No valid image or movie clip loaded.")
            return {'CANCELLED'}

        if res_x > 0 and res_y > 0:
            scene.render.resolution_x = res_x
            scene.render.resolution_y = res_y
            self.report({'INFO'}, f"Resolution set to {res_x} x {res_y}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, "Failed to retrieve resolution.")
            return {'CANCELLED'}


# --- UI Panels ---
class VIEW3D_PT_blink_bg(bpy.types.Panel):
    """Blink BG Main Control Panel"""
    bl_label = "Blink BG"
    bl_idname = "VIEW3D_PT_blink_bg"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        cam = scene.camera

        layout.prop(scene, "camera", text="", icon='CAMERA_DATA')
        
        if cam and cam.data.background_images:
            cam_data = cam.data
            bg = get_active_bg(cam_data)
            
            if bg:
                layout.separator()
                
                if len(cam_data.background_images) > 1:
                    layout.prop(cam_data, "bg_blink_active_index")
                    layout.separator()
                
                if bg.source == 'MOVIE_CLIP':
                    layout.prop(bg.clip_user, "use_render_undistorted", text="Render Undistorted")
                
                split = layout.split(factor=0.85, align=True)
                
                col_left = split.column(align=True)
                col_left.prop(cam_data, "bg_blink_base_alpha")
                col_left.prop(cam_data, "bg_blink_target_alpha")
                
                col_right = split.column(align=True)
                col_right.label(text="", icon='BLANK1') 
                col_right.operator(VIEW3D_OT_blink_bg_swap_opacity.bl_idname, text="", icon='FILE_REFRESH')
                
                row_blink = layout.row(align=True) 
                is_blink = cam_data.bg_blink_active 
                row_blink.operator(VIEW3D_OT_blink_bg.bl_idname, text="Blink BG", depress=is_blink)
                
                lock_icon = 'LOCKED' if scene.bg_blink_lock else 'UNLOCKED'
                row_blink.prop(scene, "bg_blink_lock", text="", icon=lock_icon)

                row_depth = layout.row(align=True)
                depth_text = "Depth: Front" if bg.display_depth == 'FRONT' else "Depth: Back"
                depth_icon = 'TRIA_UP_BAR' if bg.display_depth == 'FRONT' else 'TRIA_DOWN_BAR'
                row_depth.operator(VIEW3D_OT_blink_bg_depth_toggle.bl_idname, text=depth_text, icon=depth_icon)
            
        else:
            layout.separator()
            layout.label(text="Please add a background image", icon='INFO')


class VIEW3D_PT_blink_bg_options(bpy.types.Panel):
    """Blink BG Options Sub-Panel"""
    bl_label = "Options"
    bl_idname = "VIEW3D_PT_blink_bg_options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'View'
    bl_parent_id = "VIEW3D_PT_blink_bg"
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        return context.scene.camera is not None

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        col = layout.column()
        col.enabled = not scene.bg_blink_lock
        col.prop(scene, "bg_blink_delay", text="Auto-OFF Delay (Sec)")

        layout.prop(scene, "bg_blink_auto_pin", text="Auto-Sync Pinned Camera")


def add_set_resolution_button_to_properties(self, context):
    """Append Match Render Size button to the standard Camera properties panel."""
    self.layout.separator()
    self.layout.operator(VIEW3D_OT_blink_bg_set_resolution.bl_idname, text="Match Render Size", icon='OUTPUT')


# --- Handlers ---
_last_active_camera_name = ""

@bpy.app.handlers.persistent
def sync_pinned_camera_handler(scene, depsgraph):
    """Automatically sync pinned Properties editors to the active camera."""
    if not getattr(scene, "bg_blink_auto_pin", False):
        return

    cam = scene.camera
    if not cam:
        return

    global _last_active_camera_name
    if cam.name == _last_active_camera_name:
        return

    _last_active_camera_name = cam.name

    for wm in bpy.data.window_managers:
        for window in wm.windows:
            for area in window.screen.areas:
                if area.type == 'PROPERTIES':
                    for space in area.spaces:
                        if space.type == 'PROPERTIES' and space.use_pin_id:
                            if not space.pin_id:
                                continue
                                
                            if isinstance(space.pin_id, bpy.types.Object) and space.pin_id.type == 'CAMERA':
                                space.pin_id = cam
                                area.tag_redraw()
                                
                            elif isinstance(space.pin_id, bpy.types.Camera):
                                space.pin_id = cam.data
                                area.tag_redraw()


# --- Registration ---
classes = (
    VIEW3D_OT_blink_bg,
    VIEW3D_OT_blink_bg_swap_opacity,
    VIEW3D_OT_blink_bg_depth_toggle,
    VIEW3D_OT_blink_bg_set_resolution,
    VIEW3D_PT_blink_bg,
    VIEW3D_PT_blink_bg_options,
)

addon_keymaps = []

def register():
    bpy.types.Camera.bg_blink_active_index = bpy.props.IntProperty(
        name="Target BG",
        description="Select which background image to control",
        default=0,
        min=0,
        update=update_active_state
    )
    
    bpy.types.Camera.bg_blink_base_alpha = bpy.props.FloatProperty(
        name="Opacity A (Base)",
        description="Base opacity for background image",
        get=get_base_alpha,
        set=set_base_alpha,
        min=0.0,
        max=1.0,
        subtype='FACTOR'
    )
    
    bpy.types.Camera.bg_blink_target_alpha = bpy.props.FloatProperty(
        name="Opacity B (Target)",
        description="Target opacity when Blink BG is active",
        default=0.0,
        min=0.0,
        max=1.0,
        subtype='FACTOR',
        update=update_target_alpha
    )
    
    bpy.types.Camera.bg_blink_active = bpy.props.BoolProperty(
        default=False,
        update=update_active_state
    )
    
    bpy.types.Scene.bg_blink_lock = bpy.props.BoolProperty(
        name="Lock Blink State",
        description="When locked, the shortcut key (Alt+V) acts as a toggle instead of hold",
        default=False
    )
    
    bpy.types.Scene.bg_blink_delay = bpy.props.FloatProperty(
        name="Auto-OFF Delay",
        description="Delay in seconds before automatically turning off when clicked via UI",
        default=0.2, 
        min=0.1,
        max=5.0
    )
    
    bpy.types.Scene.bg_blink_auto_pin = bpy.props.BoolProperty(
        name="Auto-Sync Pinned Camera",
        description="Automatically update pinned Properties editors to the active camera",
        default=True
    )

    for cls in classes:
        bpy.utils.register_class(cls)
    
    if sync_pinned_camera_handler not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(sync_pinned_camera_handler)
        
    bpy.types.DATA_PT_camera_background_image.append(add_set_resolution_button_to_properties)
    
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D', region_type='WINDOW')
        kmi1 = km.keymap_items.new(VIEW3D_OT_blink_bg.bl_idname, 'V', 'PRESS', alt=True)
        addon_keymaps.append((km, kmi1))


def unregister():
    if sync_pinned_camera_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(sync_pinned_camera_handler)
        
    bpy.types.DATA_PT_camera_background_image.remove(add_set_resolution_button_to_properties)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        for km, kmi in addon_keymaps:
            km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    del bpy.types.Camera.bg_blink_active_index
    del bpy.types.Camera.bg_blink_base_alpha
    del bpy.types.Camera.bg_blink_target_alpha
    del bpy.types.Camera.bg_blink_active
    del bpy.types.Scene.bg_blink_lock
    del bpy.types.Scene.bg_blink_delay 
    del bpy.types.Scene.bg_blink_auto_pin