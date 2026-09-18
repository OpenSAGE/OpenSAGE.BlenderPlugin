# <pep8 compliant>
# Written by Stephan Vedder and Michael Schnabel


def save(context, export_settings, data_context):
    filepath = context.filepath
    if not filepath.lower().endswith(context.filename_ext):
        filepath += context.filename_ext

    context.info(f'Saving file: {filepath}')

    export_mode = export_settings['mode']
    context.info(f'export mode: {export_mode}')

    file = open(filepath, 'wb')

    if export_mode == 'M':
        if len(data_context.meshes) > 1:
            context.warning('Scene does contain multiple meshes, exporting only the first with export mode M!')
        mesh = data_context.meshes[0]
        mesh.header.container_name = ''
        mesh.header.mesh_name = data_context.container_name
        mesh.write(file)

    elif export_mode == 'HM' or export_mode == 'HAM':
        # 'use existing skeleton' means the hierarchy this file's geometry/animation
        # binds to already exists elsewhere under its own name (e.g. the base model
        # this is a build-up/destroy animation variant of) - renaming it to this
        # file's own name would produce a hierarchy the game does not recognise as
        # the same object, so the animation silently never shows up in-game
        rename_hierarchy = not export_settings.get('use_existing_skeleton', False)
        write_hierarchy = export_mode == 'HAM' or rename_hierarchy

        if rename_hierarchy:
            data_context.hlod.header.hierarchy_name = data_context.container_name
            data_context.hierarchy.header.name = data_context.container_name
        if write_hierarchy:
            data_context.hierarchy.write(file)

        for box in data_context.collision_boxes:
            box.write(file)

        for dazzle in data_context.dazzles:
            dazzle.write(file)

        for mesh in data_context.meshes:
            mesh.write(file)

        data_context.hlod.write(file)
        if export_mode == 'HAM':
            if rename_hierarchy:
                data_context.animation.header.hierarchy_name = data_context.container_name
            data_context.animation.write(file)

    elif export_mode == 'A':
        data_context.animation.write(file)

    elif export_mode == 'H':
        data_context.hierarchy.header.name = data_context.container_name.upper()
        data_context.hierarchy.write(file)
    else:
        context.error(f'unsupported export mode \'{export_mode}\', aborting export!')
        return {'CANCELLED'}

    file.close()
    context.info('finished')
    return {'FINISHED'}
